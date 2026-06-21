import React from 'react';

export interface NavItem {
  label: string;
  href?: string;
  hasDropdown?: boolean;
}

export interface NavbarProps {
  /** Navigation link items */
  items?: NavItem[];
  /** CTA button label */
  ctaLabel?: string;
  /** CTA click handler */
  onCta?: () => void;
  /** URL to logo image — falls back to logoAlt text */
  logoSrc?: string;
  /** Logo alt text / fallback text wordmark */
  logoAlt?: string;
  /** Extra inline styles on the nav element */
  style?: React.CSSProperties;
}

export declare function Navbar(props: NavbarProps): JSX.Element;
