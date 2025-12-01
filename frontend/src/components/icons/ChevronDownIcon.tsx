import React from 'react';
import { IconBase } from './IconBase';

export const ChevronDownIcon: React.FC<
  Omit<React.ComponentProps<typeof IconBase>, 'children'>
> = (props) => (
  <IconBase {...props}>
    <polyline points="6 9 12 15 18 9" />
  </IconBase>
);
