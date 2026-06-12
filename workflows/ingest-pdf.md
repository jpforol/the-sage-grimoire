# Workflow: Ingerir um PDF no Codex

SOP para transformar um livro-fonte em entradas publicadas. Implementa
`specs/pdf-extraction-pipeline.md` + `specs/content-schema.md`.

## Pré-requisitos

- PDF do livro em `sources/<book>.pdf` (a pasta é gitignored — o PDF nunca é commitado).
- Ambiente Python: `pip install -r tools/requirements.txt`.

## Passos

1. **Extrair** (determinístico — tool):

   ```
   python tools/extract_pdf.py sources/<book>.pdf --out .tmp/extracted/<book>/
   ```

2. **Revisar o manifesto** (humano): abra `.tmp/extracted/<book>/manifest.json` e
   confira as `suspect_pages` (tabelas, arte, colunas ambíguas). Corrija o texto
   dessas páginas à mão nos `page-NNN.txt` se necessário.

3. **Estruturar** (IA-assistido — camada de raciocínio): ler o texto extraído em
   blocos e emitir arquivos de entrada em `src/content/codex/<categoria>/<slug>.md`
   seguindo `specs/content-schema.md`. Regras:
   - Use as entradas existentes como referência de formato e tom.
   - Preencha `source.book` (slug do PDF) e `source.page` em TODA entrada derivada
     do livro — é a rastreabilidade de volta à fonte.
   - Slug: ASCII sem acentos, minúsculo, hifens (`tools/new_entry.py` gera certo).
   - Conteúdo que não couber nas categorias atuais: atualizar PRIMEIRO o enum em
     `specs/content-schema.md`, depois `src/data/categories.ts`,
     `src/content.config.ts` e `tools/validate_entries.py`.

4. **Validar** (determinístico — tool, obrigatório antes de commitar):

   ```
   python tools/validate_entries.py src/content/codex/
   ```

5. **Conferir o site**: `npm run build && npm run preview` — abrir a categoria,
   algumas entradas e testar a busca (a busca só funciona após o build).

6. **Publicar**: commit + push para `main` → GitHub Actions valida, builda e
   publica no GitHub Pages automaticamente.

## Lições aprendidas

_(Registrar aqui edge cases encontrados ao ingerir os livros reais — e refletir
nos specs.)_
