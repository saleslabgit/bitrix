Use `Card` as a generic content container with a surface, border, and shadow. Compose it with other primitives for richer layouts.

```jsx
// Basic content card
<Card>
  <h3>Card title</h3>
  <p>Some body content here.</p>
</Card>

// No border, custom shadow
<Card hasBorder={false} shadow="lg" padding="lg">
  <img src="…" />
</Card>

// Clickable card (hover lift)
<Card onClick={() => navigate('/detail')}>
  <p>Click me</p>
</Card>

// Stat card
<Card padding="md" shadow="sm">
  <div>Total Revenue</div>
  <div style={{ fontSize: 32, fontWeight: 700 }}>$48,295</div>
  <Badge label="+12.4%" variant="success" showDot />
</Card>
```

Cards have a 1px border (`--color-border-default`), `--shadow-md`, and `--radius-lg` by default. Clickable cards lift on hover with `--shadow-lg`.
