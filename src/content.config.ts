import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const projects = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projects' }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      year: z.number(),
      category: z.enum(['bridal', 'necklace', 'earrings', 'rings', 'sets', 'brooches', 'bracelet', 'bangle', 'kada']),
      tags: z.array(z.string()),
      cover: image(),
      editorial: image(),
      video: z.string().optional(),
      gallery: z.array(image()),
      summary: z.string(),
      metal: z.string(),
      stones: z.string(),
      tools: z.array(z.string()),
      featured: z.boolean().default(false),
      problem: z.string(),
      approach: z.string(),
      outcome: z.string(),
      orientation: z.enum(['portrait', 'landscape']).default('portrait'),
    }),
});

export const collections = { projects };
