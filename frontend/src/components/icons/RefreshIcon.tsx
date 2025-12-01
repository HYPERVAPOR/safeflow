import React from 'react';
import { IconBase } from './IconBase';

export const RefreshIcon: React.FC<
  Omit<React.ComponentProps<typeof IconBase>, 'children'>
> = (props) => (
  <IconBase {...props}>
    <path d="M21 2v6h-6M3 12a9 9 0 0115-6.7L21 8M3 22v-6h6M21 12a9 9 0 01-15 6.7L3 16" />
  </IconBase>
);
