#!/usr/bin/env python3
"""Lê o PDF do processo com o MarkItDown e monta um Markdown com o mapa de IDs.

O MarkItDown (github.com/microsoft/markitdown, licença MIT) converte o PDF em texto.
Este script separa as páginas, tira o rodapé de assinatura do PJe de cada uma,
anota o ID (PJe) ou as folhas (e-SAJ) e lista as páginas sem texto (escaneadas).
Se o MarkItDown não rodar no computador, o texto sai do pypdfium2 (--leitor escolhe à mão).

  python3 ler_processo.py processo.pdf              -> grava processo.md ao lado do PDF
  python3 ler_processo.py processo.pdf -o saida.md
  python3 ler_processo.py --teste
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MARKITDOWN = "markitdown[pdf]==0.1.9"
# Python 3.12 fixo (o mais novo nem sempre tem os pacotes). No Windows ARM, a versão x64, que o Windows emula:
# vários pacotes (cryptography, pyclipper) não têm versão pronta para ARM e não compilam sem o Visual C++.
ARM_WIN = os.name == "nt" and "ARM64" in os.environ.get("PROCESSOR_ARCHITECTURE", "") + os.environ.get("PROCESSOR_ARCHITEW6432", "")
PYTHON = ["--python", "cpython-3.12-windows-x86_64-none" if ARM_WIN else "3.12"]
UTF8 = {"encoding": "utf-8", "errors": "replace", "env": {**os.environ, "PYTHONUTF8": "1"}}  # Windows: sem isso o texto sai em cp1252

ID_PJE = re.compile(r"Num\.\s*(\d{5,})\s*-\s*P[áa]g\.\s*(\d+)")
ASSINATURA = re.compile(r"Assinado eletronicamente por:\s*(.+?)\s*-\s*(\d{2}/\d{2}/\d{4})")
RODAPE = re.compile(r"Assinado eletronicamente por:|^https?://|N[úu]mero do documento:|^Num\.\s*\d{5,}\s*-\s*P[áa]g\.|^Este documento foi gerado pelo usu[áa]rio", re.I)
FLS = re.compile(r"^fls\.\s*(\d+)$", re.I | re.M)  # carimbo do e-SAJ, sozinho na linha; "fls. 209/210" no texto não conta


# O MarkItDown 0.1.9 junta todas as páginas sem separador quando alguma página tem tabela
# ou formulário (o índice do PJe tem). Por isso cada página vai sozinha para ele; o
# pypdfium2 que corta as páginas já vem como dependência do markitdown[pdf].
POR_PAGINA = r'''
import io, sys
import pypdfium2 as pdfium
from markitdown import MarkItDown, StreamInfo
md, doc, out = MarkItDown(), pdfium.PdfDocument(sys.argv[1]), []
for i in range(len(doc)):
    novo = pdfium.PdfDocument.new(); novo.import_pages(doc, [i]); b = io.BytesIO(); novo.save(b); b.seek(0)
    try:
        out.append(md.convert_stream(b, stream_info=StreamInfo(extension=".pdf")).text_content)
    except Exception as e:
        out.append("")
        print(f"página {i + 1}: {e}", file=sys.stderr)
sys.stdout.write("\f".join(out))
'''


# Plano B: se o MarkItDown não rodar no computador (no Windows, o onnxruntime que ele usa pede o Visual C++),
# o texto de cada página sai direto do pypdfium2, que não depende de nada.
SO_PDFIUM = r'''
import sys
import pypdfium2 as pdfium
doc = pdfium.PdfDocument(sys.argv[1])
sys.stdout.write("\f".join(doc[i].get_textpage().get_text_bounded().replace("\r\n", "\n") for i in range(len(doc))))
'''


def converter(pdf, leitor="auto"):
    if leitor == "pdfium":
        if not shutil.which("uv"):
            sys.exit("Instale o uv (https://docs.astral.sh/uv/) para ler o PDF.")
        cmd = ["uv", "run", "--no-project", "--quiet", *PYTHON, "--with", "pypdfium2==4.30.0", "python", "-c", SO_PDFIUM, str(pdf)]
    elif shutil.which("uv"):
        cmd = ["uv", "run", "--no-project", "--quiet", *PYTHON, "--with", MARKITDOWN, "python", "-c", POR_PAGINA, str(pdf)]
    elif shutil.which("markitdown"):
        # shortcut: sem uv, o documento vai inteiro e as páginas podem vir juntas; instale o uv para separar
        cmd = ["markitdown", str(pdf)]
    else:
        sys.exit("MarkItDown não encontrado. Instale o uv (https://docs.astral.sh/uv/) "
                 "ou rode: pip install 'markitdown[pdf]' (Python 3.10+).")
    r = subprocess.run(cmd, capture_output=True, **UTF8)
    if r.returncode != 0 and leitor == "auto" and shutil.which("uv"):
        print("O MarkItDown não rodou neste computador; o texto foi lido pelo pypdfium2. Motivo:\n"
              + r.stderr.strip()[-600:], file=sys.stderr)
        return converter(pdf, "pdfium")
    if r.returncode != 0:
        sys.exit("A leitura do PDF falhou:\n" + r.stderr[-2000:])
    avisos = [l for l in r.stderr.splitlines() if l.strip() and "FontBBox" not in l]  # ruído do pdfminer
    if avisos:
        print("\n".join(avisos)[-1000:], file=sys.stderr)
    return r.stdout


def faixas(nums):
    """[1, 2, 3, 5] -> '1-3, 5'"""
    out, ini = [], None
    for i, n in enumerate(nums):
        if ini is None:
            ini = n
        if i + 1 == len(nums) or nums[i + 1] != n + 1:
            out.append(str(ini) if ini == n else f"{ini}-{n}")
            ini = None
    return ", ".join(out)


def mapear(texto):
    paginas = texto.split("\f")
    if paginas and not paginas[-1].strip():
        paginas.pop()
    docs, sem_texto, saida = {}, [], []
    for n, bruto in enumerate(paginas, 1):
        linhas = [re.sub(r"[ \t]+", " ", l).strip() for l in bruto.splitlines()]
        tudo = "\n".join(linhas)
        conteudo = [l for l in linhas if l and not RODAPE.search(l)]
        m, a, f = ID_PJE.search(tudo), ASSINATURA.search(tudo), FLS.findall(tudo)
        if sum(len(l) for l in conteudo) < 40:  # só o carimbo do PJe: página escaneada
            sem_texto.append(n)
        rotulo = f"Página {n}"
        if m:
            id_, pag = m.group(1), int(m.group(2))
            rotulo += f" · ID {id_} (pág. {pag})"
            d = docs.setdefault(id_, {"paginas": [], "assinante": "", "data": "", "inicio": ""})
            d["paginas"].append(n)
            if a and not d["assinante"]:
                d["assinante"], d["data"] = a.group(1), a.group(2)
            if not d["inicio"]:
                d["inicio"] = next((l[:80] for l in conteudo if len(re.findall(r"[A-Za-zÀ-ú]", l)) >= 3), "")
        elif f:
            rotulo += f" · fls. {f[-1]}"
        saida.append((rotulo, "\n".join(conteudo)))
    return saida, docs, sem_texto


def montar(nome, saida, docs, sem_texto):
    md = [f"# Processo: {nome}", "",
          f"Texto extraído com MarkItDown ({MARKITDOWN}). {len(saida)} páginas, {len(docs)} documentos com ID.", ""]
    if docs:
        md += ["## Mapa de documentos", "", "| ID | Páginas do PDF | Assinado por | Data | Início do texto |", "|---|---|---|---|---|"]
        for id_, d in docs.items():
            celulas = [id_, faixas(d["paginas"]), d["assinante"], d["data"], d["inicio"]]
            md.append("| " + " | ".join(c.replace("|", "/") for c in celulas) + " |")
        md.append("")
    if sem_texto:
        md += ["## Páginas sem texto (provavelmente escaneadas)", "",
               f"{faixas(sem_texto)}. Leia como imagem (no Mac: `swift scripts/pdf_texto.swift processo.pdf --imagem {','.join(map(str, sem_texto[:20]))}`).", ""]
    md += ["## Texto", ""]
    for rotulo, texto in saida:
        md += [f"### {rotulo}", "", texto or "[sem texto]", ""]
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="?", type=Path)
    ap.add_argument("-o", "--saida", type=Path)
    ap.add_argument("--leitor", choices=["auto", "markitdown", "pdfium"], default="auto",
                    help="auto: MarkItDown e, se ele não rodar, pypdfium2")
    ap.add_argument("--teste", action="store_true", help="roda a autoverificação")
    a = ap.parse_args()
    if a.teste:
        return _teste()
    if not a.pdf or not a.pdf.is_file():
        ap.error("informe o PDF do processo")
    texto = converter(a.pdf, a.leitor)
    saida, docs, sem_texto = mapear(texto)
    destino = a.saida or a.pdf.with_suffix(".md")
    destino.write_text(montar(a.pdf.name, saida, docs, sem_texto), encoding="utf-8")
    print(f"{destino}: {len(saida)} página(s), {len(docs)} documento(s) com ID, "
          f"{len(sem_texto)} página(s) sem texto" + (f" ({faixas(sem_texto)})" if sem_texto else ""))
    if "\f" not in texto and len(ID_PJE.findall(texto)) > 1:
        print("ATENÇÃO: as páginas vieram juntas, e o mapa de IDs não é confiável. Instale o uv e rode de novo.", file=sys.stderr)


def _teste():
    rod = ("Assinado eletronicamente por: FULANO DE TAL - 10/03/2026 14:22:11\nhttps://pje.tjce.jus.br/x\n"
           "Número do documento: 26031014221100000012345678\nEste documento foi gerado pelo usuário 029.***.***-86 em 19/11/2026 18:52:00\n")
    texto = ("DECISÃO\nDefiro a tutela de urgência,   sob pena de multa diária de R$ 500,00.\n" + rod + "Num. 12345678 - Pág. 1\f"
             "Intime-se pessoalmente a ré pelo Domicílio Judicial Eletrônico, com urgência.\n" + rod + "Num. 12345678 - Pág. 2\f"
             + rod + "Num. 12345999 - Pág. 1\f"
             "Certidão de juntada do aviso de recebimento assinado pelo devedor (fls. 85/86).\nfls. 87\f"
             "Despacho às fls. 209/210 dos autos de origem.\f")
    saida, docs, sem_texto = mapear(texto)
    assert len(saida) == 5, len(saida)
    assert saida[4][0] == "Página 5"  # menção a folhas no texto não vira carimbo
    assert docs["12345678"]["paginas"] == [1, 2] and docs["12345678"]["data"] == "10/03/2026"
    assert docs["12345678"]["assinante"] == "FULANO DE TAL" and docs["12345678"]["inicio"] == "DECISÃO"
    assert sem_texto == [3], sem_texto
    assert "sob pena de multa diária" in saida[0][1] and "Assinado" not in saida[0][1]
    assert saida[3][0] == "Página 4 · fls. 87"
    assert faixas([1, 2, 3, 5, 7, 8]) == "1-3, 5, 7-8"
    md = montar("t.pdf", saida, docs, sem_texto)
    assert "| 12345678 | 1-2 | FULANO DE TAL | 10/03/2026 | DECISÃO |" in md
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
