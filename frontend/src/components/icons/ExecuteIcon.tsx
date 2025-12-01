import React from 'react';
import { IconBase } from './IconBase';

export const ExecuteIcon: React.FC<
  Omit<React.ComponentProps<typeof IconBase>, 'children'>
> = (props) => (
  <IconBase {...props}>
    <polygon points="5 3 19 12 5 21 5 3" />
  </IconBase>
);
