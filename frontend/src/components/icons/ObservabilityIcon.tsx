import React from 'react';
import { IconBase } from './IconBase';

export const ObservabilityIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <path d="M3 3v18h18" />
    <path d="M18 9l-5 5-3-3-5 5" />
    <circle cx="18" cy="9" r="2" />
  </IconBase>
);