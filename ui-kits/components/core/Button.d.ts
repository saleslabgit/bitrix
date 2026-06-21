import React from 'react';

/**
 * @startingPoint section="Components" subtitle="Primary action button — all variants and sizes" viewport="700x320"
 */
export interface ButtonProps {
  /** Button label */
  children: React.ReactNode;
  /** Visual style */
  variant?: 'primary' | 'primary-light' | 'secondary' | 'ghost' | 'danger';
  /** Size tier */
  size?: 'XS' | 'S' | 'M' | 'L' | 'XL' | 'XXL';
  /** Disabled state */
  disabled?: boolean;
  /** Icon node rendered before label */
  iconLeft?: React.ReactNode;
  /** Icon node rendered after label */
  iconRight?: React.ReactNode;
  /** Click handler */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** HTML button type */
  type?: 'button' | 'submit' | 'reset';
  /** Stretch to fill container width */
  fullWidth?: boolean;
  /** Extra inline styles */
  style?: React.CSSProperties;
}

export declare function Button(props: ButtonProps): JSX.Element;
