# Frontend Design Ecosystem 2026

Use this file when upgrading the skill, choosing a frontend design workflow, or deciding which external skill ideas are worth absorbing.

## Skills Ecosystem Signals

Search run with `npx skills find` on 2026-06-10:

| Query | Skill | Installs | Signal |
|---|---:|---:|---|
| `frontend design` | `smithery.ai@frontend-design` | 4.5K | High install signal, but `npx skills use` failed to clone on 2026-06-10; re-verify before depending on it. |
| `ui ux design` | `nexu-io/open-design@ui-ux-pro-max` | 1.9K | Useful discovery signal; current Open Design entry is catalog-only and points upstream. |
| `frontend design` | `ulpi-io/skills@frontend-design-ui-ux` | 399 | Secondary community signal. |
| `frontend design` | `rand/cc-polymath@discover-frontend` | 111 | Low-to-mid signal; inspect before using. |

Already absorbed high-value patterns in this Light skill:

- Anthropic `frontend-design`: clear creative direction, purpose/tone/constraints/differentiation, avoid generic AI aesthetics.
- Vercel-style web design rules: accessibility, performance, UX states, responsive behavior, hover/focus/reduced-motion.
- UI/UX Pro Max idea: map brief to industry/style/tokens/components/checklist; do not claim upstream library search is active unless its assets/scripts are installed.
- Taste/anti-slop skills: variance/motion/density knobs, redesign audit, image-to-code workflow, mechanical tells.
- shadcn/Tailwind/Next best practices: source-owned components, CSS variables, Server Components, route/data/security boundaries.

## Current Version Snapshot

Npm checks run on 2026-06-10:

| Package | Version |
|---|---:|
| `next` | 16.2.9 |
| `react` | 19.2.7 |
| `tailwindcss` | 4.3.0 |
| `shadcn` | 4.11.0 |
| `motion` | 12.40.0 |
| `gsap` | 3.15.0 |
| `lucide-react` | 1.17.0 |
| `@radix-ui/react-slot` | 1.2.5 |
| `vite` | 8.0.16 |
| `@vitejs/plugin-react` | 6.0.2 |

Re-check before installation:

```powershell
npm view next version
npm view react version
npm view tailwindcss version
npm view shadcn version
npm view motion version
npm view gsap version
npm view lucide-react version
npm view @radix-ui/react-slot version
npm view vite version
npm view @vitejs/plugin-react version
```

## Modern Stack Bias

For product-quality web apps:

1. Next.js App Router when routing, server data, SEO, auth, forms, and deployment discipline matter.
2. Vite + React when the app is a contained tool, dashboard, game, prototype, or static artifact.
3. Tailwind v4 with CSS variables/tokens when custom styling speed matters.
4. shadcn/ui when you want accessible Radix-based component source that the project owns.
5. Motion or GSAP only when motion communicates hierarchy or interaction; respect `prefers-reduced-motion`.

For Mini Program UI:

1. This Light research skill pack does not include a separate `light-miniprogram` skill; treat Mini Program work here as UI/visual guidance only.
2. Ask the user or project docs for runtime, platform, AppID, release, and API constraints before making non-UI Mini Program decisions.
3. Use this skill for tokens, information hierarchy, empty/loading/error states, mobile ergonomics, and visual polish.
4. Pick one Mini Program component system: native/WeUI, TDesign, Vant, Ant Design Mini, NutUI Taro, or custom.
