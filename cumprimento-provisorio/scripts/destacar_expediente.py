#!/usr/bin/env python3
"""Destaca, nos prints da aba "Expedientes" do PJe, a linha de cada expediente pedido e gera um PDF.

Acha o texto com o Vision do macOS (ocr_linhas.swift). A linha do expediente vai do título
"Intimação (N) - Prioridade..." até o título do expediente seguinte; ela recebe fundo amarelo e
borda vermelha, e a frase da ciência ("... registrou ciência em ...") recebe marca-texto.
As páginas com destaque vêm primeiro; as demais seguem na ordem dada.

  python3 destacar_expediente.py print1.png print2.png --expediente 1234567 --expediente 1234568 \
      -o "Aba Expedientes - 0000123-45.2025.pdf"
  python3 destacar_expediente.py --teste
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TITULO = re.compile(r"^\S+ \((\d+)\) - Prioridade")  # "Intimação (1234567) - Prioridade: Normal - ..."

DESENHAR = r'''
import json, sys
from PIL import Image, ImageDraw
plano = json.load(open(sys.argv[1]))
paginas = []
for p in plano["paginas"]:
    base = Image.open(p["imagem"]).convert("RGBA")
    camada = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    for f in p["faixas"]:
        d.rounded_rectangle(f["caixa"], radius=10, fill=(255, 235, 59, 70))
        for m in f["marcas"]:
            d.rectangle(m, fill=(255, 200, 0, 120))
    base = Image.alpha_composite(base, camada)
    d = ImageDraw.Draw(base)
    for f in p["faixas"]:
        d.rounded_rectangle(f["caixa"], radius=10, outline=(211, 32, 39, 255), width=5)
    paginas.append(base.convert("RGB"))
paginas[0].save(plano["saida"], save_all=True, append_images=paginas[1:], resolution=150)
'''


def ocr(imagem):
    if not shutil.which("swift"):
        # shortcut: o OCR usa o Vision do macOS; em outro sistema, destaque o print à mão.
        sys.exit("Este script precisa do macOS (swift + Vision). Destaque o expediente à mão no print.")
    r = subprocess.run(["swift", str(AQUI / "ocr_linhas.swift"), str(imagem)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Falha no OCR de {imagem}:\n{r.stderr[-1500:]}")
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]


def faixas(linhas, expedientes, largura, altura):
    """Caixa de cada expediente pedido e marcas nas frases de ciência. Devolve {nº: faixa}."""
    titulos = sorted((l for l in linhas if TITULO.match(l["texto"])), key=lambda l: l["y"])
    out = {}
    for i, t in enumerate(titulos):
        n = TITULO.match(t["texto"]).group(1)
        if n not in expedientes:
            continue
        topo = max(t["y"] - 12, 0)
        fim = titulos[i + 1]["y"] - 12 if i + 1 < len(titulos) else altura - 2
        marcas = [[l["x"] - 4, l["y"] - 3, l["x"] + l["w"] + 4, l["y"] + l["h"] + 3]
                  for l in linhas if "ciência em" in l["texto"] and topo <= l["y"] < fim]
        out[n] = {"caixa": [max(t["x"] - 10, 2), topo, largura - 6, fim], "marcas": marcas}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("imagens", nargs="*", type=Path)
    ap.add_argument("--expediente", action="append", default=[], help="número do expediente (repita para vários)")
    ap.add_argument("-o", "--saida", type=Path)
    ap.add_argument("--teste", action="store_true")
    a = ap.parse_args()
    if a.teste:
        return _teste()
    if not (a.imagens and a.expediente and a.saida):
        ap.error("informe os prints, ao menos um --expediente e -o saída.pdf")
    if not shutil.which("uv"):
        sys.exit("Instale o uv (https://docs.astral.sh/uv/) para desenhar o destaque.")
    paginas, achados = [], set()
    for img in a.imagens:
        linhas = ocr(img)
        largura = max(l["x"] + l["w"] for l in linhas) + 20
        altura = max(l["y"] + l["h"] for l in linhas) + 20
        r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(img)], capture_output=True, text=True)
        tam = re.findall(r"pixel(?:Width|Height): (\d+)", r.stdout)
        if len(tam) == 2:
            largura, altura = int(tam[0]), int(tam[1])
        f = faixas(linhas, set(a.expediente), largura, altura)
        achados |= set(f)
        paginas.append({"imagem": str(img.resolve()), "faixas": list(f.values())})
    faltam = [n for n in a.expediente if n not in achados]
    if faltam:
        sys.exit(f"Expediente(s) não encontrado(s) nos prints: {', '.join(faltam)}. Nada foi gerado.")
    paginas.sort(key=lambda p: not p["faixas"])  # páginas com destaque primeiro
    a.saida = a.saida.expanduser()
    a.saida.parent.mkdir(parents=True, exist_ok=True)  # cria a pasta do cliente, se faltar
    with tempfile.TemporaryDirectory() as tmp:
        plano = Path(tmp, "plano.json")
        plano.write_text(json.dumps({"saida": str(a.saida.resolve()), "paginas": paginas}), encoding="utf-8")
        r = subprocess.run(["uv", "run", "--no-project", "--quiet", "--with", "pillow==10.4.0", "python", "-c", DESENHAR,
                            str(plano)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("Falha ao desenhar:\n" + r.stderr[-1500:])
    print(f"{a.saida}: {len(paginas)} página(s); destacados: {', '.join(sorted(achados))}")


def _teste():
    linhas = [
        {"texto": "Intimação (111) - Prioridade: Normal - ID do documento (9)", "x": 26, "y": 100, "w": 500, "h": 18},
        {"texto": "Usuário Domicílio Eletrônico registrou ciência em 26/05/2025 20:11:22", "x": 29, "y": 180, "w": 480, "h": 17},
        {"texto": "Citação (222) - Prioridade: Normal - ID do documento (9)", "x": 29, "y": 260, "w": 500, "h": 18},
        {"texto": "O sistema registrou ciência em 27/05/2025 00:00:00", "x": 29, "y": 330, "w": 360, "h": 17},
    ]
    f = faixas(linhas, {"111", "222"}, 2000, 1000)
    assert f["111"]["caixa"] == [16, 88, 1994, 248], f
    assert f["111"]["marcas"] == [[25, 177, 513, 200]]
    assert f["222"]["caixa"][3] == 998 and len(f["222"]["marcas"]) == 1  # último vai até o fim da imagem
    assert faixas(linhas, {"999"}, 2000, 1000) == {}
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
