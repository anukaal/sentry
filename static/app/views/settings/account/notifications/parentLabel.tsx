import styled from '@emotion/styled';

import Avatar from 'app/components/avatar';
import space from 'app/styles/space';
import {OrganizationSummary, Project} from 'app/types';
import {getParentKey} from 'app/views/settings/account/notifications/utils';

type Props = {
  notificationType: string;
  parent: OrganizationSummary | Project;
};

// TODO(mgaeta): Infer parentKey from parent.
const ParentLabel = ({notificationType, parent}: Props) => (
  <FieldLabel>
    <Avatar
      {...{
        [getParentKey(notificationType)]: parent,
      }}
    />
    <span>{parent.slug}</span>
  </FieldLabel>
);

const FieldLabel = styled('div')`
  display: flex;
  gap: ${space(0.5)};
  line-height: 16px;
`;

export default ParentLabel;
