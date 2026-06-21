import React from 'react';

export interface BadgeProps {
  /** Badge label text */
  label: string;
  /** Semantic variant controlling colors */
  variant?: 'primary' | 'info' | 'success' | 'warning' | 'error' | 'neutral';
  /** Size */
  size?: 'sm' | 'md';
  /** Show colored dot indicator before the label */
  showDot?: boolean;
  /** Extra inline styles */
  style?: React.CSSProperties;
}

export declare function Badge(props: BadgeProps): JSX.Element;
