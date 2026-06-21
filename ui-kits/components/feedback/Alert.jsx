import React from 'react';

const VARIANT_CONFIG = {
  info: {
    bg: 'var(--color-sec-blue-50)',
    border: 'var(--color-sec-blue-200)',
    iconColor: 'var(--color-sec-blue-500)',
    titleColor: 'var(--color-sec-blue-800)',
    textColor: 'var(--color-sec-blue-700)',
    icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  success: {
    bg: 'var(--color-green-50)',
    border: 'var(--color-green-200)',
    iconColor: 'var(--color-green-500)',
    titleColor: 'var(--color-green-800)',
    textColor: 'var(--color-green-700)',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  warning: {
    bg: 'var(--color-yellow-50)',
    border: 'var(--color-yellow-200)',
    iconColor: 'var(--color-warm-orange-500)',
    titleColor: 'var(--color-warm-orange-800)',
    textColor: 'var(--color-warm-orange-700)',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  },
  error: {
    bg: 'var(--color-red-50)',
    border: 'var(--color-red-200)',
    iconColor: 'var(--color-red-500)',
    titleColor: 'var(--color-red-800)',
    textColor: 'var(--color-red-700)',
    icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
  },
};

export function Alert({
  variant = 'info',
  title,
  description,
  onDismiss,
  isDismissible = true,
  actionLabel,
  onAction,
  style: extraStyle = {},
}) {
  const [dismissed, setDismissed] = React.useState(false);
  const cfg = VARIANT_CONFIG[variant] || VARIANT_CONFIG.info;

  if (dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss && onDismiss();
  };

  const alertStyle = {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    padding: '14px 16px',
    background: cfg.bg,
    border: `1px solid ${cfg.border}`,
    borderRadius: 'var(--radius-lg)',
    fontFamily: 'var(--font-primary)',
    ...extraStyle,
  };

  const closeIcon = (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  );

  return (
    <div style={alertStyle} role="alert">
      {/* Icon */}
      <span style={{ display: 'flex', flexShrink: 0, color: cfg.iconColor, marginTop: '1px' }}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d={cfg.icon} />
        </svg>
      </span>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {title && (
          <div style={{ fontSize: '14px', fontWeight: 'var(--font-weight-semibold)', color: cfg.titleColor, lineHeight: 1.4, marginBottom: description ? '2px' : 0 }}>
            {title}
          </div>
        )}
        {description && (
          <div style={{ fontSize: '13px', fontWeight: 'var(--font-weight-regular)', color: cfg.textColor, lineHeight: 1.5 }}>
            {description}
          </div>
        )}
        {(actionLabel || onDismiss) && (
          <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
            {actionLabel && (
              <button
                onClick={onAction}
                style={{
                  background: 'none', border: 'none', padding: 0,
                  fontSize: '13px', fontWeight: 'var(--font-weight-semibold)',
                  color: cfg.iconColor, cursor: 'pointer', fontFamily: 'var(--font-primary)',
                }}
              >
                {actionLabel}
              </button>
            )}
            {isDismissible && !onDismiss && (
              <button
                onClick={handleDismiss}
                style={{
                  background: 'none', border: 'none', padding: 0,
                  fontSize: '13px', fontWeight: 'var(--font-weight-medium)',
                  color: cfg.textColor, cursor: 'pointer', fontFamily: 'var(--font-primary)',
                }}
              >
                Dismiss
              </button>
            )}
          </div>
        )}
      </div>

      {/* Close button */}
      {isDismissible && (
        <button
          onClick={handleDismiss}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0, width: '24px', height: '24px',
            background: 'none', border: 'none', cursor: 'pointer',
            color: cfg.textColor, borderRadius: 'var(--radius-sm)',
            padding: 0, transition: 'background 150ms ease',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,0,0,0.05)'}
          onMouseLeave={e => e.currentTarget.style.background = 'none'}
          aria-label="Dismiss"
        >
          {closeIcon}
        </button>
      )}
    </div>
  );
}
