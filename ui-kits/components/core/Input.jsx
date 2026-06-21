import React from 'react';

export function Input({
  label,
  hintText,
  placeholder = 'Text placeholder',
  type = 'text',
  error,
  disabled = false,
  iconLeft = null,
  value,
  onChange,
  id,
  name,
  style: extraStyle = {},
  ...props
}) {
  const [focused, setFocused] = React.useState(false);
  const [showPassword, setShowPassword] = React.useState(false);
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
  const isPassword = type === 'password';
  const inputType = isPassword ? (showPassword ? 'text' : 'password') : type;

  const hasError = Boolean(error);
  const borderColor = hasError
    ? 'var(--color-border-error)'
    : focused
      ? 'var(--color-border-focus)'
      : 'var(--color-border-default)';
  const boxShadow = hasError
    ? focused ? 'var(--focus-ring-error)' : 'none'
    : focused ? 'var(--focus-ring)' : 'none';

  const wrapperStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    fontFamily: 'var(--font-primary)',
    width: '100%',
    ...extraStyle,
  };

  const labelStyle = {
    fontSize: 'var(--text-label-size)',
    fontWeight: 'var(--font-weight-medium)',
    color: disabled ? 'var(--color-text-disabled)' : 'var(--color-text-secondary)',
    lineHeight: 1.4,
  };

  const inputWrapStyle = {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    height: '40px',
    padding: iconLeft ? '0 12px 0 10px' : '0 12px',
    border: `1px solid ${borderColor}`,
    borderRadius: 'var(--radius-md)',
    background: disabled ? 'var(--color-surface-sunken)' : 'var(--color-surface-base)',
    boxShadow,
    transition: 'border-color 150ms ease, box-shadow 150ms ease',
  };

  const inputStyle = {
    flex: 1,
    border: 'none',
    outline: 'none',
    background: 'transparent',
    fontFamily: 'var(--font-primary)',
    fontSize: 'var(--text-body3-size)',
    fontWeight: 'var(--font-weight-regular)',
    color: disabled ? 'var(--color-text-disabled)' : 'var(--color-text-primary)',
    lineHeight: 1.5,
    width: '100%',
  };

  const iconStyle = {
    display: 'flex',
    alignItems: 'center',
    color: 'var(--color-text-tertiary)',
    flexShrink: 0,
  };

  const hintStyle = {
    fontSize: 'var(--text-caption-size)',
    fontWeight: 'var(--font-weight-regular)',
    color: hasError ? 'var(--color-text-error)' : 'var(--color-text-tertiary)',
    lineHeight: 1.3,
  };

  const EyeIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {showPassword
        ? <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>
        : <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
      }
    </svg>
  );

  return (
    <div style={wrapperStyle}>
      {label && <label htmlFor={inputId} style={labelStyle}>{label}</label>}
      <div style={inputWrapStyle}>
        {iconLeft && <span style={iconStyle}>{iconLeft}</span>}
        <input
          id={inputId}
          name={name}
          type={inputType}
          placeholder={placeholder}
          disabled={disabled}
          value={value}
          onChange={onChange}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={inputStyle}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(v => !v)}
            style={{ ...iconStyle, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
          >
            <EyeIcon />
          </button>
        )}
      </div>
      {(hintText || error) && (
        <span style={hintStyle}>{error || hintText}</span>
      )}
    </div>
  );
}
