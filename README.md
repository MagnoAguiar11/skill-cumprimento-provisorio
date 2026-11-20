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

## Instalação em um passo

Abra o Claude Code (no app do Claude, aba **Code**, ou no terminal com `claude`) e cole:

> Instale esta skill: https://github.com/MagnoAguiar11/skill-cumprimento-provisorio

O Claude lê as instruções abaixo, pede sua autorização e roda o instalador. Ele baixa a skill, coloca na pasta de skills do Claude, instala o uv (que cuida do Python e das bibliotecas) e testa tudo. Se o uv não instalar (rede que bloqueia o site dele, por exemplo), a skill monta um Python próprio com o python3 do computador e segue funcionando. Não pede senha de administrador. Para atualizar depois, cole o mesmo pedido.

### Instruções para o Claude Code

Quando o usuário pedir para instalar ou atualizar esta skill, rode o instalador do sistema dele, sem pedir que ele instale nada à mão:

- **Mac ou Linux** (terminal):

  ```bash
  curl -fsSL https://raw.githubusercontent.com/MagnoAguiar11/skill-cumprimento-provisorio/main/instalar.sh | bash
  ```

- **Windows** (PowerShell):

  ```powershell
  powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/MagnoAguiar11/skill-cumprimento-provisorio/main/instalar.ps1 | iex"
  ```

O instalador demora alguns minutos na primeira vez, lista os testes e termina com a linha `RESULTADO: OK` ou `RESULTADO: FALHOU`, seguida do motivo e do caminho do log (`~/.cache/skill-cumprimento-provisorio/instalacao.log`; no Windows, `%LOCALAPPDATA%\skill-cumprimento-provisorio\instalacao.log`). Com `RESULTADO: OK`, diga ao usuário para abrir uma **sessão nova** do Claude Code, anexar o PDF do processo baixado do PJe e os prints da aba Expedientes e pedir: "Faça o cumprimento provisório deste processo". Com `RESULTADO: FALHOU`, leia o log, corrija a causa e rode de novo. A falta do uv sozinha não é falha: o instalador segue sem ele.

Se não puder rodar o comando que baixa da internet (`curl ... | bash`), baixe o repositório (`git clone` ou o .zip) e rode o instalador de dentro dele: `bash instalar.sh` (no Windows, `powershell -ExecutionPolicy Bypass -File instalar.ps1`). Ele instala a partir da cópia local.

Depois de instalada, se algum script disser que o Python da skill não está pronto, rode `python3 ~/.claude/skills/cumprimento-provisorio/scripts/ambiente.py`: ele prepara e testa o ambiente sozinho (`--status` mostra o que está em uso).

Quem preferir pode rodar o mesmo comando direto no terminal, sem o Claude.

### Instalação manual

Sem o instalador: copie a pasta `cumprimento-provisorio` deste repositório para `~/.claude/skills/` (no Windows, `%USERPROFILE%\.claude\skills\`) e rode `python3 ~/.claude/skills/cumprimento-provisorio/scripts/ambiente.py`. O uv é opcional; se quiser instalá-lo, use o site https://docs.astral.sh/uv/ (no Windows, o instalador oficial no PowerShell, e não o `winget`, que pode travar pedindo permissão para instalar o Visual C++). A pasta `Cumprimento Provisórios - HRH` é criada na Área de Trabalho (com o OneDrive ligado, na Área de Trabalho do OneDrive).

### Claude.ai

Compacte a pasta `cumprimento-provisorio` em .zip e envie na área de Skills das configurações.

## Requisitos

- Python 3.9 ou mais novo, sem bibliotecas extras. Teste a calculadora:

  ```bash
  python3 cumprimento-provisorio/scripts/astreintes.py --teste
  ```

- As bibliotecas (MarkItDown, pypdf, pypdfium2, Pillow e python-docx, em versões fixadas) ficam por conta do `scripts/ambiente.py`. Ele usa o [uv](https://docs.astral.sh/uv/), que traz o Python 3.12, mesmo que o uv não esteja no PATH do terminal. Sem uv, ou se o uv não conseguir baixar o Python, ele cria um Python próprio da skill (`~/.cache/skill-cumprimento-provisorio/venv`; no Windows, em `%LOCALAPPDATA%`) com o Python do computador e instala as bibliotecas do PyPI na primeira vez. Nada pede senha de administrador.
- Para ler o processo: [MarkItDown](https://github.com/microsoft/markitdown) 0.1.9 (Microsoft, licença MIT), uma página por vez (inteiro, ele junta as páginas de PDFs com tabela, como os do PJe). O MarkItDown pede Python 3.10+; no Python 3.9 do Mac sem uv, o texto sai do pypdfium2, com o mesmo mapa de IDs. Teste: `python3 cumprimento-provisorio/scripts/ler_processo.py --teste`.
- O Word (`scripts/gerar_docx.py`, python-docx) e os PDFs (`scripts/montar_kit.py`, pypdf) saem pelo mesmo ambiente. O demonstrativo em PDF usa o Google Chrome ou o Microsoft Edge (que já vem no Windows). O destaque da aba Expedientes lê o print com o OCR do próprio sistema: o Vision no Mac e o OCR do Windows no Windows 10/11 (no Linux, o RapidOCR). Se o MarkItDown não rodar (no Windows sem o Visual C++), a leitura do processo usa o pypdfium2 e avisa.
- Opcional: a extensão Claude in Chrome para pesquisar no JusBrasil.

## Estrutura

```
instalar.sh                     instalador para Mac e Linux
instalar.ps1                    instalador para Windows
cumprimento-provisorio/
  SKILL.md                      fluxo de trabalho e regras
  references/dispositivos.md    texto literal da lei, conferido nas fontes oficiais
  references/precedentes.md     julgados do STJ e do TJCE conferidos, com link
  references/estrutura-da-peca.md  modelo da petição e tabela de valores
  scripts/ambiente.py           acha o uv ou monta o Python próprio da skill, com as bibliotecas
  scripts/ler_processo.py       leitura do processo com o MarkItDown e mapa de IDs; páginas escaneadas em PNG
  scripts/astreintes.py         calculadora de prazos e valores
  scripts/correcao.py           demonstrativo de atualização com o índice oficial (INCC-DI, IGP-M, IPCA, INPC)
  scripts/montar_kit.py         procuração sozinha e demais documentos num PDF com marcadores, na pasta do cliente
  scripts/gerar_docx.py         petição em Word na folha timbrada, com citações recuadas, links e tabelas
  scripts/demonstrativo_pdf.py  demonstrativo de cálculo em PDF com a logo
  scripts/destacar_expediente.py  destaca o expediente nos prints da aba Expedientes (OCR: ocr_linhas.swift no Mac, ocr_linhas.ps1 no Windows)
  assets/folha-modelo.docx      folha timbrada do escritório; assets/logo.png: logo para o demonstrativo
  scripts/conferir_citacoes.py  confere cada citação literal contra a lei, o processo e os julgados
  scripts/pdf_texto.swift       no Mac: texto do PDF e páginas escaneadas em imagem
```

## Aviso

Esta é uma ferramenta de apoio. A peça deve ser revisada e assinada por advogado. A lei foi conferida em 19/11/2026 e os julgados novos em 20/11/2026: confira a vigência antes de protocolar. Reabra os julgados antes de citar, porque links e entendimentos mudam.
