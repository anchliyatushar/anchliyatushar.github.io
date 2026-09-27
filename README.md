# Disha — Jewellery CAD Portfolio

Static Astro portfolio for jewellery CAD designer **Disha Jain**. It presents supplied CAD work as an object-led editorial archive, with a responsive interactive React CAD viewport and scroll-linked project studies.

## Design system

The visual direction takes high-level cues from contemporary bridal editorials - premium restraint, a strong jewellery focus and visual storytelling - without copying a campaign or its imagery.

| Layer | System choice |
| --- | --- |
| Base | Near-black ink (`--bg`) and low-contrast elevated surfaces retain focus on the work. |
| Object colour | Warm gold (`--gold`) is reserved for jewellery, high-priority actions and progress cues. |
| Technical layer | Ice-blue (`--blue-pale`) appears only in CAD grids, measurement lines and viewport states. |
| Type | Syne provides modern display structure; a restrained system serif adds editorial contrast; mono labels carry technical metadata. |
| Layout | A wide responsive container, structural hairlines and 4-up process cards keep the page precise rather than decorative. |
| Motion | Pointer parallax rotates the CAD ring viewport. Sticky project stages use scroll progress to move the render and narrative together. Motion respects `prefers-reduced-motion`. |

## Stack

- Astro for static routing, content collections and image optimisation.
- React for the interactive CAD viewport (`src/components/CadViewport.tsx`).
- Tailwind CSS 4 through its Vite plugin for utility styling inside React components.
- Existing CSS tokens and Astro component styles remain the source of truth for the editorial system.

The portfolio uses original supplied jewellery CAD images. The editorial model-wearer concept is intentionally kept as a future original-content addition; do not reuse images from a reference campaign without licence.

## Quick start

```bash
npm install
npm run dev
```

Open the local URL printed in the terminal (usually `http://localhost:4321`).

## Scripts

| Command             | Description                  |
| ------------------- | ---------------------------- |
| `npm run dev`       | Start local dev server       |
| `npm run build`     | Build static site to `dist/` |
| `npm run preview`   | Preview the production build |

## Content

Projects live in [`src/content/projects/`](src/content/projects/). Schema is in [`src/content.config.ts`](src/content.config.ts).

Frontmatter includes: `title`, `year`, `category` (`bridal` | `necklace` | `earrings` | `rings` | `sets`), `metal`, `stones`, `weight`, `cover`, `gallery`, `video`, `tools`, process fields, `orientation`.

To add a project:

1. Drop original CAD renders into `src/assets/cad/` (or editorial images into `src/assets/projects/`)
2. Add a `.md` file under `src/content/projects/`
3. Optionally add an MP4 under `public/videos/` and set `video: /videos/your-file.mp4`

[`public/resume.pdf`](public/resume.pdf) is the supplied Disha Jain resume. Update any personal contact details if they change.

## Deploy

Outputs a static `dist/` folder.

- **Netlify:** build `npm run build`, publish `dist`
- **Vercel:** Astro preset or build `npm run build`, output `dist`
- **GitHub Pages:** publish `dist` (set `site` in `astro.config.mjs`)

Update `site` in [`astro.config.mjs`](astro.config.mjs) to your real domain before go-live.
