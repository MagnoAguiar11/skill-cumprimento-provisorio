# Cumprimento provisório de tutela e astreintes: skill para o Claude

Skill para o Claude (Claude Code ou Claude.ai). Ela lê o processo completo e redige a petição de **cumprimento provisório** de decisões de tutela provisória (liminar, tutela de urgência, sentença que confirma a tutela) e de **astreintes**, no CPC/2015.

## O que ela faz

- Lê o PDF do processo com o [MarkItDown](https://github.com/microsoft/markitdown) e monta o mapa de documentos (ID, páginas, quem assinou, data). Também aponta as páginas escaneadas, que precisam ser lidas como imagem.
- Anota o **ID** de cada documento que usa.
- Confere as datas de citação e intimação da decisão exequenda e se houve **intimação pessoal** (Súmula 410/STJ). Para pessoa jurídica, mostra que a intimação pessoal é feita pelo **Domicílio Judicial Eletrônico** e deixa isso explícito na petição.
- Distingue o Domicílio Judicial Eletrônico (pessoal) da publicação no DJEN (não pessoal).
- Conta o prazo para cumprir e os dias de descumprimento com uma calculadora própria. A contagem é conservadora, com feriados nacionais e recesso.
- Aplica o **teto** fixado na decisão. Sem teto e com multa desproporcional, limita ao **valor da obrigação principal** (valor da causa ou valor pago no contrato), pela proporcionalidade.
- Trata da **caução**: depósito em conta judicial até o trânsito em julgado (art. 537, § 3º), caução só para levantamento (art. 520, IV), dispensa por gratuidade ou súmula (art. 521).
- Lista, com ID, os pedidos coercitivos que o credor já fez, para afastar a tese de que ele deixou a multa crescer.
- Transcreve *ipsis litteris* cada dispositivo na primeira citação. O texto vem da base conferida no Planalto e no CNJ.
- Fundamenta só com **jurisprudência real e conferida** do STJ e do TJCE, com link. Ela não inventa julgado.
- Traz uma tabela simples de valores.
- Entrega tudo numa pasta da Mesa (`Cumprimento Provisórios - HRH/[cliente]`): a petição em Word na folha timbrada do escritório, a procuração sozinha, os demais documentos num só PDF com marcadores (abrindo com o demonstrativo de cálculo, com a logo) e o print da aba Expedientes com o expediente de cada executada destacado.

Antes de redigir, a skill mostra um diagnóstico e espera a autorização do advogado.

## Instalação

### Claude Code

```bash
git clone https://github.com/MagnoAguiar11/skill-cumprimento-provisorio.git
cp -R skill-cumprimento-provisorio/cumprimento-provisorio ~/.claude/skills/
```

Depois, abra uma sessão nova, anexe o PDF do processo e peça, por exemplo: "faça o cumprimento provisório da multa deste processo".

### Claude.ai

Compacte a pasta `cumprimento-provisorio` em .zip e envie na área de Skills das configurações.

## Requisitos

- Python 3.9 ou mais novo, sem bibliotecas extras. Teste a calculadora:

  ```bash
  python3 cumprimento-provisorio/scripts/astreintes.py --teste
  ```

- Para ler o processo: [MarkItDown](https://github.com/microsoft/markitdown) 0.1.9 (Microsoft, licença MIT). Basta ter o [uv](https://docs.astral.sh/uv/) instalado: o `scripts/ler_processo.py` roda o MarkItDown pelo `uv`, sem instalação permanente, uma página por vez (inteiro, ele junta as páginas de PDFs com tabela, como os do PJe). Sem o uv, usa o `markitdown` instalado (`pip install 'markitdown[pdf]'`, Python 3.10+), mas as páginas podem vir juntas. Sem nenhum dos dois, a skill usa `pdftotext` (poppler) ou, no Mac, o PDFKit (`scripts/pdf_texto.swift`). Teste: `python3 cumprimento-provisorio/scripts/ler_processo.py --teste`.
- O Word (`scripts/gerar_docx.py`, python-docx) e os PDFs (`scripts/montar_kit.py`, pypdf) saem pelo uv. O demonstrativo em PDF usa o Google Chrome (ou Chromium/Edge). O destaque da aba Expedientes usa o Vision do macOS (`scripts/ocr_linhas.swift`).
- Opcional: a extensão Claude in Chrome para pesquisar no JusBrasil.

## Estrutura

```
cumprimento-provisorio/
  SKILL.md                      fluxo de trabalho e regras
  references/dispositivos.md    texto literal da lei, conferido nas fontes oficiais
  references/precedentes.md     julgados do STJ e do TJCE conferidos, com link
  references/estrutura-da-peca.md  modelo da petição e tabela de valores
  scripts/ler_processo.py       leitura do processo com o MarkItDown e mapa de IDs
  scripts/astreintes.py         calculadora de prazos e valores
  scripts/correcao.py           demonstrativo de atualização com o índice oficial (INCC-DI, IGP-M, IPCA, INPC)
  scripts/montar_kit.py         procuração sozinha e demais documentos num PDF com marcadores, na pasta do cliente
  scripts/gerar_docx.py         petição em Word na folha timbrada, com citações recuadas, links e tabelas
  scripts/demonstrativo_pdf.py  demonstrativo de cálculo em PDF com a logo
  scripts/destacar_expediente.py  destaca o expediente nos prints da aba Expedientes (com ocr_linhas.swift)
  assets/folha-modelo.docx      folha timbrada do escritório; assets/logo.png: logo para o demonstrativo
  scripts/conferir_citacoes.py  confere cada citação literal contra a lei, o processo e os julgados
  scripts/pdf_texto.swift       no Mac: texto do PDF e páginas escaneadas em imagem
```

## Aviso

Esta é uma ferramenta de apoio. A peça deve ser revisada e assinada por advogado. A lei foi conferida em 19/11/2026 e os julgados novos em 20/11/2026: confira a vigência antes de protocolar. Reabra os julgados antes de citar, porque links e entendimentos mudam.
