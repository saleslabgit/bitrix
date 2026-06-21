import React from 'react';

export interface CardProps {
  /** Card content */
  children: React.ReactNode;
  /** Inner padding preset */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Show 1px border */
  hasBorder?: boolean;
  /** Shadow depth */
  shadow?: 'none' | 'xs' | 'sm' | 'md' | 'lg';
  /** Border radius preset */
  radius?: 'sm' | 'md' | 'lg' | 'xl';
  /** Background color override */
  background?: string;
  /** Click handler — makes card interactive (hover lift effect) */
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  /** Extra inline styles */
  style?: React.CSSProperties;
}

export declare function Card(props: CardProps): JSX.Element;
