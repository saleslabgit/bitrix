Use `Button` for any interactive action. Prefer `primary` for main CTAs, `secondary` for alternative actions, `ghost` for low-emphasis or tertiary actions, `danger` for destructive actions.

```jsx
// Primary CTA
<Button variant="primary" size="L">Sign In</Button>

// With icon
<Button variant="primary" size="M" iconLeft={<StarIcon width={14} height={14} />}>Add to list</Button>

// Secondary / outline
<Button variant="secondary" size="M">Cancel</Button>

// Ghost / subtle
<Button variant="ghost" size="S">View all</Button>

// Danger
<Button variant="danger" size="M" disabled>Delete account</Button>

// Full-width
<Button variant="primary" size="XL" fullWidth>Continue</Button>
```

**Variants**: `primary`, `primary-light`, `secondary`, `ghost`, `danger`
**Sizes**: `XS` (24px) · `S` (28px) · `M` (32px) · `L` (40px) · `XL` (44px) · `XXL` (48px)

Hover darkens background one step; active darkens two steps. Disabled state is 45% opacity + no-cursor.
