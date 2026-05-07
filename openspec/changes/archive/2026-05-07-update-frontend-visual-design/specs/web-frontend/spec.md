## ADDED Requirements

### Requirement: Visual design system

The Web frontend SHALL present a cohesive visual system across Naive UI and Tailwind/shadcn surfaces: shared typography, a single accent hue with cool-neutral grays, consistent spacing rhythm, and motion on interactive controls without relying on `window.alert` for validation feedback.

#### Scenario: Typography and readability

- **WHEN** a user views any authenticated or public Vue route
- **THEN** body text uses the same primary font family as Tailwind `font-sans` (no competing default such as Inter alongside Geist)
- **AND** full-viewport shells use `min-height: 100dvh` (or equivalent) instead of `100vh` alone for the root layout where full height is required
- **AND** primary numeric tables or scores MAY use tabular figures (`font-variant-numeric: tabular-nums`) where alignment improves scanability

#### Scenario: Color and surfaces

- **WHEN** the user uses light or dark appearance (including Naive-derived surfaces)
- **THEN** neutral backgrounds and borders belong to one cool-tinted gray family
- **AND** a single accent hue is used for primary actions and key highlights (sidebars SHALL not use a separate high-chroma purple unrelated to that accent)
- **AND** optional subtle grain or noise on the page background MUST NOT intercept pointer events

#### Scenario: Layout rhythm

- **WHEN** the user views the main authenticated layout
- **THEN** main content is constrained with a maximum width and horizontal padding so text and tables do not touch wide-monitor edges
- **AND** vertical spacing between header, alerts, and content follows a clear rhythm (optical asymmetry allowed if documented in implementation notes)

#### Scenario: Interaction and accessibility

- **WHEN** the user navigates with a pointer or keyboard
- **THEN** primary buttons and sidebar navigation items show visible hover, active, and focus-visible affordances within roughly 200–300ms transitions
- **AND** in-page anchor navigation uses smooth scrolling where applicable
- **AND** a skip link is available at the start of the main layout to move focus to the primary content landmark

#### Scenario: Meta and branding

- **WHEN** the app is loaded from `index.html`
- **THEN** the document has a non-empty `meta name="description"`
- **AND** Open Graph `og:title` and `og:description` reflect the product
- **AND** the favicon is not the default Vite logo; it represents Prof-Finder with a simple branded mark
