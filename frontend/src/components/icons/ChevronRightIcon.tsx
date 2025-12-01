import React from 'react';
import { IconBase } from './IconBase';

export const ChevronRightIcon: React.FC<
  Omit<React.ComponentProps<typeof IconBase>, 'children'>
> = (props) => (
  <IconBase {...props}>
    <polyline points="9 18 15 12 9 6" />
  </IconBase>
);
