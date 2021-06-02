import logging
import re

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework.response import Response

from sentry.api.bases.project import ProjectEndpoint, ProjectReleasePermission
from sentry.api.endpoints.organization_release_files import load_dist
from sentry.api.exceptions import ResourceDoesNotExist
from sentry.api.paginator import (
    CombinedQuerysetIntermediary,
    CombinedQuerysetPaginator,
    OffsetPaginator,
)
from sentry.api.serializers import serialize
from sentry.constants import MAX_RELEASE_FILES_OFFSET
from sentry.models import File, Release, ReleaseFile
from sentry.models.releasefile import ReleaseArchive
from sentry.tasks.assemble import RELEASE_ARCHIVE_FILENAME, get_artifact_basename

ERR_FILE_EXISTS = "A file matching this name already exists for the given release"
_filename_re = re.compile(r"[\n\t\r\f\v\\]")


class ProjectReleaseFilesEndpoint(ProjectEndpoint):
    permission_classes = (ProjectReleasePermission,)

    def get(self, request, project, version):
        """
        List a Project Release's Files
        ``````````````````````````````

        Retrieve a list of files for a given release.

        :pparam string organization_slug: the slug of the organization the
                                          release belongs to.
        :pparam string project_slug: the slug of the project to list the
                                     release files of.
        :pparam string version: the version identifier of the release.
        :qparam string query: If set, this parameter is used to search files.
        :auth: required
        """
        query = request.GET.getlist("query")

        try:
            release = Release.objects.get(
                organization_id=project.organization_id, projects=project, version=version
            )
        except Release.DoesNotExist:
            raise ResourceDoesNotExist

        file_list = (
            ReleaseFile.objects.filter(release=release)
            .exclude(name=RELEASE_ARCHIVE_FILENAME)
            .select_related("file")
            .order_by("name")
        )

        if query:
            if not isinstance(query, list):
                query = [query]

            condition = Q(name__icontains=query[0])
            for name in query[1:]:
                condition |= Q(name__icontains=name)
            file_list = file_list.filter(condition)

        def on_results(r):
            results = serialize(load_dist(r), request.user)
            for result in results:
                if result["id"] == "None":
                    result.pop("id")

            return results

        # Get contents of release archive as well:
        archive = release.get_release_archive()
        if archive is None:
            # Behave like ProjectReleaseFilesEndpoint
            return self.paginate(
                request=request,
                queryset=file_list,
                order_by="name",
                paginator_cls=OffsetPaginator,
                max_offset=MAX_RELEASE_FILES_OFFSET,
                on_results=on_results,
            )
        else:
            with archive:
                archived_list = ReleaseArchiveQuerySet(archive, query)

            return self.paginate(
                request=request,
                intermediaries=[
                    CombinedQuerysetIntermediary(file_list, order_by=["name"]),
                    CombinedQuerysetIntermediary(archived_list, order_by=["name"]),
                ],
                paginator_cls=CombinedQuerysetPaginator,
                on_results=on_results,
            )

    def post(self, request, project, version):
        """
        Upload a New Project Release File
        `````````````````````````````````

        Upload a new file for the given release.

        Unlike other API requests, files must be uploaded using the
        traditional multipart/form-data content-type.

        The optional 'name' attribute should reflect the absolute path
        that this file will be referenced as. For example, in the case of
        JavaScript you might specify the full web URI.

        :pparam string organization_slug: the slug of the organization the
                                          release belongs to.
        :pparam string project_slug: the slug of the project to change the
                                     release of.
        :pparam string version: the version identifier of the release.
        :param string name: the name (full path) of the file.
        :param string dist: the name of the dist.
        :param file file: the multipart encoded file.
        :param string header: this parameter can be supplied multiple times
                              to attach headers to the file.  Each header
                              is a string in the format ``key:value``.  For
                              instance it can be used to define a content
                              type.
        :auth: required
        """
        try:
            release = Release.objects.get(
                organization_id=project.organization_id, projects=project, version=version
            )
        except Release.DoesNotExist:
            raise ResourceDoesNotExist

        logger = logging.getLogger("sentry.files")
        logger.info("projectreleasefile.start")

        if "file" not in request.data:
            return Response({"detail": "Missing uploaded file"}, status=400)

        fileobj = request.data["file"]

        full_name = request.data.get("name", fileobj.name)
        if not full_name or full_name == "file":
            return Response({"detail": "File name must be specified"}, status=400)

        name = full_name.rsplit("/", 1)[-1]

        if _filename_re.search(name):
            return Response(
                {"detail": "File name must not contain special whitespace characters"}, status=400
            )

        dist_name = request.data.get("dist")
        dist = None
        if dist_name:
            dist = release.add_dist(dist_name)

        # Quickly check for the presence of this file before continuing with
        # the costly file upload process.
        if ReleaseFile.objects.filter(
            organization_id=release.organization_id,
            release=release,
            name=full_name,
            dist=dist,
        ).exists():
            return Response({"detail": ERR_FILE_EXISTS}, status=409)

        headers = {"Content-Type": fileobj.content_type}
        for headerval in request.data.getlist("header") or ():
            try:
                k, v = headerval.split(":", 1)
            except ValueError:
                return Response({"detail": "header value was not formatted correctly"}, status=400)
            else:
                if _filename_re.search(v):
                    return Response(
                        {"detail": "header value must not contain special whitespace characters"},
                        status=400,
                    )
                headers[k] = v.strip()

        file = File.objects.create(name=name, type="release.file", headers=headers)
        file.putfile(fileobj, logger=logger)

        try:
            with transaction.atomic():
                releasefile = ReleaseFile.objects.create(
                    organization_id=release.organization_id,
                    release=release,
                    file=file,
                    name=full_name,
                    dist=dist,
                )
        except IntegrityError:
            file.delete()
            return Response({"detail": ERR_FILE_EXISTS}, status=409)

        return Response(serialize(releasefile, request.user), status=201)


class ListQuerySet:
    """ Pseudo queryset offering a subset of QuerySet operations """

    def __init__(self, release_files, query=None):
        self._files = [
            # Mimic "or" operation applied for real querysets:
            rf
            for rf in release_files
            if not query or any(search_string.lower() in rf.name.lower() for search_string in query)
        ]

    def get(self):
        files = self._files
        if not files:
            raise ObjectDoesNotExist
        if len(files) > 1:
            raise MultipleObjectsReturned

        return files[0]

    def annotate(self, **kwargs):
        if kwargs:
            raise NotImplementedError

        return self

    def filter(self, **kwargs):
        if kwargs:
            raise NotImplementedError

        return self

    def order_by(self, key):
        return ListQuerySet(sorted(self._files, key=lambda f: getattr(f, key)))

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._files[index]
        return ListQuerySet(self._files[index])


class ReleaseArchiveQuerySet(ListQuerySet):
    """ Pseudo queryset offering a subset of QuerySet operations, """

    def __init__(self, archive: ReleaseArchive, query=None):
        # Assume manifest
        release_files = [
            ReleaseFile(
                name=get_artifact_basename(info["url"]),
                file=File(
                    headers=info.get("headers", {}),
                    size=archive.get_file_size(filename),
                ),
            )
            for filename, info in archive.manifest.get("files", {}).items()
        ]
        super().__init__(release_files, query)
