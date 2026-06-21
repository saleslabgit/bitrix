# Bitrix Sales Web App UI Kit

Interactive dashboard prototype for the Bitrix Sales SaaS web application.

## Overview

Full-featured dashboard UI built on top of the Bitrix Sales Design System component library. Demonstrates real-world composition of tokens + components into a working product interface.

## Screens

| Screen | Description |
|---|---|
| **Dashboard** | Stats overview, revenue chart, activity feed |
| **Analytics** | Page views, sessions, traffic sources |
| **Calendar** | Monthly calendar with daily event view |
| **Notifications** | Unread/read notification list |
| **Settings** | Profile editing form |
| **Support** | Ticket submission form |

## Usage

Open `index.html` directly in a browser. Navigation state persists via `localStorage` — the last-viewed screen is remembered on refresh.

## Components used

`Sidebar`, `Button`, `Badge`, `Avatar`, `Card`, `Alert` from `window.VartiDesignSystem_07c3de`

## Notes

- Sidebar is collapsible (click the hamburger in the top bar)
- All data is fictional/static — no API calls
- The `Income` item in the sidebar has child navigation to demonstrate nested expand/collapse
