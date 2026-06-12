// Category registry — adding a category: update specs/content-schema.md first,
// then this file, src/content.config.ts and tools/validate_entries.py.
export type CategoryId =
  | 'criacao-de-personagens'
  | 'regras'
  | 'equipamentos'
  | 'magias'
  | 'tradicoes'
  | 'ancestralidades'
  | 'trilhas';

export type SubcategoryId = 'novato' | 'ancestralidade' | 'especialista' | 'mestre';

export interface SubcategoryDef {
  id: SubcategoryId;
  label: string;
  description: string;
}

export interface CategoryDef {
  id: CategoryId;
  label: string;
  icon: string;
  description: string;
  /** Markdown-free intro shown on the listing page, above the entries. */
  intro?: string;
  /** When set, the listing page groups entries by these subcategories. */
  subcategories?: SubcategoryDef[];
  /** When set, the listing page groups entries by this stats key (e.g. tradição). */
  groupByStat?: string;
}

export const CATEGORIES: CategoryDef[] = [
  {
    id: 'criacao-de-personagens',
    label: 'Criação de Personagens',
    icon: '🪶',
    description: 'Guia prático para criar um personagem, passo a passo.',
  },
  {
    id: 'regras',
    label: 'Regras do Jogo',
    icon: '📜',
    description: 'As principais regras do jogo: testes, combate e tudo entre eles.',
  },
  {
    id: 'equipamentos',
    label: 'Equipamentos',
    icon: '⚔️',
    description: 'Armas, armaduras, ferramentas e os equipamentos básicos do jogo.',
  },
  {
    id: 'magias',
    label: 'Magias',
    icon: '✨',
    description: 'Todos os feitiços do sistema, organizados por tradição.',
    groupByStat: 'tradicao',
  },
  {
    id: 'tradicoes',
    label: 'Tradições',
    icon: '✦',
    description: 'As tradições mágicas e seus feitiços, separados por rank.',
  },
  {
    id: 'ancestralidades',
    label: 'Ancestralidades',
    icon: '🌿',
    description: 'As raças do jogo: de humanos a cambiões e além.',
  },
  {
    id: 'trilhas',
    label: 'Trilhas',
    icon: '🛤️',
    description: 'As classes do jogo, em quatro tipos: Novato, Ancestralidade, Especialista e Mestre.',
    intro:
      'As Trilhas de Novato e as Trilhas de Ancestralidade compartilham os mesmos níveis — ' +
      'o jogador escolhe qual seguir. Exceção: a ancestralidade Humana só pode escolher ' +
      'entre as Trilhas de Novato.',
    subcategories: [
      {
        id: 'novato',
        label: 'Trilhas de Novato',
        description: 'Os quatro caminhos iniciais, abertos a todos os personagens.',
      },
      {
        id: 'ancestralidade',
        label: 'Trilhas de Ancestralidade',
        description:
          'Alternativas às trilhas de novato, ligadas à ancestralidade do personagem (exceto Humana).',
      },
      {
        id: 'especialista',
        label: 'Trilhas de Especialista',
        description: 'Especializações escolhidas nos níveis intermediários.',
      },
      {
        id: 'mestre',
        label: 'Trilhas de Mestre',
        description: 'O ápice de poder, escolhido nos níveis finais.',
      },
    ],
  },
];

export function getCategory(id: string): CategoryDef | undefined {
  return CATEGORIES.find((c) => c.id === id);
}
