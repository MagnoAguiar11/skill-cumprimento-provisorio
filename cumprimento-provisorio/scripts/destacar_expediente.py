#!/usr/bin/env python3
"""Destaca, nos prints da aba "Expedientes" do PJe, a linha de cada expediente pedido e gera um PDF.

Lê o texto do print com o OCR do próprio sistema, sem instalar nada: no Mac, o Vision (ocr_linhas.swift);
no Windows 10/11, o Windows.Media.Ocr (ocr_linhas.ps1). No Linux, o RapidOCR, que scripts/ambiente.py instala sozinho.
A linha do expediente vai do título "Intimação (N) - Prioridade..." até o título do expediente
seguinte; ela recebe fundo amarelo e borda vermelha, e a frase da ciência ("... registrou ciência
em ...") recebe marca-texto. As páginas com destaque vêm primeiro; as demais seguem na ordem dada.

  python3 destacar_expediente.py print1.png print2.png --expediente 1234567 --expediente 1234568 \
      -o "Aba Expedientes - 0000123-45.2025.pdf"
  python3 destacar_expediente.py --teste
(no Windows, use "python" ou "py" no lugar de "python3")
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

import ambiente  # acha o uv (mesmo fora do PATH) ou o Python próprio da skill
from ambiente import UTF8

AQUI = Path(__file__).resolve().parent
TITULO = re.compile(r"^[a-z]+\((\d+)\)-prioridade")  # texto normalizado: "intimacao(1234567)-prioridade:normal..."
RAPIDOCR = ["rapidocr_onnxruntime==1.3.24", "pillow==10.4.0"]

LER = r'''
import json, sys
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
img = Image.open(sys.argv[1]).convert("RGB")
print(json.dumps({"largura": img.width, "altura": img.height}))
res, _ = RapidOCR()(np.array(img)[:, :, ::-1])
for caixa, texto, _conf in res or []:
    xs, ys = [p[0] for p in caixa], [p[1] for p in caixa]
    print(json.dumps({"texto": texto, "x": int(min(xs)), "y": int(min(ys)), "w": int(max(xs) - min(xs)), "h": int(max(ys) - min(ys))}))
'''

DESENHAR = r'''
import json, sys
from PIL import Image, ImageDraw
plano = json.load(open(sys.argv[1], encoding="utf-8"))
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


def norm(t):
    """Sem acento, sem espaço e em minúsculas: o OCR do Windows lê "Intimacao(1234567)-Prioridade"."""
    t = unicodedata.normalize("NFKD", t)  # também troca os parênteses largos "（" por "("
    return re.sub(r"\s+", "", "".join(c for c in t if not unicodedata.combining(c))).lower()


def ocr(imagem, motor="auto"):
    """(linhas de texto, largura, altura) do print."""
    if motor == "auto":
        motor = "vision" if sys.platform == "darwin" and shutil.which("swift") else "windows" if os.name == "nt" else "rapidocr"
    if motor == "vision":
        cmd = ["swift", str(AQUI / "ocr_linhas.swift"), str(imagem)]
    elif motor == "windows":
        local = Path(tempfile.mkdtemp()) / ("print" + Path(imagem).suffix)  # o OCR do Windows só abre arquivo local
        shutil.copyfile(imagem, local)
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(AQUI / "ocr_linhas.ps1"), str(local)]
    else:
        cmd = None
    if cmd:
        r = subprocess.run(cmd, capture_output=True, **UTF8)
    else:
        try:
            r = ambiente.rodar(RAPIDOCR, ["-c", LER, str(imagem)])
        except ambiente.SemAmbiente as e:
            ambiente.falhar(e)
    if r.returncode != 0:
        sys.exit(f"Falha no OCR de {imagem}:\n{r.stderr[-1500:]}")
    dados = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    tam = next(d for d in dados if "largura" in d)
    return [d for d in dados if "texto" in d], tam["largura"], tam["altura"]


def faixas(linhas, expedientes, largura, altura):
    """Caixa de cada expediente pedido e marcas nas frases de ciência. Devolve {nº: faixa}."""
    titulos = sorted((l for l in linhas if TITULO.match(norm(l["texto"]))), key=lambda l: l["y"])
    out = {}
    for i, t in enumerate(titulos):
        n = TITULO.match(norm(t["texto"])).group(1)
        if n not in expedientes:
            continue
        topo = max(t["y"] - 12, 0)
        fim = titulos[i + 1]["y"] - 12 if i + 1 < len(titulos) else altura - 2
        marcas = [[l["x"] - 4, l["y"] - 3, l["x"] + l["w"] + 4, l["y"] + l["h"] + 3]
                  for l in linhas if "cienciaem" in norm(l["texto"]) and topo <= l["y"] < fim]
        out[n] = {"caixa": [max(t["x"] - 10, 2), topo, largura - 6, fim], "marcas": marcas}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("imagens", nargs="*", type=Path)
    ap.add_argument("--expediente", action="append", default=[], help="número do expediente (repita para vários)")
    ap.add_argument("-o", "--saida", type=Path)
    ap.add_argument("--ocr", choices=["auto", "vision", "windows", "rapidocr"], default="auto",
                    help="auto: Vision no Mac, OCR do Windows no Windows, RapidOCR no Linux")
    ap.add_argument("--teste", action="store_true")
    a = ap.parse_args()
    if a.teste:
        return _teste()
    if not (a.imagens and a.expediente and a.saida):
        ap.error("informe os prints, ao menos um --expediente e -o saída.pdf")
    paginas, achados = [], set()
    for img in a.imagens:
        linhas, largura, altura = ocr(img, a.ocr)
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
        try:
            r = ambiente.rodar(["pillow==10.4.0"], ["-c", DESENHAR, str(plano)])
        except ambiente.SemAmbiente as e:
            ambiente.falhar(e)
        if r.returncode != 0:
            sys.exit("Falha ao desenhar:\n" + r.stderr[-1500:])
    print(f"{a.saida}: {len(paginas)} página(s); destacados: {', '.join(sorted(achados))}")


def _teste():
    linhas = [  # como o Vision do Mac lê
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
    rapido = [  # como o RapidOCR (Windows) lê: sem acento, sem espaço, parêntese largo
        {"texto": "Intimacao（111)-Prioridade:Normal-IDdodocumento（9)", "x": 26, "y": 100, "w": 500, "h": 18},
        {"texto": "UsuarioDomicilioEletronicoregistroucienciaem26/05/202520:11:22", "x": 29, "y": 180, "w": 480, "h": 17},
        {"texto": "Citacao(222)-Prioridade:Normal-IDdodocumento(9)", "x": 29, "y": 260, "w": 500, "h": 18},
    ]
    assert faixas(rapido, {"111"}, 2000, 1000) == {"111": f["111"]}
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
