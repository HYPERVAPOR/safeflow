import React from 'react';
import { IconBase } from './IconBase';

export const ConsoleIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <polyline points="4 17 10 11 4 5" />
    <path d="M12 19h8" />
  </IconBase>
);