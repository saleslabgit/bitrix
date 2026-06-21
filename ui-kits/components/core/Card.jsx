import React from 'react';

const PADDING_MAP = {
  none: '0',
  sm:   'var(--space-5)',    /* 16px */
  md:   'var(--space-7)',    /* 24px */
  lg:   'var(--space-8)',    /* 32px */
};

export function Card({
  children,
  padding = 'md',
  hasBorder = true,
  shadow = 'md',
  radius = 'lg',
  background,
  style: extraStyle = {},
  onClick,
  ...props
}) {
  const [hovered, setHovered] = React.useState(false);
  const isClickable = Boolean(onClick);

  const shadowMap = {
    none: 'none',
    xs: 'var(--shadow-xs)',
    sm: 'var(--shadow-sm)',
    md: 'var(--shadow-md)',
    lg: 'var(--shadow-lg)',
  };

  const radiusMap = {
    sm: 'var(--radius-sm)',
    md: 'var(--radius-md)',
    lg: 'var(--radius-lg)',
    xl: 'var(--radius-xl)',
  };

  const cardStyle = {
    background: background || 'var(--color-surface-base)',
    borderRadius: radiusMap[radius] || radiusMap.lg,
    boxShadow: shadowMap[shadow] || shadowMap.md,
    border: hasBorder ? '1px solid var(--color-border-default)' : 'none',
    padding: PADDING_MAP[padding] || PADDING_MAP.md,
    transition: 'box-shadow 150ms ease, transform 150ms ease',
    cursor: isClickable ? 'pointer' : 'default',
    boxShadow: isClickable && hovered
      ? 'var(--shadow-lg)'
      : shadowMap[shadow] || shadowMap.md,
    transform: isClickable && hovered ? 'translateY(-1px)' : 'none',
    ...extraStyle,
  };

  return (
    <div
      style={cardStyle}
      onClick={onClick}
      onMouseEnter={() => isClickable && setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      {...props}
    >
      {children}
    </div>
  );
}
