import React from 'react';
import { IconBase } from './IconBase';

export const DependencyAnalysisIcon: React.FC<Omit<React.ComponentProps<typeof IconBase>, 'children'>> = (props) => (
  <IconBase {...props}>
    {/* 垂直线 */}
    <line x1="12" y1="6" x2="12" y2="18" strokeWidth="2" strokeLinecap="round" />
    
    {/* 节点 */}
    <circle cx="12" cy="7" r="1.5" fill="currentColor" />
    <circle cx="12" cy="12" r="1.5" fill="currentColor" />
    <circle cx="12" cy="17" r="1.5" fill="currentColor" />
  </IconBase>
);
