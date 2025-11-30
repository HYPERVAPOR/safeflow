import React from 'react';
import { IconBase } from './IconBase';

export const DependencyAnalysisIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <circle cx="12" cy="12" r="3" />
    <circle cx="4" cy="8" r="2" />
    <circle cx="20" cy="8" r="2" />
    <circle cx="8" cy="20" r="2" />
    <circle cx="16" cy="20" r="2" />
    <path d="M12 9V6.5a2.5 2.5 0 00-4-2.5m4 5l-4-2m4 2l4-2m-4 2v3m-4 1.5a2.5 2.5 0 002 4 2.5 2.5 0 002-4m0 0l4-2m-4 2l-4-2" />
  </IconBase>
);