Use `Sidebar` for the main app navigation shell. Supports flat items or grouped sections, light/dark variants, and icon-only collapsed mode.

```jsx
// Basic usage
<Sidebar
  items={[
    { label: 'Dashboard', icon: 'dashboard', isActive: true },
    { label: 'Calendar', icon: 'calendar' },
    { label: 'Notifications', icon: 'notifications' },
    { label: 'Analytics', icon: 'analytics' },
    { label: 'Support', icon: 'support' },
  ]}
  onLogout={() => signOut()}
/>

// Grouped sections
<Sidebar
  sections={[
    { label: 'Main', items: [
      { label: 'Dashboard', icon: 'dashboard', isActive: true },
      { label: 'Income', icon: 'income', children: [
        { label: 'Overview' }, { label: 'Reports' }
      ]},
    ]},
    { label: 'Settings', items: [
      { label: 'Settings', icon: 'settings' },
      { label: 'Support', icon: 'support' },
    ]},
  ]}
/>

// Dark collapsed
<Sidebar variant="dark" isCollapsed={true} items={…} />
```

Width: 240px expanded, 64px collapsed. Active item uses primary-50 background + primary-600 text. Supports nested children with chevron expand/collapse.
