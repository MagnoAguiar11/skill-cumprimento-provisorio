#!/usr/bin/env python3
"""Transforma o demonstrativo de cálculo (Markdown simples) num PDF com a logo do escritório (Chrome headless).

O PDF vai junto com os documentos (montar_kit.py --item "Demonstrativo de cálculo=demonstrativo.pdf"),
não dentro da petição. Marcações:
  # Título                 ^ linha de identificação (processo, partes, data-base)
  = Rótulo: Valor          cartão de destaque (os "=" seguidos ficam lado a lado; o primeiro é o principal)
  ## Seção                 parágrafo comum (aceita **negrito**)      > nota em letra menor
  ---pagina---             quebra de página
  | tabela |               alinhamento pela linha |---|---:|; linha toda em **negrito** = total

  python3 demonstrativo_pdf.py demonstrativo.md -o "Demonstrativo de cálculo.pdf"
  python3 demonstrativo_pdf.py --teste
"""
import argparse
import base64
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
RODAPE = ("Almeida & Aguiar Advogados · Av. Sargento Hermínio 3100 – Torre Empresarial Rio Mar · 60355-512 · "
          "WhatsApp (85) 99231-7224")
CHROMES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
           r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
           "google-chrome", "chromium", "chromium-browser", "chrome", "msedge"]

CSS = """
@page { size: A4; margin: 14mm 14mm 18mm 14mm;
  @bottom-left { content: "%s"; font: 7.5pt 'Helvetica Neue', Arial, sans-serif; color: #6B7A8C; }
  @bottom-right { content: "Página " counter(page) " de " counter(pages); font: 7.5pt 'Helvetica Neue', Arial, sans-serif; color: #6B7A8C; } }
:root { --azul: #013F6E; --azul-claro: #E8EEF5; --tinta: #1D2733; --cinza: #5E6E80; --linha: #D3DBE5; }
* { box-sizing: border-box; }
body { margin: 0; color: var(--tinta); font: 9.5pt/1.45 'Helvetica Neue', Arial, sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
header { display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 10px; border-bottom: 2px solid var(--azul); margin-bottom: 16px; }
header img { height: 34px; }
header .tipo { font: 600 8pt 'Helvetica Neue', Arial, sans-serif; letter-spacing: .14em; text-transform: uppercase; color: var(--azul); }
h1 { font: 600 19pt/1.2 'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif; color: var(--azul); margin: 0 0 6px; }
.meta { color: var(--cinza); font-size: 8.5pt; margin: 0 0 2px; }
.cartoes { display: grid; grid-template-columns: repeat(var(--n), 1fr); gap: 10px; margin: 16px 0 6px; }
.cartao { border: 1px solid var(--linha); border-radius: 8px; padding: 10px 12px; background: #fff; }
.cartao span { display: block; font-size: 7.5pt; letter-spacing: .08em; text-transform: uppercase; color: var(--cinza); }
.cartao b { display: block; margin-top: 4px; font: 600 14pt 'Palatino Linotype', Palatino, Georgia, serif; color: var(--azul); font-variant-numeric: tabular-nums; }
.cartao.principal { background: var(--azul); border-color: var(--azul); }
.cartao.principal span { color: #C9D7E8; } .cartao.principal b { color: #fff; }
h2 { font: 600 11.5pt 'Palatino Linotype', Palatino, Georgia, serif; color: var(--azul); margin: 20px 0 8px; padding-left: 9px; border-left: 3px solid var(--azul); break-after: avoid; }
p { margin: 0 0 7px; text-align: justify; }
.nota { font-size: 8pt; color: var(--cinza); }
table { width: 100%%; border-collapse: collapse; margin: 6px 0 10px; font-size: 8.3pt; font-variant-numeric: tabular-nums; }
thead { display: table-header-group; }
th { background: var(--azul); color: #fff; font-weight: 600; padding: 6px 7px; text-align: center; vertical-align: bottom; }
td { padding: 3.4px 7px; border-bottom: 1px solid var(--linha); }
tbody tr:nth-child(even) td { background: #F5F8FB; }
tr { break-inside: avoid; }
tr.total td { background: var(--azul-claro) !important; border-top: 2px solid var(--azul); border-bottom: 2px solid var(--azul); font-weight: 700; color: var(--azul); }
.r { text-align: right; white-space: nowrap; } .c { text-align: center; } .nw { white-space: nowrap; }
"""


def inline(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(t))


def tabela(linhas):
    alin = []
    if len(linhas) > 1 and re.match(r"^\|[\s:|-]+\|$", linhas[1].strip()):
        for c in linhas[1].strip().strip("|").split("|"):
            c = c.strip()
            alin.append("c" if c.startswith(":") and c.endswith(":") else "r" if c.endswith(":") else "")
        linhas = [linhas[0]] + linhas[2:]
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in linhas]
    out = ["<table><thead><tr>" + "".join(f"<th>{inline(c.replace('**', ''))}</th>" for c in rows[0]) + "</tr></thead><tbody>"]
    for r in rows[1:]:
        cheias = [c for c in r if c]
        cls = ' class="total"' if cheias and all(c.startswith("**") for c in cheias) else ""
        tds = "".join(f'<td class="{alin[j] if j < len(alin) else ""}{" nw" if len(c.replace("**", "")) <= 16 else ""}">'
                      f'{inline(c.replace("**", "") if cls else c)}</td>' for j, c in enumerate(r))
        out.append(f"<tr{cls}>{tds}</tr>")
    return "\n".join(out + ["</tbody></table>"])


def montar_html(md, rodape=RODAPE, logo=ASSETS / "logo.png"):
    corpo, linhas, i = [], md.splitlines(), 0
    while i < len(linhas):
        l = linhas[i].rstrip()
        if l.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith("|"):
                bloco.append(linhas[i]); i += 1
            corpo.append(tabela(bloco)); continue
        if l.startswith("= "):
            cards = []
            while i < len(linhas) and linhas[i].startswith("= "):
                rot, _, val = linhas[i][2:].partition(":")
                cards.append(f'<div class="cartao{" principal" if not cards else ""}"><span>{inline(rot.strip())}</span>'
                             f"<b>{inline(val.strip())}</b></div>")
                i += 1
            corpo.append(f'<div class="cartoes" style="--n:{len(cards)}">{"".join(cards)}</div>'); continue
        i += 1
        if not l.strip():
            continue
        if l.strip() == "---pagina---":
            corpo.append('<div style="break-before: page"></div>')
        elif l.startswith("# "):
            corpo.append(f"<h1>{inline(l[2:])}</h1>")
        elif l.startswith("## "):
            corpo.append(f"<h2>{inline(l[3:])}</h2>")
        elif l.startswith("^ "):
            corpo.append(f'<p class="meta">{inline(l[2:])}</p>')
        elif l.startswith("> "):
            corpo.append(f'<p class="nota">{inline(l[2:])}</p>')
        else:
            corpo.append(f"<p>{inline(l)}</p>")
    img = (f'<img src="data:image/png;base64,{base64.b64encode(Path(logo).read_bytes()).decode()}" alt="">'
           if Path(logo).exists() else "")
    css = CSS % rodape.replace('"', "'")
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Demonstrativo de cálculo</title>'
            f"<style>{css}</style></head><body><header>{img}<div class=\"tipo\">Demonstrativo de cálculo</div></header>"
            + "\n".join(corpo) + "</body></html>")


def chrome():
    for c in CHROMES:
        if Path(c).exists() or shutil.which(c):
            return c if Path(c).exists() else shutil.which(c)
    sys.exit("Chrome, Chromium ou Edge não encontrado: instale um deles para gerar o PDF do demonstrativo.")


def gerar_pdf(html_txt, saida):
    saida = Path(saida).expanduser()
    saida.parent.mkdir(parents=True, exist_ok=True)  # cria a pasta, se faltar
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp, "demonstrativo.html")
        pagina.write_text(html_txt, encoding="utf-8")
        r = subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
                            f"--user-data-dir={tmp}/perfil", f"--print-to-pdf={Path(saida).resolve()}", pagina.as_uri()],
                           capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        if not Path(saida).exists():
            sys.exit("Falha ao gerar o PDF:\n" + r.stderr[-1500:])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md", nargs="?", type=Path)
    ap.add_argument("-o", "--saida", type=Path)
    ap.add_argument("--html", type=Path, help="grava também o HTML (para conferir)")
    ap.add_argument("--teste", action="store_true")
    a = ap.parse_args()
    if a.teste:
        return _teste()
    if not a.md:
        ap.error("informe o demonstrativo .md")
    doc = montar_html(a.md.read_text(encoding="utf-8"))
    if a.html:
        a.html.write_text(doc, encoding="utf-8")
    saida = a.saida or a.md.with_suffix(".pdf")
    gerar_pdf(doc, saida)
    print(saida)


def _teste():
    md = ("# Demonstrativo\n^ Processo nº 1\n= Total: R$ 2,00\n= Multa: R$ 1,00\n## 1. Resumo\nTexto **forte** <x>.\n"
          "> nota\n---pagina---\n| Item | Valor |\n|---|---:|\n| A | 1,00 |\n| **Total** | **2,00** |\n")
    h = montar_html(md)
    for esperado in ("<h1>Demonstrativo</h1>", 'class="meta"', 'cartao principal', "--n:2", "<h2>1. Resumo</h2>",
                     "<b>forte</b> &lt;x&gt;", 'class="nota"', '<td class="r nw">1,00</td>', '<tr class="total">', "counter(pages)", "break-before: page"):
        assert esperado in h, esperado
    try:
        chrome()
    except SystemExit:
        print("ok: testes passaram (sem Chrome, o PDF não foi testado)")
        return
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp, "t.pdf")
        gerar_pdf(h, out)
        assert out.read_bytes()[:5] == b"%PDF-"
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
