import React from 'react';

const SIZE_STYLES = {
  XS:  { height: '24px', padding: '0 10px', fontSize: '11px', gap: '4px', iconSize: '12px' },
  S:   { height: '28px', padding: '0 12px', fontSize: '12px', gap: '4px', iconSize: '14px' },
  M:   { height: '32px', padding: '0 14px', fontSize: '13px', gap: '6px', iconSize: '14px' },
  L:   { height: '40px', padding: '0 18px', fontSize: '14px', gap: '6px', iconSize: '16px' },
  XL:  { height: '44px', padding: '0 20px', fontSize: '14px', gap: '8px', iconSize: '16px' },
  XXL: { height: '48px', padding: '0 24px', fontSize: '16px', gap: '8px', iconSize: '18px' },
};

const VARIANT_STYLES = {
  primary: {
    background: 'var(--color-primary-500)',
    color: 'var(--color-white)',
    border: 'none',
    hoverBg: 'var(--color-primary-600)',
    activeBg: 'var(--color-primary-700)',
  },
  'primary-light': {
    background: 'var(--color-primary-50)',
    color: 'var(--color-primary-500)',
    border: 'none',
    hoverBg: 'var(--color-primary-100)',
    activeBg: 'var(--color-primary-200)',
  },
  secondary: {
    background: 'transparent',
    color: 'var(--color-primary-500)',
    border: '1px solid var(--color-primary-400)',
    hoverBg: 'var(--color-primary-50)',
    activeBg: 'var(--color-primary-100)',
  },
  ghost: {
    background: 'transparent',
    color: 'var(--color-neutral-700)',
    border: '1px solid var(--color-neutral-200)',
    hoverBg: 'var(--color-neutral-50)',
    activeBg: 'var(--color-neutral-100)',
  },
  danger: {
    background: 'var(--color-red-500)',
    color: 'var(--color-white)',
    border: 'none',
    hoverBg: 'var(--color-red-600)',
    activeBg: 'var(--color-red-700)',
  },
};

export function Button({
  children,
  variant = 'primary',
  size = 'M',
  disabled = false,
  iconLeft = null,
  iconRight = null,
  onClick,
  type = 'button',
  fullWidth = false,
  style: extraStyle = {},
  ...props
}) {
  const [hovered, setHovered] = React.useState(false);
  const [pressed, setPressed] = React.useState(false);

  const sz = SIZE_STYLES[size] || SIZE_STYLES.M;
  const vr = VARIANT_STYLES[variant] || VARIANT_STYLES.primary;

  const bgColor = pressed ? vr.activeBg : hovered ? vr.hoverBg : vr.background;

  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: 'var(--font-primary)',
    fontWeight: 'var(--font-weight-semibold)',
    borderRadius: 'var(--radius-md)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.45 : 1,
    transition: 'background 150ms ease, box-shadow 150ms ease, opacity 150ms ease',
    outline: 'none',
    width: fullWidth ? '100%' : 'auto',
    whiteSpace: 'nowrap',
    textDecoration: 'none',
    lineHeight: 1,
    letterSpacing: '-0.01em',
    height: sz.height,
    padding: sz.padding,
    fontSize: sz.fontSize,
    gap: sz.gap,
    background: bgColor,
    color: vr.color,
    border: vr.border || 'none',
    boxShadow: hovered && !disabled ? 'var(--shadow-sm)' : 'none',
    ...extraStyle,
  };

  return (
    <button
      type={type}
      style={baseStyle}
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={() => !disabled && setHovered(true)}
      onMouseLeave={() => { setHovered(false); setPressed(false); }}
      onMouseDown={() => !disabled && setPressed(true)}
      onMouseUp={() => setPressed(false)}
      {...props}
    >
      {iconLeft && (
        <span style={{ display: 'flex', alignItems: 'center', flexShrink: 0, width: sz.iconSize, height: sz.iconSize }}>
          {iconLeft}
        </span>
      )}
      {children}
      {iconRight && (
        <span style={{ display: 'flex', alignItems: 'center', flexShrink: 0, width: sz.iconSize, height: sz.iconSize }}>
          {iconRight}
        </span>
      )}
    </button>
  );
}
