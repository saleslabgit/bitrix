Use `Badge` for status labels, category tags, and count indicators. Never for interactive actions — use Button for those.

```jsx
<Badge label="Active" variant="success" showDot />
<Badge label="Pending" variant="warning" />
<Badge label="Error" variant="error" showDot />
<Badge label="New" variant="primary" />
<Badge label="Info" variant="info" size="sm" />
<Badge label="Draft" variant="neutral" />
```

**Variants**: `primary` (blue) · `info` (cyan) · `success` (green) · `warning` (amber) · `error` (red) · `neutral` (grey)
**Sizes**: `sm` (11px, 6px padding) · `md` (12px, 8px padding)
`showDot` adds a small colored circle on the left — useful for live status indicators.
