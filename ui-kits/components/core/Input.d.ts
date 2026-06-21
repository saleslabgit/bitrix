import React from 'react';

export interface InputProps {
  /** Field label rendered above the input */
  label?: string;
  /** Helper text shown below the input */
  hintText?: string;
  /** Input placeholder text */
  placeholder?: string;
  /** Input type — use 'password' for password inputs with show/hide toggle */
  type?: 'text' | 'email' | 'password' | 'number' | 'search' | 'url' | 'tel';
  /** Error message — replaces hintText and triggers error styling */
  error?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Icon node rendered on the left inside the input */
  iconLeft?: React.ReactNode;
  /** Controlled value */
  value?: string;
  /** Change handler */
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  /** HTML id attribute */
  id?: string;
  /** HTML name attribute */
  name?: string;
  /** Extra inline styles on the wrapper */
  style?: React.CSSProperties;
}

export declare function Input(props: InputProps): JSX.Element;
