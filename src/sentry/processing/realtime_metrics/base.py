from typing import Set, Union

from sentry.utils.services import Service


class RealtimeMetricsStore(Service):  # type: ignore
    """A service for storing metrics about incoming requests within a given time window."""

    __all__ = (
        "increment_project_event_counter",
        "validate",
        "get_lpq_projects",
        "add_project_to_lpq",
        "remove_projects_from_lpq",
    )

    def increment_project_event_counter(
        self, project_id: int, timestamp: Union[int, float]
    ) -> None:
        """Increment the event counter for the given project_id.

        The counter is used to track the rate of events for the project.
        Calling this increments the counter of the current
        time-window bucket with "timestamp" providing the time of the event.
        """
        pass

    def get_lpq_projects(self) -> Set[int]:
        """
        Fetches the list of projects that are currently using the low priority queue.

        Returns a list of project IDs.
        """
        pass

    def add_project_to_lpq(self, project_id: int) -> None:
        """
        Moves projects to the low priority queue.

        This forces all symbolication events triggered by the specified projects to be redirected to
        the low priority queue, unless these projects have been manually excluded from the low
        priority queue via the `store.symbolicate-event-lpq-never` kill switch.

        Raises ``LowPriorityQueueMembershipError`` if this fails to add the specified project to the
        low priority queue.
        """
        pass

    def remove_projects_from_lpq(self, project_ids: Set[int]) -> Set[int]:
        """
        Removes projects from the low priority queue.

        This restores all specified projects back to the regular queue, unless they have been
        manually forced into the low priority queue via the store.symbolicate-event-lpq-always kill
        switch.


        Returns all projects that have been successfully removed from the low priority queue.
        """
        pass
