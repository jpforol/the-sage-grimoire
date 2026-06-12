// @ts-check
import { defineConfig } from 'astro/config';

// GitHub Pages subpath deploy: every internal link must respect `base`.
// Use the `url()` helper from src/utils/url.ts — never hardcode root-relative paths.
export default defineConfig({
  site: 'https://jpforol.github.io',
  base: '/the-sage-grimoire',
});
