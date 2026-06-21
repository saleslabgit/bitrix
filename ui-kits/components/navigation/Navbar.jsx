import React from 'react';

export function Navbar({
  items = [],
  ctaLabel = 'Sign In',
  onCta,
  logoSrc,
  logoAlt = 'Bitrix Sales',
  style: extraStyle = {},
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
    ...extraStyle,
  };

  const logoStyle = {
    fontWeight: 'var(--font-weight-extrabold)',
    fontSize: '22px',
    color: 'var(--color-primary-900)',
    textDecoration: 'none',
    letterSpacing: '-0.03em',
    flexShrink: 0,
  };

  const itemsRowStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    listStyle: 'none',
    margin: 0,
    padding: 0,
  };

  const chevronSvg = (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: '2px' }}>
      <polyline points="6 9 12 15 18 9"/>
    </svg>
  );

  const menuIcon = (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
    </svg>
  );

  return (
    <nav style={navStyle}>
      {/* Logo */}
      <a href="#" style={logoStyle}>
        {logoSrc
          ? <img src={logoSrc} alt={logoAlt} style={{ height: '28px' }} />
          : logoAlt}
      </a>

      {/* Desktop nav */}
      <ul style={{ ...itemsRowStyle, display: 'flex' }} className="bs-nav-desktop">
        {items.map((item, i) => (
          <li key={i} style={{ position: 'relative' }}>
            <button
              style={{
                display: 'flex', alignItems: 'center', gap: '2px',
                padding: '6px 12px', background: 'none', border: 'none',
                fontFamily: 'var(--font-primary)', fontSize: '14px',
                fontWeight: 'var(--font-weight-medium)',
                color: 'var(--color-text-secondary)',
                cursor: 'pointer', borderRadius: 'var(--radius-sm)',
                transition: 'background 150ms ease, color 150ms ease',
              }}
              onClick={() => setOpenDropdown(openDropdown === i ? null : i)}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-neutral-50)'; e.currentTarget.style.color = 'var(--color-text-primary)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'var(--color-text-secondary)'; }}
            >
              {item.label}
              {item.hasDropdown && chevronSvg}
            </button>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          onClick={onCta}
          style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            height: '36px', padding: '0 18px',
            background: 'var(--color-primary-500)', color: 'var(--color-white)',
            border: 'none', borderRadius: 'var(--radius-md)',
            fontFamily: 'var(--font-primary)', fontSize: '14px',
            fontWeight: 'var(--font-weight-semibold)',
            cursor: 'pointer', transition: 'background 150ms ease',
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--color-primary-600)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--color-primary-500)'}
        >
          {ctaLabel}
        </button>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileOpen(v => !v)}
          style={{
            display: 'none', background: 'none', border: 'none',
            cursor: 'pointer', color: 'var(--color-text-primary)', padding: '4px',
          }}
          className="bs-nav-mobile-btn"
        >
          {menuIcon}
        </button>
      </div>
    </nav>
  );
}
