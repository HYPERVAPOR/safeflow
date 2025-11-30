import React from 'react';
import { IconBase } from './IconBase';

export const StatusWarningIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <path d="m21.73 18-8-14a2 2 0 00-3.48 0l-8 14A2 2 0 004 21h16a2 2 0 001.73-3z" />
    <path d="M12 9v4m0 4h.01" stroke="white" fill="none" />
  </IconBase>
);