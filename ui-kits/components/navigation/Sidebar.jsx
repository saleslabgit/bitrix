import React from 'react';

// ── Icon primitives ─────────────────────────────────────────────
function Icon({ d, size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

const ICONS = {
  dashboard:     'M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z',
  calendar:      'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  notifications: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9',
  analytics:     'M18 20V10M12 20V4M6 20v-6',
  settings:      'M12 15a3 3 0 100-6 3 3 0 000 6z M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z',
  support:       'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  logout:        'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1',
  income:        'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  search:        'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  chevronDown:   'M19 9l-7 7-7-7',
  chevronRight:  'M9 18l6-6-6-6',
};

function SidebarItem({ item, isCollapsed, depth = 0 }) {
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
    position: 'relative',
  };

  return (
    <>
      <div
        style={itemStyle}
        onMouseEnter={e => { if (!item.isActive) { e.currentTarget.style.background = 'var(--color-neutral-50)'; e.currentTarget.style.color = 'var(--color-neutral-800)'; }}}
        onMouseLeave={e => { if (!item.isActive) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--color-neutral-600)'; }}}
        onClick={() => hasChildren ? setExpanded(v => !v) : item.onClick && item.onClick()}
      >
        <span style={{ display: 'flex', alignItems: 'center', flexShrink: 0, color: item.isActive ? 'var(--color-primary-500)' : 'inherit' }}>
          <Icon d={icon} size={18} />
        </span>
        {!isCollapsed && (
          <>
            <span style={{ flex: 1 }}>{item.label}</span>
            {hasChildren && (
              <span style={{ display: 'flex', transition: 'transform 200ms ease', transform: expanded ? 'rotate(180deg)' : 'none' }}>
                <Icon d={ICONS.chevronDown} size={14} />
              </span>
            )}
          </>
        )}
      </div>
      {hasChildren && expanded && !isCollapsed && (
        <div>
          {item.children.map((child, i) => (
            <SidebarItem key={i} item={child} isCollapsed={false} depth={depth + 1} />
          ))}
        </div>
      )}
    </>
  );
}

export function Sidebar({
  items = [],
  sections = [],
  isCollapsed = false,
  variant = 'light',
  logoText = 'Bitrix Sales',
  onLogout,
  style: extraStyle = {},
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
    ...extraStyle,
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
    borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'var(--color-border-default)'}`,
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
    cursor: 'text',
  };

  const sectionLabelStyle = {
    padding: '16px 16px 4px',
    fontSize: '10px',
    fontWeight: 'var(--font-weight-semibold)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: isDark ? 'rgba(255,255,255,0.35)' : 'var(--color-text-placeholder)',
    display: isCollapsed ? 'none' : 'block',
  };

  const navStyle = {
    flex: 1,
    padding: '8px',
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    overflowY: 'auto',
  };

  const darkItemOverride = isDark ? {
    '--dark-text': 'rgba(255,255,255,0.65)',
    '--dark-active-bg': 'rgba(255,255,255,0.1)',
  } : {};

  const allItems = sections.length > 0
    ? sections.flatMap(s => [{ _sectionLabel: s.label }, ...s.items])
    : items;

  return (
    <div style={sidebarStyle}>
      {/* Logo */}
      <div style={logoStyle}>
        {isCollapsed
          ? <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '32px', height: '32px', background: 'var(--color-primary-500)', borderRadius: '8px', color: '#fff', fontSize: '16px', fontWeight: 800 }}>{logoText.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()}</span>
          : logoText
        }
      </div>

      {/* Search */}
      <div style={searchStyle}>
        <Icon d={ICONS.search} size={14} />
        <span>Search</span>
      </div>

      {/* Nav items */}
      <div style={navStyle}>
        {allItems.map((item, i) => {
          if (item._sectionLabel) {
            return <div key={`sec-${i}`} style={sectionLabelStyle}>{item._sectionLabel}</div>;
          }
          const adjustedItem = isDark ? {
            ...item,
            isActive: item.isActive,
          } : item;
          return (
            <div key={i} style={isDark ? { color: item.isActive ? '#fff' : 'rgba(255,255,255,0.65)' } : {}}>
              <SidebarItem item={adjustedItem} isCollapsed={isCollapsed} />
            </div>
          );
        })}
      </div>

      {/* Logout */}
      <div style={{ padding: '8px', borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'var(--color-border-default)'}` }}>
        <div
          style={{
            display: 'flex', alignItems: 'center', gap: '10px',
            padding: '10px 12px', borderRadius: 'var(--radius-md)',
            cursor: 'pointer', color: isDark ? 'rgba(255,255,255,0.55)' : 'var(--color-neutral-500)',
            fontSize: '14px', fontWeight: 'var(--font-weight-regular)',
            justifyContent: isCollapsed ? 'center' : 'flex-start',
          }}
          onClick={onLogout}
          onMouseEnter={e => { e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.06)' : 'var(--color-neutral-50)'; e.currentTarget.style.color = isDark ? '#fff' : 'var(--color-text-primary)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = isDark ? 'rgba(255,255,255,0.55)' : 'var(--color-neutral-500)'; }}
        >
          <Icon d={ICONS.logout} size={18} />
          {!isCollapsed && <span>Logout</span>}
        </div>
      </div>
    </div>
  );
}
