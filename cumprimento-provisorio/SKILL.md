---
name: cumprimento-provisorio
description: Lê o processo completo e redige a petição de cumprimento provisório de decisão de tutela provisória (liminar, tutela de urgência ou de evidência, sentença que confirma a tutela) e de astreintes, no CPC/2015. Confere as datas de citação e intimação e se houve intimação pessoal (Súmula 410/STJ; para empresas, pelo Domicílio Judicial Eletrônico). Conta os dias de descumprimento, aplica o teto ou o limite da obrigação principal e trata da caução e da gratuidade. Mostra, com ID, os pedidos coercitivos já feitos e fundamenta com lei transcrita e jurisprudência real do STJ e do TJCE, com link. Entrega, na pasta do cliente, a petição em Word timbrado, a procuração, os documentos num só PDF com o demonstrativo de cálculo e o print da aba Expedientes destacado. Use quando o advogado falar em cumprimento provisório, executar liminar ou tutela antecipada, multa diária, astreintes, descumprimento de decisão, bloqueio da multa, ou mandar um processo pedindo para cobrar a multa, mesmo sem dizer o nome da peça.
---

# Cumprimento provisório de tutela provisória e de astreintes

Esta skill transforma o processo completo numa petição de cumprimento provisório pronta para revisão. Ela trabalha em fases: primeiro **lê e calcula**, depois **mostra o diagnóstico e espera a autorização do advogado**, só então **pesquisa e redige**. A separação existe porque os erros aqui custam caro: cobrar astreintes sem intimação pessoal esbarra na Súmula 410/STJ; uma conta mal feita abre a porta para a impugnação; e deixar a multa correr sem nenhum pedido convida o juiz a reduzi-la.

## Regras que valem para a peça inteira

1. **ID sempre.** Toda menção a documento, petição, decisão, certidão, expediente ou comprovante leva o ID do PJe entre parênteses: "(ID 12345678)". No PDF baixado do PJe, o ID está no rodapé de cada página ("Num. 12345678 - Pág. 1") e no índice do início do arquivo. Fato sem ID (por exemplo, a data de ciência que só aparece na aba de expedientes) deve vir com a origem indicada, e o advogado é avisado para juntar a certidão ou o print.
2. **Lei só conferida.** Na primeira citação, o dispositivo é transcrito *ipsis litteris*, copiado de `references/dispositivos.md`. Nas citações seguintes, só o número ("art. 537, § 3º, do CPC"). Dispositivo citado só nos pedidos (multa e honorários dos arts. 520, § 2º, e 523, § 1º; SISBAJUD do art. 854) vai só pelo número, sem transcrição. Dispositivo fora do arquivo: abra a lei no Planalto, copie o texto vigente (o revogado aparece riscado), acrescente ao arquivo com a data e só então cite. Nunca de memória.
3. **Jurisprudência só real.** Só entra julgado aberto e conferido na fonte, com link. Dê preferência ao STJ e ao TJCE, com julgados concordantes com a tese do pedido. Nunca invente nem complete de memória número, relator, data ou ementa. Se não achar julgado para um ponto, diga isso ao advogado e sustente o ponto na lei.
4. **CPC estrito.** Cada raciocínio aponta o dispositivo que o sustenta, e antes de usá-lo leia o texto e confirme que ele diz aquilo. Exemplos de confusão a evitar: a caução do cumprimento provisório é a do art. 520, IV, e sua dispensa é a do art. 521; a do art. 300, § 1º, é outra coisa (concessão da tutela). Publicação no DJEN não é intimação pessoal; o canal da intimação pessoal da empresa é o Domicílio Judicial Eletrônico.
5. **Peça direta e concisa.** O advogado quer a petição sem rodeio: cada seção com o fato, o ID, o dispositivo e, no máximo, um ou dois julgados com trecho curto. Nada de "insta salientar", "mister se faz", repetição de argumento ou adjetivos sobre a parte contrária. Os fatos e as datas falam por si. Fique no que sustenta o pedido: não fale de embargos, recursos ou expedientes que não mudam a exigibilidade, a intimação ou o valor.
6. **Peça desconsiderada some.** Se o advogado mandar desconsiderar uma peça (desentranhada, protocolada por engano, refeita), ela sai da análise inteira: não serve de fato, de parâmetro, de conta nem de modelo, e não entra no kit. Faça os cálculos com os critérios desta skill.
7. **Sem majoração por conta própria.** Use só a multa que o juiz fixou. Não peça majoração e não reitere pedido de majoração que o juiz não decidiu, salvo se o advogado pedir.
8. **Limite pela proporcionalidade.** Sem teto na decisão, a peça diz que a exequente limita a multa ao valor da obrigação principal em respeito à razoabilidade e à proporcionalidade (art. 537, caput: "suficiente e compatível com a obrigação"), com o TJCE (ED 0640351-55.2022.8.06.0000) e o STJ (AgInt no AREsp 1.638.130/SP) de `precedentes.md`. A peça não diz que a multa vencida não pode ser reduzida: isso fica só no diagnóstico, para o advogado.

## Referências

- `references/dispositivos.md`: texto literal vigente do CPC, da Lei 11.419/2006, da Resolução CNJ 455/2022 e da Súmula 410, conferido nas fontes oficiais.
- `references/precedentes.md`: julgados do STJ e do TJCE já conferidos, com trecho literal e link, organizados por tema. É o ponto de partida da pesquisa, não o fim.
- `references/estrutura-da-peca.md`: modelo da petição, parágrafos-base, tabela de valores e pedidos.
- `scripts/ler_processo.py`: lê o PDF com o MarkItDown e monta o mapa de IDs (`--teste` faz a autoverificação).
- `scripts/pdf_texto.swift`: no Mac, texto do PDF e páginas escaneadas em imagem, sem instalar nada.
- `scripts/astreintes.py`: calculadora de ciência, prazo, dias de descumprimento e valor (rode `--teste` antes do primeiro uso; `--help` mostra as opções).
- `scripts/correcao.py`: demonstrativo de atualização no modelo do advogado, com o número-índice oficial (INCC-DI, IGP-M, IPCA ou INPC, do Ipeadata) e conferência do encadeamento com o SGS do Banco Central.
- `scripts/montar_kit.py`: recorta do PDF do processo, por ID, os documentos que instruem o cumprimento provisório; grava a procuração sozinha e junta o resto num PDF com marcadores.
- `scripts/gerar_docx.py`: transforma a petição em Markdown no Word (.docx) na folha timbrada (`assets/folha-modelo.docx`), com endereçamento em negrito, citações recuadas, link clicável abaixo de cada julgado e tabelas no padrão do escritório.
- `scripts/demonstrativo_pdf.py`: transforma o demonstrativo de cálculo em PDF com a logo (`assets/logo.png`), pelo Chrome.
- `scripts/destacar_expediente.py` (com `ocr_linhas.swift`): acha, nos prints da aba Expedientes, a linha de cada expediente e a destaca (fundo amarelo, borda vermelha e marca-texto na ciência). Só no Mac.
- `scripts/conferir_citacoes.py`: confere se cada trecho citado entre aspas existe, palavra por palavra, na lei, no processo ou no julgado.

## Fase 1: leitura do processo

**Leitura do PDF com o MarkItDown.** Sempre comece por aqui:

```bash
python3 scripts/ler_processo.py processo.pdf
```

O script roda o [MarkItDown](https://github.com/microsoft/markitdown) na versão fixada 0.1.9, pelo `uv`, sem instalação permanente. Ele manda **uma página por vez**, porque o MarkItDown junta todas as páginas quando o PDF tem alguma tabela ou formulário, e o índice do PJe tem. Sem `uv`, o script usa o `markitdown` instalado; nesse caso as páginas podem vir juntas, e o script avisa. O resultado é o `processo.md`, gravado ao lado do PDF, com:

- o **mapa de documentos**: ID do PJe, páginas do PDF, quem assinou, data e início do texto;
- a lista de **páginas sem texto** (escaneadas);
- o texto de cada página, já com o ID no título e sem o rodapé de assinatura.

Leia o mapa primeiro e use as buscas abaixo no `processo.md`.

- **Processo do e-SAJ** (sem ID): o título da página traz as folhas ("fls. 87"); cite "fls." no lugar de ID.
- **ID fora da sequência** (muito menor ou maior que os vizinhos, no meio de um anexo) costuma ser de documento de outro processo juntado como prova. Não o cite como peça deste processo.
- **O PDF do PJe não traz a aba "Expedientes".** As datas de envio e de ciência pelo Domicílio Judicial Eletrônico, e a indicação de que a decisão seguiu junto, ficam fora do PDF. Se a intimação pessoal depender delas, peça ao advogado o print ou a certidão dos expedientes. Não presuma a data a partir do que uma petição da parte afirma. A aba é paginada, com o mais recente primeiro; os expedientes da decisão exequenda costumam estar nas últimas páginas. Peça as linhas de cada executada logo após a decisão: tipo do ato (citação ou intimação), meio (Domicílio Judicial Eletrônico, Correios, Diário Eletrônico), data de envio e "ciência registrada em". O "ID do documento" do expediente é o do ato de comunicação, não o da decisão. Como ler o PJe:
  - "Expedição eletrônica" com o ícone do Domicílio significa que o ato foi pelo Domicílio Judicial Eletrônico.
  - "Usuário Domicílio Eletrônico registrou ciência em" é ciência expressa (consulta).
  - "O sistema registrou ciência em" é ciência tácita (fim dos 10 dias corridos). Também vale como intimação pessoal (Lei 11.419/2006, art. 5º, §§ 3º e 6º).
  - "Comunicação frustrada" quer dizer que não houve intimação.
  - A "data limite" do expediente serve para conferir a conta da calculadora.
- **Páginas escaneadas** (AR, certidões, comprovantes, prints) não têm texto. No Mac, transforme-as em imagem com `swift scripts/pdf_texto.swift processo.pdf --imagem 12,13 pasta` e leia os PNG. Em outros sistemas, leia essas páginas com a ferramenta de leitura de PDF. Nunca presuma o conteúdo de página que não leu: o AR assinado pelo devedor costuma estar justamente numa delas.
- **Sem MarkItDown e sem uv:** `pdftotext -layout`, ou, no Mac, `swift scripts/pdf_texto.swift processo.pdf > processo.txt`. Avise o advogado e monte o mapa de IDs à mão (documento, tipo, data e ID) antes de seguir.

**Buscas úteis no texto:** `Num. `, `Assinado eletronicamente`, `Domicílio Judicial`, `DJEN`, `Diário`, `expediente`, `ciência`, `Decorrido prazo`, `mandado`, `AR`, `intime-se`, `multa`, `astreinte`, `por dia`, `limitad`, `teto`, `até o limite`, `tutela`, `liminar`, `efeito suspensivo`, `agravo`, `apelação`, `trânsito`, `gratuidade`, `justiça gratuita`, `valor da causa`, `Súmula`, `Tema`, `descumpri`, `majora`, `bloqueio`, `SISBAJUD`.

Levante, sempre com ID e data:

1. **Decisão exequenda.** Tipo e data. Transcreva o comando: a obrigação, o prazo para cumprir (dias úteis, corridos ou horas), o valor e a periodicidade da multa, o teto e a quem a ordem se dirige.
2. **O que veio depois.** Decisões que majoraram, reduziram ou limitaram a multa, deram novo prazo ou revogaram a tutela; a sentença (que confirma, concede ou revoga a tutela, art. 1.012, § 1º, V); acórdãos.
3. **Recursos e efeito suspensivo.** Agravo de instrumento ou apelação com efeito suspensivo deferido (arts. 995, parágrafo único, 1.012, §§ 3º e 4º, e 1.019, I)? Se a parte executada estiver suspensa, pare e avise o advogado em primeiro lugar.
   - **Sentença que confirmou a tutela (ID)?** Para a cobrança da multa isso é decisivo. A Corte Especial do STJ mantém o Tema 743 no CPC/2015 (EAREsp 1.883.876/RS): a multa fixada em liminar só pode ser executada provisoriamente depois de confirmada por sentença de mérito, com recurso sem efeito suspensivo. Se só existe a liminar, avise logo no diagnóstico e leia o alerta 1 de `precedentes.md`.
4. **Intimação do devedor sobre a decisão exequenda.** Este é o ponto central. Com mais de uma executada, faça a análise para cada uma: uma pode ter intimação pessoal comprovada e a outra não. Registre:
   - o meio (Domicílio Judicial Eletrônico, mandado de oficial de justiça, carta com AR, sistema do PJe, DJEN);
   - o destinatário (a própria parte ou só o advogado);
   - a data do envio e a data da ciência (consulta), ou a ciência tácita após 10 dias corridos sem consulta; a data de juntada do mandado ou do AR; o ID da certidão ou do expediente.
   - **Classificação.** São pessoais: o Domicílio Judicial Eletrônico; o mandado cumprido na pessoa do devedor ou de quem o represente; o AR recebido pelo devedor; a citação que levou a decisão junto. **Não** são pessoais: a publicação no DJEN e a intimação em nome do advogado.
   - Para pessoa jurídica, a intimação pessoal se faz pelo Domicílio Judicial Eletrônico (art. 246, § 1º, do CPC; Lei 11.419/2006, art. 5º, § 6º; Resolução CNJ 455/2022, arts. 11, § 2º, e 18). Isso deve ficar **explícito** na petição.
5. **Cumprimento.** A obrigação foi cumprida? Quando? Qual documento prova o cumprimento ou o descumprimento (ID)?
6. **Pedidos do credor depois da decisão.** Liste cada manifestação do credor com ID, data, o que pediu e o que o juiz decidiu (ID): comunicação de descumprimento, pedido de majoração, de bloqueio, de nova intimação, de ofício, de medidas do art. 139, IV, ou do art. 536, § 1º. Isso afasta o argumento de que o credor ficou inerte e deixou a multa crescer. Marque também os períodos longos de silêncio do credor, que são risco.
7. **Gratuidade.** Deferida (ID da decisão), pendente ou indeferida?
8. **Valor da causa** (ID da inicial ou da decisão que o corrigiu) e **valor do contrato ou valor pago** (ID do documento).
9. **Súmula ou repetitivo** em que a decisão ou a ação se apoia (art. 521, IV): onde aparece (ID) e o texto conferido no site do STJ ou do STF.
10. **Outras hipóteses do art. 521:** crédito alimentar (I)? Agravo do art. 1.042 pendente (III)?
11. **Execução já existente.** Já há cumprimento provisório ou definitivo, depósito, pagamento ou bloqueio (ID)?
12. **Rito.** Se for Juizado Especial (Lei 9.099/1995), avise: há regras próprias, e esta skill foi escrita para o procedimento comum.
13. **Qualificação completa** (o cumprimento provisório é processo incidental novo). Exequente: nome como está no PJe, nacionalidade, estado civil, profissão, RG, CPF, e-mail e endereço (inicial e procuração). Executadas: razão social atual, CNPJ e o endereço mais recente que elas mesmas declararam (procuração ou petição delas) ou em que receberam AR, sempre com o ID. Se o nome da parte mudou entre a inicial e o PJe, use o do PJe e avise.

## Fase 2: cálculo e diagnóstico (antes de redigir)

Rode a calculadora (caminho relativo à pasta da skill):

```bash
python3 scripts/astreintes.py --envio-domicilio AAAA-MM-DD --prazo 5 --diaria 500 --teto 30000
python3 scripts/astreintes.py --ciencia AAAA-MM-DD --prazo 48h --diaria 1000 --referencia 25000 --cumprido-em AAAA-MM-DD
```

Regras da conta:

- **Ciência pelo Domicílio:** é a data da consulta (se caiu em dia não útil, vale o dia útil seguinte). Sem consulta, vale o fim dos 10 dias corridos contados do envio (Lei 11.419/2006, art. 5º, §§ 2º e 3º; Resolução CNJ 455/2022, art. 20).
- **Prazo para cumprir:** siga o que a decisão diz (úteis, corridos ou horas). Se ela for omissa, conte em dias úteis, como faz o STJ (REsp 1.778.885/DF e REsp 2.251.367/PR). A calculadora já conta assim e mostra numa nota quanto mudaria em dias corridos.
- **Dias de multa:** a calculadora soma dias corridos ("multa diária") e mostra numa nota o total se cada dia de multa contasse só em dia útil. O STJ ainda não deixou isso claro, então mostre as duas contas ao advogado.
- **Começo do prazo:** a data da comunicação (art. 231, § 3º), excluindo-se o dia do começo (art. 224).
- **Multa:** corre do dia seguinte ao vencimento (art. 537, § 4º) até a véspera do cumprimento ou até hoje. Majorações e reduções entram com `--mudanca`. Multa que não é diária (por ato, mensal ou fixa) é calculada à mão, com a conta mostrada.
- **Limite:** com teto na decisão, executa-se no máximo o teto. Sem teto, se o total passar do valor da obrigação principal, limita-se a esse valor: o valor da causa ou, quando a ação gira em torno de um contrato, o valor pago no contrato. Mostre os dois ao advogado; sem resposta, use o valor da causa. Avise também, só no diagnóstico (nunca na peça), que, pela Corte Especial (EAREsp 1.766.665/RS e 1.479.019/SP), a multa vencida não pode ser reduzida. Limitar, portanto, é escolha do escritório, e não exigência, e o ponto ainda será decidido nos Temas 1.442 e 1.448 do STJ.
- **Quando o total passa muito do limite**, a disputa sobre o termo inicial não muda o valor executado. Diga isso no diagnóstico, com o número mínimo de dias de descumprimento que basta para atingir o limite.
- **Feriados locais e dias sem expediente** do tribunal entram com `--feriados` (no Ceará, consulte o calendário do TJCE do ano).
- Os valores são nominais. A atualização monetária é decisão do advogado (art. 524, II a IV).

**Sem intimação pessoal, não há multa a cobrar agora** (Súmula 410). Nesse caso, a petição pede a intimação pessoal pelo Domicílio Judicial Eletrônico (pessoa jurídica) ou por mandado (pessoa física) para cumprir no prazo, sob pena da multa já fixada, além de medidas coercitivas e do cumprimento provisório do que mais for exigível. Diga isso em primeiro lugar no diagnóstico.

Apresente o diagnóstico no chat, curto e em blocos:

```
DECISÃO EXEQUENDA: [tipo] (ID) de dd/mm/aaaa: [obrigação]; multa R$ [x]/dia; teto [R$ x | sem teto]
EXEQUIBILIDADE: [nenhum recurso | recurso sem efeito suspensivo (ID) | ATENÇÃO: efeito suspensivo (ID)]
CONFIRMAÇÃO DA MULTA: [sentença de dd/mm confirmou a tutela (ID) | SÓ LIMINAR: Tema 743 e EAREsp 1.883.876/RS, risco alto; opções: esperar a sentença, ou protocolar enfrentando o precedente com os acórdãos do TJCE]
INTIMAÇÃO PESSOAL: [sim: Domicílio Judicial Eletrônico, envio dd/mm, ciência dd/mm (ID) | NÃO: só DJEN/advogado (ID); a Súmula 410 impede cobrar a multa agora]
PRAZO E DESCUMPRIMENTO: venceu em dd/mm; multa de dd/mm a dd/mm; [n] dias; prova (ID)
CREDOR NÃO FICOU INERTE: [ID, data, pedido, decisão] | NENHUM PEDIDO: risco de redução da multa
VALORES: [tabela da calculadora]
CAUÇÃO: [não se aplica: só depósito, sem levantamento | dispensa: necessidade concreta + gratuidade (ID), súmula (ID)]
RISCOS: [itens]
DECIDA:
 (a) referência sem teto: valor da causa R$ [x] (ID) ou valor pago no contrato R$ [y] (ID)?
 (b) prazo omisso: dias úteis ou corridos?
 (c) atualizar os valores? O índice é o da sentença ou da decisão de tutela (ID); pergunte o índice só se nenhuma das duas o fixou.
 (d) ressalvar o saldo acima do limite para a execução definitiva?
 (e) só depósito em conta judicial, ou pedir também o levantamento (exige caução ou dispensa)?
 (f) quem assina (nome e OAB)?
```

Pergunte se pode seguir e não redija antes da resposta.

## Fase 3: jurisprudência

1. Comece por `references/precedentes.md`. Reabra cada julgado que for usar e confira o link, o número, o órgão, o relator, as datas e a ementa.
2. Pesquise julgados recentes e concordantes, um por seção da peça: intimação pessoal pelo Domicílio e Súmula 410; cumprimento provisório de astreintes (art. 537, § 3º); credor que não ficou inerte; limite e proporcionalidade; caução.
3. Fontes que funcionaram em 19/11/2026:
   - **STJ, Íntegra de Acórdãos:** `https://processo.stj.jus.br/processo/revista/inteiroteor/?num_registro=NÚMERO_DE_REGISTRO` abre sem captcha. Leia o PDF com o MarkItDown.
   - **STJ, Informativo e repetitivos:** `processo.stj.jus.br/jurisprudencia/externo/informativo` e `processo.stj.jus.br/repetitivos`.
   - **SCON:** fica atrás do Cloudflare; use-o pelo navegador do advogado.
   - **TJCE:** o formulário `https://esaj.tjce.jus.br/cjsg/consultaCompleta.do` exige navegador (tem reCAPTCHA invisível). Desmarque "Pesquisar por sinônimos" para busca exata. O PDF do acórdão abre direto em `https://esaj.tjce.jus.br/cjsg/getArquivo.do?cdAcordao=N&cdForo=0`.
   - **JusBrasil:** só pelo Chrome do advogado, com a extensão Claude in Chrome.
   
   Faça uma consulta por vez, porque buscas em rajada são bloqueadas, e feche as abas que abrir.
4. Acrescente a `references/precedentes.md` o julgado novo que conferir, para a próxima peça.

Nunca cite julgado que não tenha sido aberto e conferido.

## Fase 4: redação

Siga `references/estrutura-da-peca.md`. Em resumo: síntese primeiro; decisão exequenda e sua eficácia; intimação pessoal (com o parágrafo explícito sobre o Domicílio); descumprimento e contagem; o credor não ficou inerte; valor executado com a tabela simples; caução; pedidos.

Escreva a petição em Markdown (marcações em `gerar_docx.py --help`) e gere o Word com `scripts/gerar_docx.py`, que usa a folha timbrada. O demonstrativo não vai no Word: ele entra no PDF dos documentos. Antes de gerar, rode `scripts/conferir_citacoes.py` com a petição, `references/dispositivos.md`, o `processo.md` e o texto de cada julgado citado (lido com `ler_processo.py`); só entregue com 0 trechos sem correspondência. Nome do arquivo: `Cumprimento provisório - [exequente] - [nº do processo].docx`.

**Demonstrativo de cálculo.** Monte um Markdown com cartões de resumo (total, principal e multa), a tabela-resumo, a conta da multa (ciência, vencimento, período, dias, valor diário, acumulado e o limite aplicado) e, se houve atualização, a tabela de `scripts/correcao.py`. Gere o PDF com `scripts/demonstrativo_pdf.py` e abra-o para conferir: nada de página quase vazia nem tabela cortada no fim.

**Entrega numa pasta.** A pasta principal fica na Mesa: `~/Desktop/Cumprimento Provisórios - HRH` (para outro grupo executado, `Cumprimento Provisórios - [executada]`). Dentro dela, uma subpasta com o nome completo do cliente, com:

1. `Cumprimento provisório - [cliente] - [nº do processo].docx`: a petição;
2. `Procuração - [cliente].pdf`: só a procuração da parte do advogado (com a declaração de hipossuficiência, se vier junto), nunca a da parte adversa;
3. `Documentos do cumprimento provisório - [nº curto].pdf`: os demais documentos num só PDF, com marcadores, nesta ordem: demonstrativo de cálculo; decisão exequenda; sentença que confirmou a tutela e certidão de publicação; petição inicial; base do cálculo (trecho do contrato com o índice e extrato dos pagamentos); peças em que o credor comunicou o descumprimento, com a resposta do juízo; recurso sem efeito suspensivo, só se a exigibilidade depender dele (art. 522, II);
4. `Aba Expedientes - intimação pelo Domicílio Judicial Eletrônico.pdf`: os prints da aba Expedientes enviados pelo advogado, com o expediente de cada executada destacado por `scripts/destacar_expediente.py`. Se a prova da intimação for mandado ou AR, ela entra no PDF dos documentos.

Os arquivos de trabalho (petição em Markdown, demonstrativo em Markdown e PDF, extrato em CSV) ficam em `.trabalho/`, dentro da subpasta, oculta no Finder. Monte os PDFs com `scripts/montar_kit.py --pasta ... --avulso "Procuração - [cliente]=ID" --item ...`, usando páginas internas para trechos (`ID:8,22-23`). Antes de entregar, abra o PDF dos documentos e confira que cada marcador começa na página certa (o carimbo "Num. ID - Pág. N").

Junto da peça, mande ao advogado:

- a tabela de valores;
- a lista de IDs usados;
- o que ficou pendente (por exemplo, certidão de ciência a juntar ou julgado não encontrado).

## Checklist final (conferir antes de entregar)

- Cada documento citado tem ID.
- A sentença que confirmou a tutela está citada com ID. Se não há sentença, o advogado decidiu protocolar e a peça enfrenta o Tema 743 (EAREsp 1.883.876/RS) às claras.
- Cada dispositivo foi transcrito literalmente na primeira citação, a partir de `dispositivos.md` ou do Planalto; depois aparece só pelo número; nenhuma nota "(Redação dada...)" foi copiada. O `conferir_citacoes.py` deu 0 trechos sem correspondência.
- Todo julgado foi aberto e conferido, tem link, e os de STJ e TJCE concordam com a tese.
- A intimação pessoal está demonstrada com data e ID, com o parágrafo explícito sobre o Domicílio Judicial Eletrônico, ou a peça pede a intimação pessoal.
- As datas e os valores batem com a saída da calculadora, e a tabela está na peça.
- Se houve atualização, o demonstrativo segue o modelo de `references/estrutura-da-peca.md` (seção 6: método, índice, valores e acumulado), usa o índice da sentença ou da decisão de tutela, com ID, e foi conferido linha a linha por script.
- A seção "o credor não ficou inerte" está presente, ou o advogado foi avisado do risco.
- A caução está tratada (arts. 537, § 3º, 520, IV, e 521).
- Os pedidos trazem, sem transcrever esses artigos: pagamento em 15 dias sob pena de multa de 10% e honorários de 10% (arts. 520, § 2º, e 523, § 1º); SISBAJUD (art. 854); valor mantido em conta judicial até o trânsito em julgado ou a liberação judicial; e, se a obrigação ainda estiver descumprida, nova intimação pessoal e medidas coercitivas. Não há pedido de majoração, salvo se o advogado pediu.
- O valor atribuído ao cumprimento provisório está indicado.
- A qualificação das partes é completa (é processo incidental novo): nome, nacionalidade, estado civil, profissão, RG, CPF, e-mail e endereço da exequente; razão social, CNPJ e endereço das executadas, com o ID de onde saiu cada endereço.
- O Word está na folha timbrada, com o endereçamento em negrito, justificado e sem recuo, e o link de cada julgado na linha de baixo, entre parênteses e clicável. Abra o Word (ou exporte em PDF) e confira página por página: assinatura inteira numa página, tabela sem coluna espremida.
- A pasta do cliente tem os quatro arquivos, com a procuração só da parte do advogado, o expediente destacado no print, e nenhuma peça desconsiderada entrou nela nem na análise.
