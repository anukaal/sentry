import styled from '@emotion/styled';

import Alert from 'app/components/alert';
import {IconInfo} from 'app/icons';
import {tct} from 'app/locale';

type Props = {
  className?: string;
};

const FeedbackAlert = ({className}: Props) => (
  <StyledAlert type="info" icon={<IconInfo />} className={className}>
    {tct('Got feedback? Email [email:ecosystem-feedback@sentry.io].', {
      email: <a href="mailto:ecosystem-feedback@sentry.io" />,
    })}
  </StyledAlert>
);

const StyledAlert = styled(Alert)`
  margin: 20px 0px;
`;

export default FeedbackAlert;
