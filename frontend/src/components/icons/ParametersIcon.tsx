import React from 'react';
import { IconBase } from './IconBase';

export const ParametersIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <circle cx="12" cy="12" r="3" />
    <circle cx="12" cy="5" r="2" />
    <circle cx="12" cy="19" r="2" />
    <path d="M12 5v3m0 4v3m0 4v3" />
  </IconBase>
);