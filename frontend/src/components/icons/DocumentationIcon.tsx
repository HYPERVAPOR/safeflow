import React from 'react';
import { IconBase } from './IconBase';

export const DocumentationIcon: React.FC<
  Omit<React.ComponentProps<typeof IconBase>, 'children'>
> = (props) => (
  <IconBase {...props}>
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <path d="M16 13H8m8 4H8m2-8H8" />
  </IconBase>
);
