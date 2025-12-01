import React from 'react';
import { IconBase } from './IconBase';

export const StaticAnalysisIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    <path d="M 7 6 L 2 12 L 7 18"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"/>

    <path d="M 10 13.75 L 13.75 6.25"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"/>

    <path d="M 17 6 L 22 12 L 17 18"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"/>
  </IconBase>
);