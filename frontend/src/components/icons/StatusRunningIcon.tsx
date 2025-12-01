import React from 'react';
import { IconBase } from './IconBase';

export const StatusRunningIcon: React.FC<
  Omit<React.ComponentProps<typeof IconBase>, 'children'>
> = (props) => (
  <IconBase {...props}>
    <circle cx="12" cy="12" r="10" />
    <path d="M12 6v6l4 2" stroke="#E5E7EB" fill="none" />
  </IconBase>
);
