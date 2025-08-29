# Technical Specification: Proof of Putt Design System

**Version:** 1.0
**Date:** 2025-08-19
**Author:** Gemini Code Assist
**Status:** Initial Draft

---

## 1. Introduction

This document outlines the comprehensive design system and user interface (UI) guidelines for the "Proof of Putt" web application. Its purpose is to establish a consistent, high-quality, and intuitive user experience (UX) across all pages and components. This specification will serve as the single source of truth for all visual elements, from atomic components like buttons and colors to complex layouts and tables.

## 2. Core Design Philosophy

The application's aesthetic is a "Masters-inspired dark theme," which combines deep greens and a sandy off-white with a vibrant yellow accent. The core principles are:

- **Clarity:** Information should be presented clearly and without ambiguity. Visual hierarchy must guide the user's attention to the most important elements.
- **Consistency:** Components and layouts should look and behave predictably across the entire application. A user should not have to learn new interaction patterns for different pages.
- **Responsiveness:** The application must be fully usable and aesthetically pleasing on all screen sizes, from mobile phones to large desktop monitors.

---

## 3. Foundational Elements

### 3.1. Color Palette

The color palette is defined in `src/App.css` using CSS variables. All new components must use these variables to ensure theme consistency.

| Variable Name               | Hex/HSL Value             | Usage Description                                         |
| --------------------------- | ------------------------- | --------------------------------------------------------- |
| `--masters-green-dark`      | `hsl(137, 92%, 10%)`      | Main application background (`--background-color`).       |
| `--masters-green-medium`    | `hsl(105, 100%, 18%)`   | Primary surface color for cards, tables (`--surface-color`). |
| `--masters-green-light`     | `#188400`                 | Borders and subtle highlights (`--border-color`).         |
| `--highlighter-yellow`      | `#d3ce34`                 | Primary accent for buttons, stats (`--primary-color`).     |
| `--highlighter-yellow-hover`| `#d58114`                 | Hover state for primary accents.                          |
| `--sand-color`              | `#f0e6d6`                 | Background for light-themed elements like dropdowns.      |
| `--sand-color-hover`        | `#e1d5c3`                 | Hover state for sand-colored elements.                    |
| `--text-white`              | `#ffffff`                 | Primary text color (`--text-color`).                      |
| `--text-white-secondary`    | `#ffffff`                 | Secondary text, slightly lower emphasis.                  |
| `--error-color`             | `#f44336`                 | Error messages and destructive actions.                   |

### 3.2. Typography

- **Font Family:** The primary font is `var(--font-family)`, a system font stack for optimal performance and native feel.
- **Base Size:** The base font size should be `16px` (`1rem`).
- **Hierarchy:**
  - **`h1`:** Page titles. Font size: `2rem`, `font-weight: 600`. Color: `var(--text-color)`.
  - **`h2`:** Section titles (e.g., "Fundraising Campaigns"). Font size: `1.5rem`, `font-weight: 600`.
  - **`h3`:** Card and sub-section titles. Font size: `1.2rem`, `font-weight: 600`. Color: `var(--text-color-secondary)`.
  - **`h4`:** Smaller card headers (e.g., stat cards). Font size: `1rem`, `font-weight: 500`.
  - **Body Text (`p`, `td`, etc.):** `1rem` for primary content. `0.85rem` - `0.9rem` for secondary or dense information.

### 3.3. Layout & Spacing

- **Containers:**
  - `.container`: Max-width of `1200px`, centered with auto margins. Used for most content pages.
  - `.container-fluid`: Full-width container, primarily for layouts like the Coach page that need to span the viewport.
- **Spacing Unit:** A base unit of `1rem` (16px) should be used for margins and padding to maintain a consistent rhythm. Multiples of `0.25rem` (4px) are encouraged (e.g., `0.5rem`, `1rem`, `1.5rem`, `2rem`).

---

## 4. Component Design

This section details the design and implementation of reusable components.

### 4.1. Buttons

Buttons are the primary interactive elements. Consistency is key.

- **Base (`.btn`):**
  - `background-color`: `var(--primary-color)`
  - `color`: `var(--masters-green-dark)`
  - `padding`: `0.75rem 1.5rem` (standard), `0.25rem` vertical padding for compact versions (e.g., in headers).
  - `border-radius`: `8px`
  - `font-weight`: `bold`
  - `text-transform`: `uppercase`
  - `transition`: `background-color 0.2s ease`
- **Hover State (`:hover`):**
  - `background-color`: `var(--primary-color-hover)`
- **Active State (`.active`):**
  - Used for `NavLink` to indicate the current page.
  - `background-color`: `var(--primary-color-hover)`
  - `box-shadow`: `inset 0 2px 4px rgba(0,0,0,0.2)`
- **Secondary (`.btn-secondary`):** For less prominent actions.
  - `background-color`: `var(--masters-green-light)`
  - `color`: `var(--text-color)`
- **Tertiary (`.btn-tertiary`):** For actions like "Decline" or "Cancel".
  - `background-color`: `transparent`
  - `border`: `1px solid var(--border-color)`
  - `color`: `var(--text-color)`
- **Danger (`.btn-danger`):** For destructive actions like "Delete".
  - `background-color`: `var(--error-color)`
  - `color`: `var(--text-white)`
- **Icon Button (`.icon-button`):** Used for the profile dropdown.
  - Fixed `width` and `height` (`40px`).
  - Centered SVG icon.

### 4.2. Cards (`.card`)

Cards are used to group related information (e.g., `LeagueCard`, `StatCard`).

- **Base Style:**
  - `background-color`: `var(--surface-color)`
  - `border`: `1px solid var(--border-color)`
  - `border-radius`: `12px`
  - `padding`: `1.5rem`
- **Structure:**
  - **Card Header (`.league-card-header`):** Contains the title (`h3`) and any badges, uses flexbox for alignment.
  - **Card Body/Description:** Main content area.
  - **Card Footer (`.league-card-footer`):** Contains actions or summary info, uses flexbox for alignment.

### 4.3. Tables

#### Standard Table (`.duels-table`, `.session-table`, etc.)
- **Container:** Tables should be wrapped in a container (e.g., `.duels-table-container`) with a `background-color` of `var(--surface-color)` and `border-radius` of `12px`.
- **Styling:**
  - `width`: `100%`
  - `border-collapse`: `collapse`
  - `th`, `td`: `padding: 0.75rem 1rem`, `text-align: left`, `border-bottom: 1px solid var(--border-color)`.
  - `thead th`: `color: var(--text-color-secondary)`, `text-transform: uppercase`, `font-size: 0.85rem`.
  - `tbody tr:hover`: `background-color: var(--masters-green-light)`.

#### Pivot Table (`.league-pivot-table`)
- **Unique Feature:** This table uses rotated headers for player names to conserve horizontal space.
- **Implementation:**
  - The player name cell (`.player-name`) has a `position: relative`.
  - The inner `div` is absolutely positioned and transformed: `transform: translateX(-50%) rotate(-90deg)`.
  - `transform-origin` is set to `bottom center` to ensure correct rotation.
  - `padding-bottom` on the cell creates the necessary vertical space for the rotated text.
- **Styling:** Uses a `var(--sand-color)` background with `var(--masters-green-dark)` text for high contrast.

### 4.4. Navigation & Header

- **Header (`.app-header`):**
  - `background-color`: `var(--surface-color)`
  - `padding`: `0.5rem 2rem`
  - `display: flex`, `justify-content: space-between`, `align-items: center`
- **Logo (`.logo-img`):**
  - `height`: `68px`. The size is intentionally larger to establish a strong brand presence.
- **Profile Dropdown (`.profile-dropdown`):**
  - **Container:** `position: relative`.
  - **Menu (`.dropdown-menu`):** `position: absolute`, `right: 0`. Uses `var(--sand-color)` for the background.
  - **Items (`.dropdown-item`):** Text color is `var(--masters-green-dark)`.
  - **Unread Indicator (`.unread`):** The "Notifications" link should have a class of `.unread` when new notifications exist, which sets the `color` to a strong red (`#c00`) and `font-weight` to `bold`.

### 4.5. Charts (Recharts)

Charts are used on the `FundraiserDetailPage` and should follow a consistent theme.

- **Container:** Charts should be wrapped in a `.card` for consistent padding and background.
- **Colors:**
  - `Line (stroke)`: Use a vibrant, distinct color. `#8884d8` is currently used; this should be aliased to a CSS variable like `--chart-line-color-1`.
  - `CartesianGrid (stroke)`: Use a subtle, low-opacity version of the border color. `strokeDasharray="3 3"` provides a pleasant dashed appearance.
- **Labels & Axes:**
  - `XAxis`, `YAxis`: Labels should be clear and descriptive.
  - `Tooltip`: Should be styled to match the application's dark theme. The default style is often too bright.

---

## 5. Page-Specific Designs

### 5.1. Fundraising Page (`FundraisingPage.jsx`)

- **Layout:** A two-row table structure per campaign. The first row contains primary data, and the second, full-width row contains the progress bar.
- **Styling:**
  - Campaign Name (`.fundraiser-name`): `font-size: 1.2rem`, `font-weight: bold`, `color: var(--highlighter-yellow)`.
  - Cause (`.fundraiser-cause`): `font-size: 0.85rem`, `color: var(--highlighter-yellow)`.
  - Progress Bar (`.progress-bar-container`): The container holds the bar and the text label (`Progress: $X / $Y`). The fill color should be `var(--primary-color)`.

### 5.2. Fundraiser Detail Page (`FundraiserDetailPage.jsx`)

- **Layout:** A two-column flexible layout.
  - **Left Panel (`.fundraiser-detail-header`):** Contains the main description. Uses a distinct sandy background (`#fdf5e6`) with dark green text for readability.
  - **Right Panel (`.fundraiser-stats-grid`):** A 2x2 grid of `.stat-card` components for key metrics.
- **Below-Fold:** The layout uses a `.fundraiser-columns` grid to display "Top Pledges" and "Putting Sessions" side-by-side. The `.chart-card` is set to `flex-basis: 100%` to ensure it takes up its own full-width row.

### 5.3. Leagues Page (`LeaguesPage.jsx`)

- **Layout:** A grid-based layout (`.leagues-grid`) of `.league-card` components.
- **Sections:** The page is clearly divided into "Pending Invitations," "My Leagues," and "Public Leagues" using `<h3>` section headers.
- **Invite Card:** The `InviteCard` is a distinct component with primary and tertiary action buttons for accepting or declining.

### 5.4. Coach Page (`CoachPage.jsx`)

- **Layout:** A two-pane layout (`.coach-page-layout`).
  - **Sidebar (`.conversation-sidebar`):** Lists past conversations. The selected item (`.selected`) has a primary color background.
  - **Chat Panel (`.chat-panel`):** The main interaction area. It has a lighter background (`--surface-color`) than the message bubbles (`--background-color`) for contrast.
- **Messages:** User messages are right-aligned with a primary color background. Bot messages are left-aligned.

---

## 6. Responsiveness

- **Strategy:** A mobile-first approach is recommended for future development. For existing components, media queries are used to adapt layouts.
- **Breakpoints:** The primary breakpoint is `(max-width: 768px)`.
- **Key Adaptations:**
  - **Grids (`.dashboard-grid`, `.leagues-grid`):** Should collapse from multiple columns to a two-column or single-column layout on smaller screens.
  - **Tables:** For wide tables like the league pivot table, `overflow-x: auto` on a wrapper (`.league-table-wrapper`) is essential to allow horizontal scrolling on mobile, preventing page distortion.
  - **Flex Layouts (`.fundraiser-detail-page`):** `flex-wrap: wrap` allows columns to stack vertically on smaller screens.

---

## 7. Action Items & Future Improvements

1.  **Centralize Theme Variables:** Consolidate all color, font, and spacing variables into a single `_theme.css` or `_variables.css` file and import it into `App.css`. This will make theme management easier.
2.  **Refactor Redundant CSS:** There are several duplicate style blocks (e.g., `.profile-dropdown` styles appear twice in `App.css`). These should be consolidated.
3.  **Component Abstraction:** Create more abstract, reusable components. For example, a generic `<Card>` component could replace the specific implementations in `LeaguesPage` and `Dashboard`.
4.  **Living Style Guide:** For long-term maintainability, implement a tool like **Storybook**. This would allow developers to view, test, and document each UI component in isolation, enforcing consistency and speeding up development.
5.  **Accessibility (A11y) Review:** Conduct a full accessibility audit. Ensure all interactive elements have proper focus states, all images have `alt` text, and ARIA attributes are used correctly (e.g., on the `ProgressBar`).