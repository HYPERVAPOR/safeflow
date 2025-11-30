import React from 'react';
import { IconBase } from './IconBase';

export const FuzzingIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <path d="M14 2v6m0 4v6m0 4v2m-6-8h6m-4 0h.01M8 10h.01M12 14h.01M16 10h.01" />
    <circle cx="9" cy="9" r="2" />
    <circle cx="15" cy="15" r="2" />
  </IconBase>
);