import React from 'react';

const SIZE_MAP = {
  xs: { size: '24px', font: '10px' },
  sm: { size: '32px', font: '12px' },
  md: { size: '40px', font: '14px' },
  lg: { size: '48px', font: '16px' },
  xl: { size: '64px', font: '20px' },
  '2xl': { size: '80px', font: '24px' },
};

// Stable color from initials
function getAvatarColor(initials) {
  const colors = [
    { bg: 'var(--color-primary-100)', color: 'var(--color-primary-700)' },
    { bg: 'var(--color-warm-orange-100)', color: 'var(--color-warm-orange-700)' },
    { bg: 'var(--color-green-100)', color: 'var(--color-green-700)' },
    { bg: 'var(--color-sec-blue-100)', color: 'var(--color-sec-blue-700)' },
    { bg: 'var(--color-yellow-100)', color: 'var(--color-yellow-700)' },
    { bg: 'var(--color-red-100)', color: 'var(--color-red-700)' },
  ];
  const idx = (initials || 'U').charCodeAt(0) % colors.length;
  return colors[idx];
}

export function Avatar({
  src,
  initials,
  alt = '',
  size = 'md',
  shape = 'circle',
  style: extraStyle = {},
}) {
  const [imgError, setImgError] = React.useState(false);
  const sz = SIZE_MAP[size] || SIZE_MAP.md;
  const borderRadius = shape === 'circle' ? '50%' : shape === 'square' ? 'var(--radius-md)' : 'var(--radius-sm)';
  const { bg, color } = getAvatarColor(initials || alt);

  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: sz.size,
    height: sz.size,
    borderRadius,
    flexShrink: 0,
    overflow: 'hidden',
    fontFamily: 'var(--font-primary)',
    fontSize: sz.font,
    fontWeight: 'var(--font-weight-semibold)',
    userSelect: 'none',
    background: bg,
    color,
    ...extraStyle,
  };

  if (src && !imgError) {
    return (
      <div style={baseStyle}>
        <img
          src={src}
          alt={alt}
          onError={() => setImgError(true)}
          style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
        />
      </div>
    );
  }

  const displayInitials = initials
    ? initials.slice(0, 2).toUpperCase()
    : alt ? alt.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() : 'U';

  return <div style={baseStyle}>{displayInitials}</div>;
}
