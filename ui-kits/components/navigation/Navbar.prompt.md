Use `Navbar` for the top marketing/public site navigation. Renders logo + horizontal nav items + primary CTA.

```jsx
const NAV_ITEMS = [
  { label: 'Work', hasDropdown: true },
  { label: 'Product', hasDropdown: true },
  { label: 'Download', hasDropdown: true },
  { label: 'Resources', hasDropdown: true },
  { label: 'About' },
];

<Navbar
  items={NAV_ITEMS}
  ctaLabel="Sign In"
  onCta={() => navigate('/login')}
  logoAlt="Bitrix Sales"
/>
```

Height is 64px. CTA button uses primary-500 fill. Items with `hasDropdown: true` render a chevron. On mobile, the nav links hide and a hamburger appears — wire `onCta` to your router.
