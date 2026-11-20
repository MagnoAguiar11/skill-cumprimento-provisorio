#!/usr/bin/env python3
"""Converte a petição em Markdown simples num .docx na folha timbrada do escritório (python-docx; scripts/ambiente.py acha o uv ou o Python próprio da skill).

A folha timbrada é assets/folha-modelo.docx (cabeçalho com a logo e rodapé com o endereço); troque com --modelo.

Marcações aceitas:
  ! linha             endereçamento: negrito, justificado, sem recuo e sem espaço entre parágrafos
  # Título            centralizado, negrito        ## Seção        negrito, maiúsculas
  > citação           recuo de 4 cm, 10 pt, espaço simples (lei e ementa)
  > (https://...)     linha do link, logo abaixo da citação, no mesmo formato (alinhada à esquerda)
  ^ linha             centralizada (assinatura; o bloco não se separa)    ---pagina---    quebra de página
  Hífen entre algarismos (nº do processo, CPF, CNPJ) vira hífen inquebrável.
  | tabela |          cabeçalho azul repetido em cada página, linhas alternadas, linha de total destacada,
                      colunas na largura do texto;
                      alinhamento pela linha |---|---:| (":" à direita = coluna à direita)
  **negrito**, *itálico* e endereços https://... (viram link clicável) no meio do texto.
  Parágrafo comum = justificado, 12 pt, entrelinha 1,5, recuo de 1,25 cm.

  python3 gerar_docx.py peticao.md -o "Cumprimento provisório.docx"
  python3 gerar_docx.py --teste
"""
import argparse
import sys
import tempfile
from pathlib import Path

import ambiente  # acha o uv (mesmo fora do PATH) ou o Python próprio da skill

MODELO = Path(__file__).resolve().parent.parent / "assets" / "folha-modelo.docx"

GERAR = r'''
import re, sys
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

AZUL, LINHA, ZEBRA, TOTAL = "013F6E", "C9D3DF", "F3F6FA", "E3EAF3"
TOKENS = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|https?://[^\s)]+)")
NUM = re.compile(r"^[\d.,%/R$ ()*-]+$")
md, saida, modelo = sys.argv[1], sys.argv[2], sys.argv[3]

if modelo:
    doc = Document(modelo)
    corpo = doc.element.body
    for el in list(corpo):
        if el.tag != qn("w:sectPr"):
            corpo.remove(el)
else:
    doc = Document()
    s = doc.sections[0]
    s.page_height, s.page_width = Cm(29.7), Cm(21)
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(3), Cm(2), Cm(2.5), Cm(2)
base = doc.styles["Normal"]
base.font.name, base.font.size = "Arial", Pt(12)
rf = base.element.rPr.rFonts
for k in ("w:eastAsia", "w:cs"):
    rf.set(qn(k), "Arial")

def el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    return e

def link(par, url, tamanho):
    h = el("w:hyperlink")
    h.set(qn("r:id"), par.part.relate_to(url, RT.HYPERLINK, is_external=True))
    r, rpr = el("w:r"), el("w:rPr")
    rpr.append(el("w:color", val="0563C1")); rpr.append(el("w:u", val="single"))
    if tamanho:
        rpr.append(el("w:sz", val=tamanho * 2))
    t = el("w:t"); t.text = url; t.set(qn("xml:space"), "preserve")
    r.append(rpr); r.append(t); h.append(r); par._p.append(h)

def runs(par, texto, tamanho=None, cor=None, negrito=None):
    for parte in TOKENS.split(texto):
        if not parte:
            continue
        if parte.startswith("http"):
            link(par, parte, tamanho); continue
        b, i = parte.startswith("**"), parte.startswith("*") and not parte.startswith("**")
        r = par.add_run()
        for k, trecho in enumerate(re.split(r"(?<=\d)-(?=\d)", parte.strip("*") if (b or i) else parte)):
            if k:  # hífen inquebrável: nº do processo, CPF e CNPJ não se partem no fim da linha
                r._r.append(OxmlElement("w:noBreakHyphen"))
            t = el("w:t"); t.text = trecho; t.set(qn("xml:space"), "preserve"); r._r.append(t)
        r.bold, r.italic = (b or negrito) or None, i or None
        if tamanho:
            r.font.size = Pt(tamanho)
        if cor:
            r.font.color.rgb = RGBColor.from_string(cor)

def borda(pai, lado, cor, tam=4, tipo="single"):
    pai.append(el("w:" + lado, val=tipo, sz=tam, space=0, color=cor))

def celula(c, fundo=None, topo=None):
    tcpr = c._tc.get_or_add_tcPr()
    if fundo:
        tcpr.append(el("w:shd", val="clear", color="auto", fill=fundo))
    if topo:
        b = el("w:tcBorders"); borda(b, "top", topo, 12); tcpr.append(b)
    c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def tabela(linhas):
    alin = None
    if len(linhas) > 1 and re.match(r"^\|[\s:|-]+\|$", linhas[1].strip()):
        alin = ["r" if c.strip().endswith(":") and not c.strip().startswith(":") else "c" if c.strip().startswith(":") and c.strip().endswith(":") else "l"
                for c in linhas[1].strip().strip("|").split("|")]
        linhas = [linhas[0]] + linhas[2:]
    celulas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in linhas]
    n = max(len(c) for c in celulas)
    for c in celulas:
        c += [""] * (n - len(c))
    tam = 9 if n >= 7 else 10
    # colunas curtas (até 16 caracteres) ganham a largura de que precisam; as longas dividem o resto
    s0 = doc.sections[0]
    util = s0.page_width - s0.left_margin - s0.right_margin
    cw, pad = Cm(0.02 * tam), Cm(0.45)
    precisa = []
    for j in range(n):
        corpo = [c[j].replace("**", "") for c in celulas[1:]] or [""]
        cab = max((len(w) for w in celulas[0][j].replace("**", "").split()), default=4) * 1.1
        precisa.append(max(cab, max(len(x) for x in corpo)))
    larg = [int(x * cw + pad) if x <= 16 else 0 for x in precisa]
    longas = [j for j in range(n) if not larg[j]]
    resto = util - sum(larg)
    if not longas:
        larg = [int(util * x / sum(larg)) for x in larg]
    elif resto > len(longas) * Cm(2.5):
        soma = sum(min(precisa[j], 60) for j in longas)
        for j in longas:
            larg[j] = int(resto * min(precisa[j], 60) / soma)
    else:
        larg = [int(util * x / sum(precisa)) for x in precisa]
    t = doc.add_table(rows=len(celulas), cols=n)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblpr = t._tbl.tblPr
    tblpr.append(el("w:tblW", w=int(util / 635), type="dxa"))
    tblpr.append(el("w:tblLayout", type="fixed"))
    for row in t.rows:
        for j in range(n):
            row.cells[j].width = larg[j]
    for j in range(n):
        t.columns[j].width = larg[j]
    b = el("w:tblBorders")
    borda(b, "top", AZUL, 12); borda(b, "bottom", AZUL, 12); borda(b, "insideH", LINHA, 4)
    for lado in ("left", "right", "insideV"):
        borda(b, lado, "auto", 0, "nil")
    tblpr.append(b)
    m = el("w:tblCellMar")
    for lado, v in (("top", 70), ("bottom", 70), ("left", 110), ("right", 110)):
        m.append(el("w:" + lado, w=v, type="dxa"))
    tblpr.append(m)
    for i, linha in enumerate(celulas):
        row = t.rows[i]
        trpr = row._tr.get_or_add_trPr()
        trpr.append(el("w:cantSplit"))
        cheias = [x for x in linha if x]
        total = i > 0 and cheias and all(x.startswith("**") for x in cheias)
        if i == 0:
            trpr.append(el("w:tblHeader", val="true"))
        for j in range(n):
            texto = linha[j] if j < len(linha) else ""
            c = row.cells[j]; p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            if i == 0:
                runs(p, texto.replace("**", ""), tam, "FFFFFF", True); celula(c, AZUL)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                continue
            runs(p, texto, tam)
            celula(c, TOTAL if total else ZEBRA if i % 2 == 0 else None, AZUL if total else None)
            a = alin[j] if alin and j < len(alin) else ("r" if NUM.match(texto.replace("*", "")) and texto else "l")
            p.alignment = {"r": WD_ALIGN_PARAGRAPH.RIGHT, "c": WD_ALIGN_PARAGRAPH.CENTER}.get(a, WD_ALIGN_PARAGRAPH.LEFT)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)

linhas = open(md, encoding="utf-8").read().splitlines()
i, anterior = 0, None
while i < len(linhas):
    l = linhas[i].rstrip()
    if l.startswith("|"):
        bloco = []
        while i < len(linhas) and linhas[i].startswith("|"):
            bloco.append(linhas[i]); i += 1
        tabela(bloco); anterior = None; continue
    i += 1
    if not l.strip():
        continue
    if l.strip() == "---pagina---":
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE); anterior = None; continue
    if l.startswith("!"):
        p = doc.add_paragraph(); runs(p, l[1:].strip(), negrito=True)
        f = p.paragraph_format; f.space_before = f.space_after = Pt(0); f.first_line_indent = Cm(0); f.line_spacing = 1.0
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if not (i < len(linhas) and linhas[i].startswith("!")):
            doc.add_paragraph().paragraph_format.space_after = Pt(0)  # linha em branco depois do endereçamento
        anterior = None; continue
    if l.startswith("# "):
        p = doc.add_paragraph(); runs(p, l[2:].strip("* "), negrito=True); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f = p.paragraph_format; f.space_before, f.space_after, f.keep_with_next = Pt(12), Pt(12), True
        anterior = None; continue
    if l.startswith("## "):
        p = doc.add_paragraph(); runs(p, l[3:].strip("* ").upper(), negrito=True)
        f = p.paragraph_format; f.space_before, f.space_after, f.keep_with_next = Pt(12), Pt(6), True
        anterior = None; continue
    if l.startswith(">"):
        texto = l.lstrip("> ").strip()
        if texto.startswith("(") and anterior is not None:  # link logo abaixo da citação
            anterior.paragraph_format.space_after = Pt(0); anterior.paragraph_format.keep_with_next = True
        p = doc.add_paragraph(); runs(p, texto, 10)
        f = p.paragraph_format; f.left_indent = Cm(4); f.line_spacing = 1.0; f.space_after = Pt(10)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if texto.startswith("(") else WD_ALIGN_PARAGRAPH.JUSTIFY
        anterior = p; continue
    proxima = next((x for x in linhas[i:] if x.strip()), "")
    if l.startswith("^"):  # assinatura: o bloco não se separa entre páginas
        p = doc.add_paragraph(); runs(p, l[1:].strip()); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f = p.paragraph_format; f.space_after = Pt(0); f.keep_with_next = proxima.startswith("^")
        if not (i >= 2 and linhas[i - 2].startswith("^")):
            f.space_before = Pt(30)
        anterior = None; continue
    p = doc.add_paragraph(); runs(p, l.strip())
    f = p.paragraph_format; f.line_spacing = 1.5; f.space_after = Pt(6); f.first_line_indent = Cm(1.25)
    f.keep_with_next = proxima.startswith("^")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    anterior = None
doc.save(saida)
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md", nargs="?", type=Path)
    ap.add_argument("-o", "--saida", type=Path)
    ap.add_argument("--modelo", type=Path, default=MODELO, help="folha timbrada .docx (padrão: assets/folha-modelo.docx)")
    ap.add_argument("--sem-modelo", action="store_true", help="página em branco, sem timbre")
    ap.add_argument("--teste", action="store_true")
    a = ap.parse_args()
    if a.teste:
        return _teste()
    if not a.md:
        ap.error("informe o arquivo .md da petição")
    saida = a.saida or a.md.with_suffix(".docx")
    gerar(a.md, saida, None if a.sem_modelo else a.modelo)
    print(saida)


def gerar(md, saida, modelo=MODELO):
    if modelo and not Path(modelo).exists():
        sys.exit(f"Folha timbrada não encontrada: {modelo} (use --modelo ou --sem-modelo)")
    Path(saida).expanduser().parent.mkdir(parents=True, exist_ok=True)  # cria a pasta do cliente, se faltar
    try:
        r = ambiente.rodar(["python-docx==1.1.2"], ["-c", GERAR, str(md), str(Path(saida).expanduser()), str(modelo or "")])
    except ambiente.SemAmbiente as e:
        ambiente.falhar(e)
    if r.returncode != 0:
        sys.exit("Falha ao gerar o Word:\n" + r.stderr[-2000:])


def _teste():
    import zipfile
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp, "t.md")
        md.write_text("! EXCELENTÍSSIMO JUÍZO\n\n# TÍTULO\n\n## 1. Síntese\n\nTexto com **negrito** e *itálico*, processo nº 0000123-45.2025.\n\n"
                      "> \"Citação com **destaque**.\"\n> (https://exemplo.jus.br/a?b=1)\n\n"
                      "| Item | Valor |\n|---|---:|\n| Multa | 1.000,00 |\n| **Total** | **2.000,00** |\n\n---pagina---\n\n^ ASSINATURA\n",
                      encoding="utf-8")
        for modelo in ([MODELO] if MODELO.exists() else []) + [None]:
            out = Path(tmp, "t.docx")
            gerar(md, out, modelo)
            with zipfile.ZipFile(out) as z:  # fechar antes de apagar: o Windows não apaga arquivo aberto
                xml = z.read("word/document.xml").decode("utf-8")
                rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
            for esperado in ("EXCELENTÍSSIMO JUÍZO", "TÍTULO", "1. SÍNTESE", "w:hyperlink", "w:tblHeader", "013F6E", "E3EAF3",
                             "2.000,00", 'w:type="page"', "ASSINATURA", "destaque", "w:noBreakHyphen", "w:tblLayout"):
                assert esperado in xml, esperado
            assert "https://exemplo.jus.br/a?b=1" in rels.replace("&amp;", "&")
            if modelo:
                assert "header" in rels and "footer" in rels  # timbre preservado
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
