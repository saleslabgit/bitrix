Use `Avatar` to represent users or entities. Falls back to colored initials when no image is provided or image fails to load. Color is deterministic based on initials.

```jsx
// With image
<Avatar src="/users/alice.jpg" alt="Alice Foster" size="md" />

// Initials fallback
<Avatar initials="AF" alt="Alice Foster" size="md" />

// Square avatar (for workspaces / orgs)
<Avatar initials="VD" size="lg" shape="square" />

// Sizes
<Avatar initials="HM" size="xs" />
<Avatar initials="HM" size="sm" />
<Avatar initials="HM" size="md" />  // default
<Avatar initials="HM" size="xl" />
```

**Sizes**: `xs` (24px) · `sm` (32px) · `md` (40px) · `lg` (48px) · `xl` (64px) · `2xl` (80px)
**Shapes**: `circle` (default) · `square` · `rounded`
