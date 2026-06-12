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

## Lições aprendidas (ingestão SotWW, jun/2026)

- **Construa parsers, não estruture à mão.** Os dois livros renderam 4 parsers
  determinísticos (`parse_spells.py`, `parse_ancestries.py`, `parse_paths.py`,
  `build_sections.py`) que geraram ~870 das 887 entradas. Só 5 entradas foram
  escritas à mão (Humana + 4 trilhas de novato).
- **Âncoras confiáveis primeiro.** Headers de seção repetitivos (`CONJURAÇÕES:`,
  `X de Nível N`, `Traços de X`) são âncoras melhores que headings soltos. Para o
  início de seções, busque a ÚLTIMA ocorrência do nome antes da âncora — tabelas
  de índice mencionam os nomes antes das seções reais.
- **O livro tem inconsistências de nomenclatura**: Cósmica usa headers adjetivos
  ('Novato Cósmicos'); 'Combatente Arcano' tem um header impresso como 'Guerreiro
  Arcano'; 'Vanguarda' usa headers 'Vanguardista'. Resolvidas com mapas de alias
  nos parsers.
- **Furniture**: toda página tem a marca d'água `Licenciado para ...` (dado
  pessoal — NUNCA pode vazar para o site), fólio numérico, `Capítulo N` e
  running headers minúsculos (`criando um personagem`, `equipamento`, `Magia`).
  O fólio só pode ser removido por igualdade exata com o número da página —
  remover `\d+` genérico come células de tabela (dano '0').
- **Página do livro = página do arquivo − 1** em ambos os PDFs.
- **Tabelas em 2 colunas saem intercaladas** na extração; linhas de tabelas de
  rolagem (D20) precisam ser reordenadas pela chave numérica.
- **O flag de páginas suspeitas do extract_pdf.py é inútil nestes livros** (marca
  ~90% das páginas por serem 2 colunas) — calibrar na próxima revisão do spec.
