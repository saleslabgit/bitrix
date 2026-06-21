import React from 'react';

export interface SidebarNavItem {
  label: string;
  icon?: 'dashboard' | 'calendar' | 'notifications' | 'analytics' | 'settings' | 'support' | 'logout' | 'income' | string;
  href?: string;
  isActive?: boolean;
  children?: SidebarNavItem[];
  onClick?: () => void;
}

export interface SidebarSection {
  label: string;
  items: SidebarNavItem[];
}

export interface SidebarProps {
  /** Flat list of nav items (alternative to sections) */
  items?: SidebarNavItem[];
  /** Grouped sections — each section has a label + items */
  sections?: SidebarSection[];
  /** Collapsed state — shows only icons */
  isCollapsed?: boolean;
  /** Light or dark sidebar variant */
  variant?: 'light' | 'dark';
  /** Wordmark text in the sidebar header */
  logoText?: string;
  /** Logout click handler */
  onLogout?: () => void;
  /** Extra inline styles on the sidebar container */
  style?: React.CSSProperties;
}

export declare function Sidebar(props: SidebarProps): JSX.Element;
