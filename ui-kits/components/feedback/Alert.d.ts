import React from 'react';

export interface AlertProps {
  /** Semantic variant */
  variant?: 'info' | 'success' | 'warning' | 'error';
  /** Bold title line */
  title?: string;
  /** Body description text */
  description?: string;
  /** Called when the alert is dismissed (X clicked) */
  onDismiss?: () => void;
  /** Show dismiss X button */
  isDismissible?: boolean;
  /** Primary inline action label */
  actionLabel?: string;
  /** Called when actionLabel is clicked */
  onAction?: () => void;
  /** Extra inline styles */
  style?: React.CSSProperties;
}

export declare function Alert(props: AlertProps): JSX.Element;
