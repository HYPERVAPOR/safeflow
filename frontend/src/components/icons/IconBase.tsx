import React from 'react';

interface IconBaseProps {
  size?: number | string;
  className?: string;
  color?: string;
  children?: React.ReactNode;
}

export const IconBase: React.FC<IconBaseProps> = ({
  size = 20,
  className = '',
  color = 'currentColor',
  children
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {children}
    </svg>
  );
};