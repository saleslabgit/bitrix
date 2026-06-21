import React from 'react';

export interface AvatarProps {
  /** Image URL — falls back to initials if broken or not provided */
  src?: string;
  /** Override initials (up to 2 chars, auto-uppercased) */
  initials?: string;
  /** Alt text; used as fallback for initials if `initials` not set */
  alt?: string;
  /** Size tier */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  /** Shape */
  shape?: 'circle' | 'square' | 'rounded';
  /** Extra inline styles */
  style?: React.CSSProperties;
}

export declare function Avatar(props: AvatarProps): JSX.Element;
