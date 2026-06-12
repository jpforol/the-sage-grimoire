# O Grimório do Sábio 📖

Codex estático do nosso sistema de RPG — classes, magias, itens e regras, com busca
instantânea. Feito para a mesa, hospedado de graça no GitHub Pages.

**Site:** https://jpforol.github.io/the-sage-grimoire/

## Rodar localmente

```sh
npm install
npm run dev        # http://localhost:4321/the-sage-grimoire/
```

A busca só funciona no site buildado: `npm run build && npm run preview`.

## Adicionar conteúdo

```sh
python tools/new_entry.py magias "Nome da Magia" --tags fogo,evocação
python tools/validate_entries.py src/content/codex/
```

Push para `main` publica automaticamente. Para ingerir um livro PDF, siga
`workflows/ingest-pdf.md`.

---

Projeto pessoal, sem fins comerciais.
