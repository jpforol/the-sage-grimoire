// Category registry — adding a category: update specs/content-schema.md first,
// then this file, src/content.config.ts and tools/validate_entries.py.
export type CategoryId = 'classes' | 'magias' | 'itens' | 'regras';

export interface CategoryDef {
  id: CategoryId;
  label: string;
  icon: string;
  description: string;
}

export const CATEGORIES: CategoryDef[] = [
  {
    id: 'classes',
    label: 'Classes',
    icon: '🛡️',
    description: 'As vocações e caminhos que definem cada herói.',
  },
  {
    id: 'magias',
    label: 'Magias',
    icon: '✨',
    description: 'Feitiços, rituais e poderes arcanos.',
  },
  {
    id: 'itens',
    label: 'Itens',
    icon: '⚔️',
    description: 'Armas, armaduras, poções e relíquias.',
  },
  {
    id: 'regras',
    label: 'Regras',
    icon: '📜',
    description: 'As leis que regem a mesa e o mundo.',
  },
];

export function getCategory(id: string): CategoryDef | undefined {
  return CATEGORIES.find((c) => c.id === id);
}
