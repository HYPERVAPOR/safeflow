import React from 'react';
import { IconBase } from './IconBase';

export const WebSecurityIcon: React.FC<
  Omit<React.ComponentProps<typeof IconBase>, 'children'>
> = (props) => (
  <IconBase {...props}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="M12 8v4m0 4h.01" />
  </IconBase>
);
