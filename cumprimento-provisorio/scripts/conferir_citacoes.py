#!/usr/bin/env python3
"""Confere se cada trecho entre aspas nas citações (linhas "> ") da petição existe, palavra por palavra, nas fontes.

Fontes: references/dispositivos.md, o processo.md e o texto dos julgados lidos com ler_processo.py.
Trechos separados por "[...]" são conferidos um a um; o número do artigo, parágrafo ou item no início é ignorado.
Aspas, travessões, hifenização de fim de linha e espaços são normalizados.

  python3 conferir_citacoes.py peticao.md ../references/dispositivos.md processo.md julgado1.md julgado2.md
  python3 conferir_citacoes.py --teste
"""
import re
import sys


def norm(t):
    t = t.replace("**", "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[–—]", "-", t).replace("°", "º")
    t = re.sub(r"-\s*\n\s*", "", t)
    return re.sub(r"\s+", " ", t)


def conferir(peticao, fontes):
    """Devolve (total de trechos, trechos sem correspondência)."""
    base = norm(" ".join(fontes)).replace("> ", " ")
    total, ruins = 0, []
    for linha in peticao.splitlines():
        if not linha.startswith(">"):
            continue
        q = re.findall(r'"(.+)"', linha)
        if not q:
            continue
        for frag in re.split(r"\s*\[\.\.\.\]\s*", q[0]):
            frag = re.sub(r"^(Art\. [\d.]+º?\.?|\d+\.|§ \d+º|[IVX]+ -)\s*", "", norm(frag).strip(' ,.;"'))
            if len(frag) < 20:
                continue
            total += 1
            if frag not in base:
                ruins.append(frag)
    return total, ruins


def main():
    if sys.argv[1:] == ["--teste"]:
        return _teste()
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    peticao = open(sys.argv[1], encoding="utf-8").read()
    total, ruins = conferir(peticao, [open(f, encoding="utf-8").read() for f in sys.argv[2:]])
    for r in ruins:
        print("NÃO ACHEI: " + r[:160])
    print(f"{total} trechos conferidos; {len(ruins)} sem correspondência")
    sys.exit(1 if ruins else 0)


def _teste():
    fonte = "> Art. 537. [...]\n> § 3º A decisão que fixa a multa é passível de cumprimento provisório, devendo ser depositada em juízo."
    ok = '> "Art. 537. [...] § 3º A decisão que fixa a multa é passível de cumprimento provisório, devendo ser depositada em juízo."'
    errado = '> "Art. 537. [...] § 3º A decisão que fixa a multa é sempre passível de cumprimento provisório."'
    assert conferir(ok, [fonte]) == (1, [])
    total, ruins = conferir(errado, [fonte])
    assert total == 1 and len(ruins) == 1
    assert conferir('> "trecho com **negrito** que existe na fonte, sim"', ["trecho com negrito que existe na fonte, sim"])[1] == []
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
