Use `Alert` for inline feedback messages — info notices, success confirmations, warnings, and errors. Not for toasts or modals.

```jsx
// Info banner
<Alert
  variant="info"
  title="Information text"
  description="Review the changes and feel free to contact us if you have any questions."
  actionLabel="Learn more"
  onAction={() => {}}
/>

// Success
<Alert variant="success" title="New version is available!" description="All pages and reports now load faster." actionLabel="Try it now" />

// Warning
<Alert variant="warning" title="Your trial ends in 3 days" isDismissible={false} />

// Error
<Alert variant="error" title="Error text" description="Please try again later or contact support team." actionLabel="Learn more" />
```

**Variants**: `info` (blue) · `success` (green) · `warning` (amber) · `error` (red)
Alerts self-dismiss on X click (internal state). Pass `onDismiss` to hook into external state. Set `isDismissible={false}` to hide the X button.
