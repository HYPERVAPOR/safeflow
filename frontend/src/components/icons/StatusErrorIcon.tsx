import React from 'react';
import { IconBase } from './IconBase';

export const StatusErrorIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <circle cx="12" cy="12" r="10" />
    <path d="m15 9-6 6m0-6 6 6" stroke="white" fill="none" />
  </IconBase>
);