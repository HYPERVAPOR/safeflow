import React from 'react';
import { IconBase } from './IconBase';

export const CloseIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <path d="M18 6L6 18M6 6l12 12" />
  </IconBase>
);