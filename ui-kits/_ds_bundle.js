/* @ds-bundle: {"format":3,"namespace":"VartiDesignSystem_07c3de","components":[{"name":"Avatar","sourcePath":"components/core/Avatar.jsx"},{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"Input","sourcePath":"components/core/Input.jsx"},{"name":"Alert","sourcePath":"components/feedback/Alert.jsx"},{"name":"Navbar","sourcePath":"components/navigation/Navbar.jsx"},{"name":"Sidebar","sourcePath":"components/navigation/Sidebar.jsx"}],"sourceHashes":{"components/core/Avatar.jsx":"523a32f00bc6","components/core/Badge.jsx":"ea29eff6a508","components/core/Button.jsx":"408ec1eeb760","components/core/Card.jsx":"23f50be7ad10","components/core/Input.jsx":"3a503d0a30b8","components/feedback/Alert.jsx":"6e022cbb519e","components/navigation/Navbar.jsx":"fac9ad9519d3","components/navigation/Sidebar.jsx":"b37392cd46d5"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.VartiDesignSystem_07c3de = window.VartiDesignSystem_07c3de || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Avatar.jsx
try { (() => {
const SIZE_MAP = {
  xs: {
    size: '24px',
    font: '10px'
  },
  sm: {
    size: '32px',
    font: '12px'
  },
  md: {
    size: '40px',
    font: '14px'
  },
  lg: {
    size: '48px',
    font: '16px'
  },
  xl: {
    size: '64px',
    font: '20px'
  },
  '2xl': {
    size: '80px',
    font: '24px'
  }
};

// Stable color from initials
function getAvatarColor(initials) {
  const colors = [{
    bg: 'var(--color-primary-100)',
    color: 'var(--color-primary-700)'
  }, {
    bg: 'var(--color-warm-orange-100)',
    color: 'var(--color-warm-orange-700)'
  }, {
    bg: 'var(--color-green-100)',
    color: 'var(--color-green-700)'
  }, {
    bg: 'var(--color-sec-blue-100)',
    color: 'var(--color-sec-blue-700)'
  }, {
    bg: 'var(--color-yellow-100)',
    color: 'var(--color-yellow-700)'
  }, {
    bg: 'var(--color-red-100)',
    color: 'var(--color-red-700)'
  }];
  const idx = (initials || 'U').charCodeAt(0) % colors.length;
  return colors[idx];
}
function Avatar({
  src,
  initials,
  alt = '',
  size = 'md',
  shape = 'circle',
  style: extraStyle = {}
}) {
  const [imgError, setImgError] = React.useState(false);
  const sz = SIZE_MAP[size] || SIZE_MAP.md;
  const borderRadius = shape === 'circle' ? '50%' : shape === 'square' ? 'var(--radius-md)' : 'var(--radius-sm)';
  const {
    bg,
    color
  } = getAvatarColor(initials || alt);
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
    ...extraStyle
  };
  if (src && !imgError) {
    return /*#__PURE__*/React.createElement("div", {
      style: baseStyle
    }, /*#__PURE__*/React.createElement("img", {
      src: src,
      alt: alt,
      onError: () => setImgError(true),
      style: {
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        display: 'block'
      }
    }));
  }
  const displayInitials = initials ? initials.slice(0, 2).toUpperCase() : alt ? alt.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() : 'U';
  return /*#__PURE__*/React.createElement("div", {
    style: baseStyle
  }, displayInitials);
}
Object.assign(__ds_scope, { Avatar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Avatar.jsx", error: String((e && e.message) || e) }); }

// components/core/Badge.jsx
try { (() => {
const VARIANT_MAP = {
  primary: {
    bg: 'var(--color-primary-50)',
    color: 'var(--color-primary-600)',
    dot: 'var(--color-primary-500)'
  },
  info: {
    bg: 'var(--color-sec-blue-50)',
    color: 'var(--color-sec-blue-700)',
    dot: 'var(--color-sec-blue-500)'
  },
  success: {
    bg: 'var(--color-green-50)',
    color: 'var(--color-green-700)',
    dot: 'var(--color-green-500)'
  },
  warning: {
    bg: 'var(--color-yellow-50)',
    color: 'var(--color-warm-orange-700)',
    dot: 'var(--color-warm-orange-500)'
  },
  error: {
    bg: 'var(--color-red-50)',
    color: 'var(--color-red-700)',
    dot: 'var(--color-red-500)'
  },
  neutral: {
    bg: 'var(--color-neutral-100)',
    color: 'var(--color-neutral-700)',
    dot: 'var(--color-neutral-500)'
  }
};
function Badge({
  label,
  variant = 'neutral',
  size = 'md',
  showDot = false,
  style: extraStyle = {}
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
    ...extraStyle
  };
  return /*#__PURE__*/React.createElement("span", {
    style: badgeStyle
  }, showDot && /*#__PURE__*/React.createElement("span", {
    style: {
      width: isSmall ? '5px' : '6px',
      height: isSmall ? '5px' : '6px',
      borderRadius: '50%',
      background: v.dot,
      flexShrink: 0
    }
  }), label);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const SIZE_STYLES = {
  XS: {
    height: '24px',
    padding: '0 10px',
    fontSize: '11px',
    gap: '4px',
    iconSize: '12px'
  },
  S: {
    height: '28px',
    padding: '0 12px',
    fontSize: '12px',
    gap: '4px',
    iconSize: '14px'
  },
  M: {
    height: '32px',
    padding: '0 14px',
    fontSize: '13px',
    gap: '6px',
    iconSize: '14px'
  },
  L: {
    height: '40px',
    padding: '0 18px',
    fontSize: '14px',
    gap: '6px',
    iconSize: '16px'
  },
  XL: {
    height: '44px',
    padding: '0 20px',
    fontSize: '14px',
    gap: '8px',
    iconSize: '16px'
  },
  XXL: {
    height: '48px',
    padding: '0 24px',
    fontSize: '16px',
    gap: '8px',
    iconSize: '18px'
  }
};
const VARIANT_STYLES = {
  primary: {
    background: 'var(--color-primary-500)',
    color: 'var(--color-white)',
    border: 'none',
    hoverBg: 'var(--color-primary-600)',
    activeBg: 'var(--color-primary-700)'
  },
  'primary-light': {
    background: 'var(--color-primary-50)',
    color: 'var(--color-primary-500)',
    border: 'none',
    hoverBg: 'var(--color-primary-100)',
    activeBg: 'var(--color-primary-200)'
  },
  secondary: {
    background: 'transparent',
    color: 'var(--color-primary-500)',
    border: '1px solid var(--color-primary-400)',
    hoverBg: 'var(--color-primary-50)',
    activeBg: 'var(--color-primary-100)'
  },
  ghost: {
    background: 'transparent',
    color: 'var(--color-neutral-700)',
    border: '1px solid var(--color-neutral-200)',
    hoverBg: 'var(--color-neutral-50)',
    activeBg: 'var(--color-neutral-100)'
  },
  danger: {
    background: 'var(--color-red-500)',
    color: 'var(--color-white)',
    border: 'none',
    hoverBg: 'var(--color-red-600)',
    activeBg: 'var(--color-red-700)'
  }
};
function Button({
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
    ...extraStyle
  };
  return /*#__PURE__*/React.createElement("button", _extends({
    type: type,
    style: baseStyle,
    disabled: disabled,
    onClick: onClick,
    onMouseEnter: () => !disabled && setHovered(true),
    onMouseLeave: () => {
      setHovered(false);
      setPressed(false);
    },
    onMouseDown: () => !disabled && setPressed(true),
    onMouseUp: () => setPressed(false)
  }, props), iconLeft && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      alignItems: 'center',
      flexShrink: 0,
      width: sz.iconSize,
      height: sz.iconSize
    }
  }, iconLeft), children, iconRight && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      alignItems: 'center',
      flexShrink: 0,
      width: sz.iconSize,
      height: sz.iconSize
    }
  }, iconRight));
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const PADDING_MAP = {
  none: '0',
  sm: 'var(--space-5)',
  /* 16px */
  md: 'var(--space-7)',
  /* 24px */
  lg: 'var(--space-8)' /* 32px */
};
function Card({
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
    lg: 'var(--shadow-lg)'
  };
  const radiusMap = {
    sm: 'var(--radius-sm)',
    md: 'var(--radius-md)',
    lg: 'var(--radius-lg)',
    xl: 'var(--radius-xl)'
  };
  const cardStyle = {
    background: background || 'var(--color-surface-base)',
    borderRadius: radiusMap[radius] || radiusMap.lg,
    boxShadow: shadowMap[shadow] || shadowMap.md,
    border: hasBorder ? '1px solid var(--color-border-default)' : 'none',
    padding: PADDING_MAP[padding] || PADDING_MAP.md,
    transition: 'box-shadow 150ms ease, transform 150ms ease',
    cursor: isClickable ? 'pointer' : 'default',
    boxShadow: isClickable && hovered ? 'var(--shadow-lg)' : shadowMap[shadow] || shadowMap.md,
    transform: isClickable && hovered ? 'translateY(-1px)' : 'none',
    ...extraStyle
  };
  return /*#__PURE__*/React.createElement("div", _extends({
    style: cardStyle,
    onClick: onClick,
    onMouseEnter: () => isClickable && setHovered(true),
    onMouseLeave: () => setHovered(false)
  }, props), children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function Input({
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
  const inputType = isPassword ? showPassword ? 'text' : 'password' : type;
  const hasError = Boolean(error);
  const borderColor = hasError ? 'var(--color-border-error)' : focused ? 'var(--color-border-focus)' : 'var(--color-border-default)';
  const boxShadow = hasError ? focused ? 'var(--focus-ring-error)' : 'none' : focused ? 'var(--focus-ring)' : 'none';
  const wrapperStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    fontFamily: 'var(--font-primary)',
    width: '100%',
    ...extraStyle
  };
  const labelStyle = {
    fontSize: 'var(--text-label-size)',
    fontWeight: 'var(--font-weight-medium)',
    color: disabled ? 'var(--color-text-disabled)' : 'var(--color-text-secondary)',
    lineHeight: 1.4
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
    transition: 'border-color 150ms ease, box-shadow 150ms ease'
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
    width: '100%'
  };
  const iconStyle = {
    display: 'flex',
    alignItems: 'center',
    color: 'var(--color-text-tertiary)',
    flexShrink: 0
  };
  const hintStyle = {
    fontSize: 'var(--text-caption-size)',
    fontWeight: 'var(--font-weight-regular)',
    color: hasError ? 'var(--color-text-error)' : 'var(--color-text-tertiary)',
    lineHeight: 1.3
  };
  const EyeIcon = () => /*#__PURE__*/React.createElement("svg", {
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, showPassword ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
    d: "M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "1",
    y1: "1",
    x2: "23",
    y2: "23"
  })) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
    d: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "3"
  })));
  return /*#__PURE__*/React.createElement("div", {
    style: wrapperStyle
  }, label && /*#__PURE__*/React.createElement("label", {
    htmlFor: inputId,
    style: labelStyle
  }, label), /*#__PURE__*/React.createElement("div", {
    style: inputWrapStyle
  }, iconLeft && /*#__PURE__*/React.createElement("span", {
    style: iconStyle
  }, iconLeft), /*#__PURE__*/React.createElement("input", _extends({
    id: inputId,
    name: name,
    type: inputType,
    placeholder: placeholder,
    disabled: disabled,
    value: value,
    onChange: onChange,
    onFocus: () => setFocused(true),
    onBlur: () => setFocused(false),
    style: inputStyle
  }, props)), isPassword && /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => setShowPassword(v => !v),
    style: {
      ...iconStyle,
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      padding: 0
    }
  }, /*#__PURE__*/React.createElement(EyeIcon, null))), (hintText || error) && /*#__PURE__*/React.createElement("span", {
    style: hintStyle
  }, error || hintText));
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Input.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Alert.jsx
try { (() => {
const VARIANT_CONFIG = {
  info: {
    bg: 'var(--color-sec-blue-50)',
    border: 'var(--color-sec-blue-200)',
    iconColor: 'var(--color-sec-blue-500)',
    titleColor: 'var(--color-sec-blue-800)',
    textColor: 'var(--color-sec-blue-700)',
    icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  },
  success: {
    bg: 'var(--color-green-50)',
    border: 'var(--color-green-200)',
    iconColor: 'var(--color-green-500)',
    titleColor: 'var(--color-green-800)',
    textColor: 'var(--color-green-700)',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
  },
  warning: {
    bg: 'var(--color-yellow-50)',
    border: 'var(--color-yellow-200)',
    iconColor: 'var(--color-warm-orange-500)',
    titleColor: 'var(--color-warm-orange-800)',
    textColor: 'var(--color-warm-orange-700)',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
  },
  error: {
    bg: 'var(--color-red-50)',
    border: 'var(--color-red-200)',
    iconColor: 'var(--color-red-500)',
    titleColor: 'var(--color-red-800)',
    textColor: 'var(--color-red-700)',
    icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
  }
};
function Alert({
  variant = 'info',
  title,
  description,
  onDismiss,
  isDismissible = true,
  actionLabel,
  onAction,
  style: extraStyle = {}
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
    ...extraStyle
  };
  const closeIcon = /*#__PURE__*/React.createElement("svg", {
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "18",
    y1: "6",
    x2: "6",
    y2: "18"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "6",
    y1: "6",
    x2: "18",
    y2: "18"
  }));
  return /*#__PURE__*/React.createElement("div", {
    style: alertStyle,
    role: "alert"
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      flexShrink: 0,
      color: cfg.iconColor,
      marginTop: '1px'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: cfg.icon
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '14px',
      fontWeight: 'var(--font-weight-semibold)',
      color: cfg.titleColor,
      lineHeight: 1.4,
      marginBottom: description ? '2px' : 0
    }
  }, title), description && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '13px',
      fontWeight: 'var(--font-weight-regular)',
      color: cfg.textColor,
      lineHeight: 1.5
    }
  }, description), (actionLabel || onDismiss) && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: '12px',
      marginTop: '10px'
    }
  }, actionLabel && /*#__PURE__*/React.createElement("button", {
    onClick: onAction,
    style: {
      background: 'none',
      border: 'none',
      padding: 0,
      fontSize: '13px',
      fontWeight: 'var(--font-weight-semibold)',
      color: cfg.iconColor,
      cursor: 'pointer',
      fontFamily: 'var(--font-primary)'
    }
  }, actionLabel), isDismissible && !onDismiss && /*#__PURE__*/React.createElement("button", {
    onClick: handleDismiss,
    style: {
      background: 'none',
      border: 'none',
      padding: 0,
      fontSize: '13px',
      fontWeight: 'var(--font-weight-medium)',
      color: cfg.textColor,
      cursor: 'pointer',
      fontFamily: 'var(--font-primary)'
    }
  }, "Dismiss"))), isDismissible && /*#__PURE__*/React.createElement("button", {
    onClick: handleDismiss,
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      width: '24px',
      height: '24px',
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      color: cfg.textColor,
      borderRadius: 'var(--radius-sm)',
      padding: 0,
      transition: 'background 150ms ease'
    },
    onMouseEnter: e => e.currentTarget.style.background = 'rgba(0,0,0,0.05)',
    onMouseLeave: e => e.currentTarget.style.background = 'none',
    "aria-label": "Dismiss"
  }, closeIcon));
}
Object.assign(__ds_scope, { Alert });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Alert.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Navbar.jsx
try { (() => {
function Navbar({
  items = [],
  ctaLabel = 'Sign In',
  onCta,
  logoSrc,
  logoAlt = 'Bitrix Sales',
  style: extraStyle = {}
}) {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [openDropdown, setOpenDropdown] = React.useState(null);
  const navStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '64px',
    padding: '0 32px',
    background: 'var(--color-surface-base)',
    borderBottom: '1px solid var(--color-border-default)',
    fontFamily: 'var(--font-primary)',
    position: 'relative',
    ...extraStyle
  };
  const logoStyle = {
    fontWeight: 'var(--font-weight-extrabold)',
    fontSize: '22px',
    color: 'var(--color-primary-900)',
    textDecoration: 'none',
    letterSpacing: '-0.03em',
    flexShrink: 0
  };
  const itemsRowStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    listStyle: 'none',
    margin: 0,
    padding: 0
  };
  const chevronSvg = /*#__PURE__*/React.createElement("svg", {
    width: "12",
    height: "12",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    style: {
      marginLeft: '2px'
    }
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "6 9 12 15 18 9"
  }));
  const menuIcon = /*#__PURE__*/React.createElement("svg", {
    width: "20",
    height: "20",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "3",
    y1: "6",
    x2: "21",
    y2: "6"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "3",
    y1: "12",
    x2: "21",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "3",
    y1: "18",
    x2: "21",
    y2: "18"
  }));
  return /*#__PURE__*/React.createElement("nav", {
    style: navStyle
  }, /*#__PURE__*/React.createElement("a", {
    href: "#",
    style: logoStyle
  }, logoSrc ? /*#__PURE__*/React.createElement("img", {
    src: logoSrc,
    alt: logoAlt,
    style: {
      height: '28px'
    }
  }) : logoAlt), /*#__PURE__*/React.createElement("ul", {
    style: {
      ...itemsRowStyle,
      display: 'flex'
    },
    className: "bs-nav-desktop"
  }, items.map((item, i) => /*#__PURE__*/React.createElement("li", {
    key: i,
    style: {
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '2px',
      padding: '6px 12px',
      background: 'none',
      border: 'none',
      fontFamily: 'var(--font-primary)',
      fontSize: '14px',
      fontWeight: 'var(--font-weight-medium)',
      color: 'var(--color-text-secondary)',
      cursor: 'pointer',
      borderRadius: 'var(--radius-sm)',
      transition: 'background 150ms ease, color 150ms ease'
    },
    onClick: () => setOpenDropdown(openDropdown === i ? null : i),
    onMouseEnter: e => {
      e.currentTarget.style.background = 'var(--color-neutral-50)';
      e.currentTarget.style.color = 'var(--color-text-primary)';
    },
    onMouseLeave: e => {
      e.currentTarget.style.background = 'none';
      e.currentTarget.style.color = 'var(--color-text-secondary)';
    }
  }, item.label, item.hasDropdown && chevronSvg)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onCta,
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '36px',
      padding: '0 18px',
      background: 'var(--color-primary-500)',
      color: 'var(--color-white)',
      border: 'none',
      borderRadius: 'var(--radius-md)',
      fontFamily: 'var(--font-primary)',
      fontSize: '14px',
      fontWeight: 'var(--font-weight-semibold)',
      cursor: 'pointer',
      transition: 'background 150ms ease',
      whiteSpace: 'nowrap'
    },
    onMouseEnter: e => e.currentTarget.style.background = 'var(--color-primary-600)',
    onMouseLeave: e => e.currentTarget.style.background = 'var(--color-primary-500)'
  }, ctaLabel), /*#__PURE__*/React.createElement("button", {
    onClick: () => setMobileOpen(v => !v),
    style: {
      display: 'none',
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      color: 'var(--color-text-primary)',
      padding: '4px'
    },
    className: "bs-nav-mobile-btn"
  }, menuIcon)));
}
Object.assign(__ds_scope, { Navbar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Navbar.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Sidebar.jsx
try { (() => {
// ── Icon primitives ─────────────────────────────────────────────
function Icon({
  d,
  size = 18
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: d
  }));
}
const ICONS = {
  dashboard: 'M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z',
  calendar: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  notifications: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9',
  analytics: 'M18 20V10M12 20V4M6 20v-6',
  settings: 'M12 15a3 3 0 100-6 3 3 0 000 6z M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z',
  support: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  logout: 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1',
  income: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  search: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  chevronDown: 'M19 9l-7 7-7-7',
  chevronRight: 'M9 18l6-6-6-6'
};
function SidebarItem({
  item,
  isCollapsed,
  depth = 0
}) {
  const [expanded, setExpanded] = React.useState(false);
  const hasChildren = item.children && item.children.length > 0;
  const icon = ICONS[item.icon] || ICONS.dashboard;
  const itemStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: isCollapsed ? '10px' : `10px ${depth > 0 ? '12px' : '12px'} 10px ${depth > 0 ? '44px' : '12px'}`,
    borderRadius: 'var(--radius-md)',
    cursor: 'pointer',
    transition: 'background 150ms ease, color 150ms ease',
    background: item.isActive ? 'var(--color-primary-50)' : 'transparent',
    color: item.isActive ? 'var(--color-primary-600)' : 'var(--color-neutral-600)',
    fontFamily: 'var(--font-primary)',
    fontSize: '14px',
    fontWeight: item.isActive ? 'var(--font-weight-semibold)' : 'var(--font-weight-regular)',
    justifyContent: isCollapsed ? 'center' : 'flex-start',
    userSelect: 'none',
    position: 'relative'
  };
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: itemStyle,
    onMouseEnter: e => {
      if (!item.isActive) {
        e.currentTarget.style.background = 'var(--color-neutral-50)';
        e.currentTarget.style.color = 'var(--color-neutral-800)';
      }
    },
    onMouseLeave: e => {
      if (!item.isActive) {
        e.currentTarget.style.background = 'transparent';
        e.currentTarget.style.color = 'var(--color-neutral-600)';
      }
    },
    onClick: () => hasChildren ? setExpanded(v => !v) : item.onClick && item.onClick()
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      alignItems: 'center',
      flexShrink: 0,
      color: item.isActive ? 'var(--color-primary-500)' : 'inherit'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    d: icon,
    size: 18
  })), !isCollapsed && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1
    }
  }, item.label), hasChildren && /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      transition: 'transform 200ms ease',
      transform: expanded ? 'rotate(180deg)' : 'none'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    d: ICONS.chevronDown,
    size: 14
  })))), hasChildren && expanded && !isCollapsed && /*#__PURE__*/React.createElement("div", null, item.children.map((child, i) => /*#__PURE__*/React.createElement(SidebarItem, {
    key: i,
    item: child,
    isCollapsed: false,
    depth: depth + 1
  }))));
}
function Sidebar({
  items = [],
  sections = [],
  isCollapsed = false,
  variant = 'light',
  logoText = 'Bitrix Sales',
  onLogout,
  style: extraStyle = {}
}) {
  const isDark = variant === 'dark';
  const width = isCollapsed ? '64px' : '240px';
  const sidebarStyle = {
    display: 'flex',
    flexDirection: 'column',
    width,
    minHeight: '100vh',
    background: isDark ? '#111827' : 'var(--color-surface-base)',
    borderRight: isDark ? 'none' : '1px solid var(--color-border-default)',
    padding: '0',
    transition: 'width 200ms ease',
    fontFamily: 'var(--font-primary)',
    flexShrink: 0,
    overflow: 'hidden',
    ...extraStyle
  };
  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: isCollapsed ? 'center' : 'flex-start',
    padding: '20px 16px',
    fontWeight: 'var(--font-weight-extrabold)',
    fontSize: '20px',
    color: isDark ? '#fff' : 'var(--color-primary-900)',
    letterSpacing: '-0.03em',
    flexShrink: 0,
    borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'var(--color-border-default)'}`
  };
  const searchStyle = {
    display: isCollapsed ? 'none' : 'flex',
    alignItems: 'center',
    gap: '8px',
    margin: '12px 16px',
    padding: '8px 12px',
    borderRadius: 'var(--radius-md)',
    border: `1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'var(--color-border-default)'}`,
    background: isDark ? 'rgba(255,255,255,0.05)' : 'var(--color-bg-grey)',
    color: isDark ? 'rgba(255,255,255,0.4)' : 'var(--color-text-placeholder)',
    fontSize: '13px',
    cursor: 'text'
  };
  const sectionLabelStyle = {
    padding: '16px 16px 4px',
    fontSize: '10px',
    fontWeight: 'var(--font-weight-semibold)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: isDark ? 'rgba(255,255,255,0.35)' : 'var(--color-text-placeholder)',
    display: isCollapsed ? 'none' : 'block'
  };
  const navStyle = {
    flex: 1,
    padding: '8px',
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    overflowY: 'auto'
  };
  const darkItemOverride = isDark ? {
    '--dark-text': 'rgba(255,255,255,0.65)',
    '--dark-active-bg': 'rgba(255,255,255,0.1)'
  } : {};
  const allItems = sections.length > 0 ? sections.flatMap(s => [{
    _sectionLabel: s.label
  }, ...s.items]) : items;
  return /*#__PURE__*/React.createElement("div", {
    style: sidebarStyle
  }, /*#__PURE__*/React.createElement("div", {
    style: logoStyle
  }, isCollapsed ? /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '32px',
      height: '32px',
      background: 'var(--color-primary-500)',
      borderRadius: '8px',
      color: '#fff',
      fontSize: '16px',
      fontWeight: 800
    }
  }, logoText.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()) : logoText), /*#__PURE__*/React.createElement("div", {
    style: searchStyle
  }, /*#__PURE__*/React.createElement(Icon, {
    d: ICONS.search,
    size: 14
  }), /*#__PURE__*/React.createElement("span", null, "Search")), /*#__PURE__*/React.createElement("div", {
    style: navStyle
  }, allItems.map((item, i) => {
    if (item._sectionLabel) {
      return /*#__PURE__*/React.createElement("div", {
        key: `sec-${i}`,
        style: sectionLabelStyle
      }, item._sectionLabel);
    }
    const adjustedItem = isDark ? {
      ...item,
      isActive: item.isActive
    } : item;
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      style: isDark ? {
        color: item.isActive ? '#fff' : 'rgba(255,255,255,0.65)'
      } : {}
    }, /*#__PURE__*/React.createElement(SidebarItem, {
      item: adjustedItem,
      isCollapsed: isCollapsed
    }));
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px',
      borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'var(--color-border-default)'}`
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      padding: '10px 12px',
      borderRadius: 'var(--radius-md)',
      cursor: 'pointer',
      color: isDark ? 'rgba(255,255,255,0.55)' : 'var(--color-neutral-500)',
      fontSize: '14px',
      fontWeight: 'var(--font-weight-regular)',
      justifyContent: isCollapsed ? 'center' : 'flex-start'
    },
    onClick: onLogout,
    onMouseEnter: e => {
      e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.06)' : 'var(--color-neutral-50)';
      e.currentTarget.style.color = isDark ? '#fff' : 'var(--color-text-primary)';
    },
    onMouseLeave: e => {
      e.currentTarget.style.background = 'transparent';
      e.currentTarget.style.color = isDark ? 'rgba(255,255,255,0.55)' : 'var(--color-neutral-500)';
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    d: ICONS.logout,
    size: 18
  }), !isCollapsed && /*#__PURE__*/React.createElement("span", null, "Logout"))));
}
Object.assign(__ds_scope, { Sidebar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Sidebar.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Avatar = __ds_scope.Avatar;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Alert = __ds_scope.Alert;

__ds_ns.Navbar = __ds_scope.Navbar;

__ds_ns.Sidebar = __ds_scope.Sidebar;

})();
