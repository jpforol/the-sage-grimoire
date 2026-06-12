import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Executable form of specs/content-schema.md — keep both in sync.
const codex = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/codex' }),
  schema: z
    .object({
      title: z.string().min(1),
      category: z.enum([
        'criacao-de-personagens',
        'regras',
        'equipamentos',
        'magias',
        'tradicoes',
        'ancestralidades',
        'trilhas',
      ]),
      subcategory: z
        .enum(['novato', 'ancestralidade', 'especialista', 'mestre'])
        .optional(),
      summary: z.string().min(1),
      tags: z.array(z.string()).default([]),
      stats: z.record(z.union([z.string(), z.number(), z.boolean()])).default({}),
      source: z
        .object({
          book: z.enum(['livro-basico', 'ancestralidades']),
          page: z.number().int().positive(),
        })
        .optional(),
      draft: z.boolean().default(false),
    })
    .strict()
    .refine((data) => data.category === 'trilhas' || data.subcategory === undefined, {
      message: 'subcategory só é permitida na categoria trilhas',
    })
    .refine((data) => data.category !== 'trilhas' || data.subcategory !== undefined, {
      message: 'entradas de trilhas exigem subcategory',
    }),
});

export const collections = { codex };
