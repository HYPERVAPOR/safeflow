import React from 'react';
import { IconBase } from './IconBase';

export const StatusSuccessIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <circle cx="12" cy="12" r="10" />
    <path d="m9 12 2 2 4-4" stroke="#E5E7EB" fill="none" />
  </IconBase>
);