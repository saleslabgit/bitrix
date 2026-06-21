import React from 'react';

const VARIANT_MAP = {
  primary: {
    bg: 'var(--color-primary-50)',
    color: 'var(--color-primary-600)',
    dot: 'var(--color-primary-500)',
  },
  info: {
    bg: 'var(--color-sec-blue-50)',
    color: 'var(--color-sec-blue-700)',
    dot: 'var(--color-sec-blue-500)',
  },
  success: {
    bg: 'var(--color-green-50)',
    color: 'var(--color-green-700)',
    dot: 'var(--color-green-500)',
  },
  warning: {
    bg: 'var(--color-yellow-50)',
    color: 'var(--color-warm-orange-700)',
    dot: 'var(--color-warm-orange-500)',
  },
  error: {
    bg: 'var(--color-red-50)',
    color: 'var(--color-red-700)',
    dot: 'var(--color-red-500)',
  },
  neutral: {
    bg: 'var(--color-neutral-100)',
    color: 'var(--color-neutral-700)',
    dot: 'var(--color-neutral-500)',
  },
};

export function Badge({
  label,
  variant = 'neutral',
  size = 'md',
  showDot = false,
  style: extraStyle = {},
}) {
  const v = VARIANT_MAP[variant] || VARIANT_MAP.neutral;
  const isSmall = size === 'sm';

  const badgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: isSmall ? '2px 6px' : '3px 8px',
    borderRadius: 'var(--radius-sm)',
    background: v.bg,
    color: v.color,
    fontFamily: 'var(--font-primary)',
    fontSize: isSmall ? '11px' : '12px',
    fontWeight: 'var(--font-weight-medium)',
    lineHeight: 1.4,
    whiteSpace: 'nowrap',
    ...extraStyle,
  };

  return (
    <span style={badgeStyle}>
      {showDot && (
        <span style={{
          width: isSmall ? '5px' : '6px',
          height: isSmall ? '5px' : '6px',
          borderRadius: '50%',
          background: v.dot,
          flexShrink: 0,
        }} />
      )}
      {label}
    </span>
  );
}
