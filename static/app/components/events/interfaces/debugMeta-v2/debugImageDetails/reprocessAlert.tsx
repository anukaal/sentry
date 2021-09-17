import {useEffect, useState} from 'react';
import styled from '@emotion/styled';

import {Client} from 'app/api';
import Alert from 'app/components/alert';
import AlertLink from 'app/components/alertLink';
import {t} from 'app/locale';
import {Organization, Project} from 'app/types';
import {Event} from 'app/types/event';

enum ReprocessableEventReason {
  // It can have many reasons. The event is too old to be reprocessed (very unlikely!)
  // or was not a native event.
  UNPROCESSED_EVENT_NOT_FOUND = 'unprocessed_event.not_found',
  // The event does not exist.
  EVENT_NOT_FOUND = 'event.not_found',
  // A required attachment, such as the original minidump, is missing.
  ATTACHMENT_NOT_FOUND = 'attachment.not_found',
}

type ReprocessableEvent = {
  reprocessable: boolean;
  reason?: ReprocessableEventReason;
};

type Props = {
  onReprocessEvent: () => void;
  api: Client;
  orgSlug: Organization['slug'];
  projSlug: Project['slug'];
  eventId: Event['id'];
};

function ReprocessAlert({onReprocessEvent, api, orgSlug, projSlug, eventId}: Props) {
  const [reprocessableEvent, setReprocessableEvent] = useState<
    undefined | ReprocessableEvent
  >();

  useEffect(() => {
    checkEventReprocessable();
  }, []);

  async function checkEventReprocessable() {
    try {
      const response = await api.requestPromise(
        `/projects/${orgSlug}/${projSlug}/events/${eventId}/reprocessable/`
      );
      setReprocessableEvent(response);
    } catch {
      // do nothing
    }
  }

  if (!reprocessableEvent) {
    return null;
  }

  const {reprocessable, reason} = reprocessableEvent;

  if (reprocessable) {
    return (
      <AlertLink
        priority="warning"
        size="small"
        onClick={onReprocessEvent}
        withoutMarginBottom
      >
        {t(
          'You’ve uploaded new debug files. Reprocess events in this issue to view a better stack trace'
        )}
      </AlertLink>
    );
  }

  function getAlertInfoMessage() {
    switch (reason) {
      case ReprocessableEventReason.EVENT_NOT_FOUND:
        return t('This event cannot be reprocessed because the event has not been found');
      case ReprocessableEventReason.ATTACHMENT_NOT_FOUND:
        return t(
          'This event cannot be reprocessed because a required attachment is missing'
        );
      case ReprocessableEventReason.UNPROCESSED_EVENT_NOT_FOUND:
      default:
        return t('This event cannot be reprocessed');
    }
  }

  return <StyledAlert type="info">{getAlertInfoMessage()}</StyledAlert>;
}

export default ReprocessAlert;

const StyledAlert = styled(Alert)`
  margin-bottom: 0;
`;
