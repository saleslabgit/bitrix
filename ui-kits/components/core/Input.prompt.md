Use `Input` for any text data-entry field. Supports label, hint text, error state, left icon, and password toggle.

```jsx
// Basic
<Input placeholder="Text placeholder" />

// With label and hint
<Input label="Email" hintText="We'll never share your email." placeholder="example@domain.com" type="email" />

// Error state
<Input label="Email" error="Please enter a valid email address." value="bad-email" type="email" />

// With left icon
<Input iconLeft={<SearchIcon width={16} height={16} />} placeholder="Search…" />

// Password with show/hide toggle
<Input label="Password" type="password" placeholder="••••••••" />

// Disabled
<Input label="Username" disabled placeholder="johndoe" />
```

**States**: Default → Focused (blue border + glow) → Error (red border + glow) → Disabled (muted)

Height is fixed at 40px. Full-width by default (wrap in a sized container or set width via `style`).
