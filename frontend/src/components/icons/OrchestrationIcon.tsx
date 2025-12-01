import React from 'react';
import { IconBase } from './IconBase';

export const OrchestrationIcon: React.FC<
  Omit<React.ComponentProps<typeof IconBase>, 'children'>
> = (props) => (
  <IconBase {...props}>
    <circle cx="12" cy="5" r="2" />
    <circle cx="5" cy="19" r="2" />
    <circle cx="19" cy="19" r="2" />
    <path d="M12 5v3m0 3v2m-7 2l3.5-3.5M19 19l-3.5-3.5" />
    <circle cx="12" cy="12" r="3" />
  </IconBase>
);
