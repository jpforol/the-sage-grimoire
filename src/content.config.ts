import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Executable form of specs/content-schema.md — keep both in sync.
const codex = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/codex' }),
  schema: z
    .object({
      title: z.string().min(1),
      category: z.enum(['classes', 'magias', 'itens', 'regras']),
      summary: z.string().min(1),
      tags: z.array(z.string()).default([]),
      stats: z.record(z.union([z.string(), z.number(), z.boolean()])).default({}),
      source: z
        .object({
          book: z.string().min(1),
          page: z.number().int().positive(),
        })
        .optional(),
      draft: z.boolean().default(false),
    })
    .strict(),
});

export const collections = { codex };
