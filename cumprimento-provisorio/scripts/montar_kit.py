#!/usr/bin/env python3
"""Monta, na pasta do cliente, os PDFs que instruem o cumprimento provisório (art. 522 do CPC).

Cada --avulso vira um PDF sozinho (ex.: a procuração). Os --item são juntados, na ordem dada, num
único PDF com marcadores (sumário lateral) por documento. Origem de cada item, pelo que vem depois do "=":
  ID do PJe          "Decisão exequenda=12345678"   ou só algumas páginas internas: "Contrato=12345679:8,22-23"
  PDF pronto         "Demonstrativo de cálculo=demonstrativo.pdf"
  imagens (prints)   "Prints=print1.png,print2.png"

  python3 montar_kit.py processo.pdf processo.md --pasta "~/Desktop/Cumprimento Provisórios - HRH/Fulana" \
      --avulso "Procuração - Fulana=12345677" \
      --juntar "Documentos do cumprimento provisório - 0000123-45.2025" \
      --item "Demonstrativo de cálculo=demonstrativo.pdf" \
      --item "Decisão de tutela de urgência (decisão exequenda)=12345678" \
      --item "Contrato - índice de correção=12345679:8,22-23"
  python3 montar_kit.py --teste

O processo.md é o gerado por ler_processo.py (títulos "### Página N · ID X (pág. k)").
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Junta páginas, PDFs e imagens com marcadores; roda pelo uv para não exigir instalação.
JUNTAR = r'''
import io, json, sys
from pypdf import PdfReader, PdfWriter
from PIL import Image
plano = json.load(open(sys.argv[1]))
fonte = PdfReader(plano["pdf"])
for arquivo in plano["arquivos"]:
    w = PdfWriter()
    for it in arquivo["itens"]:
        marca = it["marcador"] if arquivo["marcadores"] else None
        if it["tipo"] == "paginas":
            w.append(fonte, pages=[p - 1 for p in it["paginas"]], outline_item=marca, import_outline=False)
        elif it["tipo"] == "pdf":
            w.append(it["arquivo"], outline_item=marca, import_outline=False)
        else:
            buf = io.BytesIO()
            imgs = [Image.open(c).convert("RGB") for c in it["arquivos"]]
            imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:], resolution=150)
            w.append(PdfReader(buf), outline_item=marca, import_outline=False)
    w.write(arquivo["saida"])
'''
IMAGEM = (".png", ".jpg", ".jpeg")


def mapa_de_paginas(md):
    """{id: {pág. interna: página do PDF}} a partir dos títulos do processo.md."""
    out = {}
    for m in re.finditer(r"^### Página (\d+) · ID (\d+) \(pág\. (\d+)\)", Path(md).read_text(encoding="utf-8"), re.M):
        out.setdefault(m.group(2), {})[int(m.group(3))] = int(m.group(1))
    return out


def faixa(txt):
    """'8,22-23' -> [8, 22, 23]"""
    out = []
    for parte in txt.split(","):
        a, _, b = parte.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def planejar(itens, mapa):
    """[(rótulo, origem)] -> (itens do plano, faltas). Nada é gerado se houver falta."""
    plano, faltas = [], []
    for n, (rotulo, alvo) in enumerate(itens, 1):
        marca = f"{n:02d} - {rotulo}"
        if re.fullmatch(r"\d+(:[\d,-]+)?", alvo):
            id_, _, pags = alvo.partition(":")
            doc = mapa.get(id_)
            if not doc:
                faltas.append(f"ID {id_} não está no processo.md")
                continue
            internas = faixa(pags) if pags else sorted(doc)
            sem = [p for p in internas if p not in doc]
            if sem:
                faltas.append(f"ID {id_}: páginas {sem} não existem")
                continue
            sufixo = f"ID {id_}" + (f", págs. {pags}" if pags else "")
            plano.append({"tipo": "paginas", "rotulo": rotulo, "marcador": f"{marca} ({sufixo})", "paginas": [doc[p] for p in internas]})
        elif alvo.lower().endswith(".pdf"):
            if not Path(alvo).exists():
                faltas.append(f"arquivo não encontrado: {alvo}")
                continue
            plano.append({"tipo": "pdf", "rotulo": rotulo, "marcador": marca, "arquivo": str(Path(alvo).resolve())})
        else:
            arqs = [c.strip() for c in alvo.split(",")]
            ruins = [c for c in arqs if not (c.lower().endswith(IMAGEM) and Path(c).exists())]
            if ruins:
                faltas.append(f"origem não reconhecida (ID, .pdf ou imagens existentes): {', '.join(ruins)}")
                continue
            plano.append({"tipo": "imagens", "rotulo": rotulo, "marcador": marca, "arquivos": [str(Path(c).resolve()) for c in arqs]})
    return plano, faltas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="?", type=Path)
    ap.add_argument("md", nargs="?", type=Path)
    ap.add_argument("--pasta", type=Path, help="pasta do cliente (criada se não existir)")
    ap.add_argument("--avulso", action="append", default=[], help='"Nome do arquivo=origem": vira um PDF sozinho')
    ap.add_argument("--item", action="append", default=[], help='"Rótulo=origem": entra no PDF juntado, na ordem dada')
    ap.add_argument("--juntar", default="Documentos do cumprimento provisório", help="nome do PDF juntado (sem .pdf)")
    ap.add_argument("--teste", action="store_true")
    a = ap.parse_args()
    if a.teste:
        return _teste()
    if not (a.pdf and a.md and a.pasta):
        ap.error("informe o PDF do processo, o processo.md e --pasta")
    mapa = mapa_de_paginas(a.md)
    avulsos, f1 = planejar([tuple(x.split("=", 1)) for x in a.avulso], mapa)
    juntos, f2 = planejar([tuple(x.split("=", 1)) for x in a.item], mapa)
    if f1 + f2:
        sys.exit("Nada foi gerado:\n - " + "\n - ".join(f1 + f2))
    if not shutil.which("uv"):
        sys.exit("Instale o uv (https://docs.astral.sh/uv/) para montar os PDFs.")
    pasta = a.pasta.expanduser()
    pasta.mkdir(parents=True, exist_ok=True)
    arquivos = [{"saida": str(pasta / f"{x['rotulo']}.pdf"), "itens": [x], "marcadores": False} for x in avulsos]
    if juntos:
        arquivos.append({"saida": str(pasta / f"{a.juntar}.pdf"), "itens": juntos, "marcadores": True})
    with tempfile.TemporaryDirectory() as tmp:
        plano = Path(tmp, "plano.json")
        plano.write_text(json.dumps({"pdf": str(a.pdf.resolve()), "arquivos": arquivos}), encoding="utf-8")
        r = subprocess.run(["uv", "run", "--no-project", "--quiet", "--with", "pypdf==5.1.0", "--with", "pillow==10.4.0",
                            "python", "-c", JUNTAR, str(plano)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("Falha ao montar os PDFs:\n" + r.stderr[-2000:])
    for arq in arquivos:
        p = Path(arq["saida"])
        print(f"{p.name}  ({p.stat().st_size / 1e6:.1f} MB)")
        for it in arq["itens"] if arq["marcadores"] else []:
            print("   " + it["marcador"])


def _teste():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp, "p.md")
        md.write_text("## Texto\n\n### Página 5 · ID 111 (pág. 1)\n\nx\n\n### Página 6 · ID 111 (pág. 2)\n\n"
                      "### Página 9 · ID 222 (pág. 1)\n\n### Página 10 · ID 222 (pág. 2)\n\n### Página 11 · ID 222 (pág. 3)\n", encoding="utf-8")
        pronto, img = Path(tmp, "d.pdf"), Path(tmp, "print.png")
        pronto.write_bytes(b"%PDF-1.4\n"); img.write_bytes(b"x")
        mapa = mapa_de_paginas(md)
        assert mapa == {"111": {1: 5, 2: 6}, "222": {1: 9, 2: 10, 3: 11}}
        plano, faltas = planejar([("Inicial", "111"), ("Trecho", "222:1,3"), ("Cálculo", str(pronto)), ("Prints", str(img))], mapa)
        assert not faltas, faltas
        assert plano[0]["paginas"] == [5, 6] and plano[1]["paginas"] == [9, 11]
        assert plano[1]["marcador"] == "02 - Trecho (ID 222, págs. 1,3)"
        assert [p["tipo"] for p in plano] == ["paginas", "paginas", "pdf", "imagens"]
        _, faltas = planejar([("X", "999"), ("Y", "111:7"), ("Z", "falta.pdf"), ("W", "nada.png")], mapa)
        assert len(faltas) == 4  # ID ausente, página inexistente, PDF e imagem inexistentes travam tudo
        assert faixa("8,22-23") == [8, 22, 23]
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
