#!/usr/bin/env python3
"""Demonstrativo de atualização com o número-índice oficial (modelo de estrutura-da-peca.md, seção 6).

Fator = índice final ÷ índice-base. Mês-base = mês anterior ao do pagamento.
Índice final = último número-índice publicado (ou --final AAAA-MM).
Números-índice do Ipeadata; o encadeamento é conferido com as variações mensais do SGS/Banco Central.

  python3 correcao.py --indice incc-di --pagamentos pagamentos.csv --percentual 75 \
      --excluidos "o desconto de R$ 10.000,00 (item 5 do extrato)" -o demonstrativo.md
  python3 correcao.py --teste

pagamentos.csv (separador ;):  nº;parcela;data;valor   ex.: 1;Entrada 001;24/10/2021;1.000,00
"""
import argparse
import csv
import json
import sys
import urllib.request
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

# Código Ipeadata (número-índice), código SGS (variação % mensal), fonte, casas do número-índice.
# Conferidos em 19/11/2026: nomes oficiais no Ipeadata; SGS 192 bate com o INCC-DI do Ipeadata.
INDICES = {
    "incc-di": ("IGP12_INCC12", 192, "FGV, INCC-DI (ago/1994 = 100)", 3),
    "igp-m": ("IGP12_IGPM12", 189, "FGV, IGP-M (ago/1994 = 100)", 3),
    "ipca": ("PRECOS12_IPCA12", 433, "IBGE, IPCA (dez/1993 = 100)", 2),
    "inpc": ("PRECOS12_INPC12", 188, "IBGE, INPC (dez/1993 = 100)", 2),
}
MESES = "jan fev mar abr mai jun jul ago set out nov dez".split()


def _get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)


def baixar_indices(codigo):
    dados = _get(f"http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{codigo}')")["value"]
    return {x["VALDATA"][:7]: Decimal(str(x["VALVALOR"])) for x in dados if x["VALVALOR"] is not None}


def baixar_variacoes(sgs, desde):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{sgs}/dados?formato=json&dataInicial=01/{desde[5:]}/{desde[:4]}"
    return {f"{x['data'][6:]}-{x['data'][3:5]}": Decimal(x["valor"]) for x in _get(url)}


def mes_anterior(m):
    a, b = int(m[:4]), int(m[5:])
    return f"{a - 1}-12" if b == 1 else f"{a}-{b - 1:02d}"


def rotulo(m):
    return f"{MESES[int(m[5:]) - 1]}/{m[:4]}"


def brl(v, casas=2):
    q = Decimal(1).scaleb(-casas)
    s = f"{Decimal(v).quantize(q, ROUND_HALF_UP):,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def ler_pagamentos(caminho):
    out = []
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.reader(f, delimiter=";"):
            if not linha or linha[0].strip().lower() in ("nº", "n", "no", "#"):
                continue
            n, parcela, data, valor = [c.strip() for c in linha[:4]]
            d, m, a = data.split("/")
            out.append((n, parcela, date(int(a), int(m), int(d)), Decimal(valor.replace(".", "").replace(",", "."))))
    return out


def calcular(pagamentos, indices, final):
    linhas, acumulado = [], Decimal(0)
    i_final = indices[final]
    for n, parcela, data, valor in pagamentos:
        base = mes_anterior(f"{data.year}-{data.month:02d}")
        fator = (i_final / indices[base]).quantize(Decimal("0.000001"), ROUND_HALF_UP)
        corrigido = (valor * fator).quantize(Decimal("0.01"), ROUND_HALF_UP)
        acumulado += corrigido
        linhas.append(dict(n=n, parcela=parcela, data=data, valor=valor, base=base, i_base=indices[base], fator=fator,
                           corrigido=corrigido, acumulado=acumulado))
    return linhas


def conferir(pagamentos, linhas, indices, variacoes, final):
    """Devolve a lista de avisos; vazia quando tudo fecha."""
    avisos = []
    for p, l in zip(pagamentos, linhas):  # recálculo independente, linha a linha
        esperado = mes_anterior(f"{p[2].year}-{p[2].month:02d}")
        if l["base"] != esperado:
            avisos.append(f"Nº {l['n']}: mês-base {l['base']} não é o mês anterior ao pagamento")
        if (p[3] * l["fator"]).quantize(Decimal("0.01"), ROUND_HALF_UP) != l["corrigido"]:
            avisos.append(f"Nº {l['n']}: valor corrigido não fecha")
    soma = Decimal(0)
    for l in linhas:
        soma += l["corrigido"]
        if soma != l["acumulado"]:
            avisos.append(f"Nº {l['n']}: acumulado não fecha")
    m = min(l["base"] for l in linhas)
    while m != final:  # encadeamento: índice do mês = índice anterior × (1 + variação)
        prox = f"{int(m[:4]) + (m[5:] == '12')}-{(int(m[5:]) % 12) + 1:02d}"
        if prox in variacoes and prox in indices:
            calc = (indices[prox] / indices[m] - 1) * 100
            if abs(calc - variacoes[prox]) > Decimal("0.011"):
                avisos.append(f"{rotulo(prox)}: variação pelo número-índice {calc:.2f}% diferente da variação publicada {variacoes[prox]}%")
        elif prox in indices:
            avisos.append(f"{rotulo(prox)}: sem variação publicada para conferir")
        m = prox
    meses = [(p[2].year, p[2].month) for p in pagamentos]
    for mes in sorted(set(x for x in meses if meses.count(x) > 1)):
        avisos.append(f"Extrato: mais de um pagamento em {MESES[mes[1] - 1]}/{mes[0]}")
    for a, b in zip(pagamentos, pagamentos[1:]):
        if b[2] < a[2]:
            avisos.append(f"Extrato: Nº {b[0]} ({b[2]:%d/%m/%Y}) tem data anterior ao Nº {a[0]} ({a[2]:%d/%m/%Y})")
    for p in pagamentos:
        if p[3] <= 0:
            avisos.append(f"Extrato: Nº {p[0]} tem valor negativo ou zero")
    return avisos


def montar(linhas, nome, casas, final, i_final, fonte, excluidos, percentual, origem=""):
    total_pago = sum(l["valor"] for l in linhas)
    total = linhas[-1]["acumulado"]
    md = [
        "**Método.** Somente as parcelas efetivamente pagas. "
        + (f"Índice: {nome}, fixado na {origem}. " if origem else "")
        + f"Fator = índice {nome} de {rotulo(final)} ({brl(i_final, casas)}) "
        "÷ índice-base (mês anterior ao do pagamento); valor corrigido = valor pago × fator. "
        "O acumulado soma o valor corrigido de cada parcela ao das anteriores.",
        "",
        f"**O que ficou fora e por quê.** {excluidos}" if excluidos else "**O que ficou fora e por quê.** Nada: todos os lançamentos do extrato são pagamentos.",
        "",
        f"**Fonte dos índices.** {fonte}.",
        "",
        "| Nº | Parcela | Data do pagamento | Valor pago | Mês-base | Índice-base | Fator | Valor corrigido | Acumulado corrigido |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for l in linhas:
        md.append(f"| {l['n']} | {l['parcela']} | {l['data']:%d/%m/%Y} | {brl(l['valor'])} | {rotulo(l['base'])} | "
                  f"{brl(l['i_base'], casas)} | {brl(l['fator'], 6)} | {brl(l['corrigido'])} | **{brl(l['acumulado'])}** |")
    md.append(f"| | **Total** | | **{brl(total_pago)}** | | | | **{brl(total)}** | **{brl(total)}** |")
    if percentual:
        pct = Decimal(percentual)
        md += ["", f"**{brl(pct, 0)}% do total corrigido:** R$ {brl(total * pct / 100)} "
                   f"(nominal: {brl(pct, 0)}% de R$ {brl(total_pago)} = R$ {brl(total_pago * pct / 100)})."]
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--indice", choices=sorted(INDICES))
    ap.add_argument("--pagamentos")
    ap.add_argument("--final", help="mês do índice final (AAAA-MM); padrão: o último publicado")
    ap.add_argument("--percentual", help="aplica um percentual ao total corrigido (ex.: 75)")
    ap.add_argument("--excluidos", default="", help="frase dizendo o que ficou fora do cálculo e por quê")
    ap.add_argument("--origem", default="", help='onde o índice foi fixado, ex.: "decisão de tutela (ID 12345678)"')
    ap.add_argument("-o", "--saida")
    ap.add_argument("--teste", action="store_true")
    a = ap.parse_args()
    if a.teste:
        return _teste()
    if not (a.indice and a.pagamentos):
        ap.error("informe --indice e --pagamentos")
    codigo, sgs, nome_fonte, casas = INDICES[a.indice]
    pagamentos = ler_pagamentos(a.pagamentos)
    indices = baixar_indices(codigo)
    final = a.final or max(indices)
    desde = mes_anterior(min(f"{p[2].year}-{p[2].month:02d}" for p in pagamentos))
    variacoes = baixar_variacoes(sgs, desde)
    linhas = calcular(pagamentos, indices, final)
    fonte = (f"{nome_fonte}, número-índice publicado no Ipeadata (série {codigo}, "
             f"http://www.ipeadata.gov.br); variações mensais conferidas com a série {sgs} do SGS/Banco Central")
    md = montar(linhas, a.indice.upper(), casas, final, indices[final], fonte, a.excluidos, a.percentual, a.origem)
    avisos = conferir(pagamentos, linhas, indices, variacoes, final)
    if a.saida:
        open(a.saida, "w", encoding="utf-8").write(md + "\n")
    print(md)
    print("\nCONFERÊNCIA: " + ("tudo fecha." if not avisos else f"{len(avisos)} aviso(s):"), file=sys.stderr)
    for x in avisos:
        print(" - " + x, file=sys.stderr)


def _teste():
    idx = {"2021-09": Decimal("100.00"), "2021-10": Decimal("101.00"), "2021-11": Decimal("102.01"), "2021-12": Decimal("103.03")}
    var = {"2021-10": Decimal("1.00"), "2021-11": Decimal("1.00"), "2021-12": Decimal("1.00")}
    pg = [("1", "Entrada", date(2021, 10, 24), Decimal("1000.00")), ("2", "Parcela", date(2021, 11, 15), Decimal("500.00")),
          ("3", "Parcela", date(2021, 11, 10), Decimal("500.00"))]
    linhas = calcular(pg, idx, "2021-12")
    assert linhas[0]["base"] == "2021-09" and linhas[0]["fator"] == Decimal("1.030300") and linhas[0]["corrigido"] == Decimal("1030.30")
    assert linhas[1]["base"] == "2021-10" and linhas[1]["fator"] == Decimal("1.020099") and linhas[1]["corrigido"] == Decimal("510.05")
    assert linhas[2]["acumulado"] == Decimal("1030.30") + Decimal("510.05") * 2
    av = conferir(pg, linhas, idx, var, "2021-12")
    assert any("mais de um pagamento em nov/2021" in x for x in av) and any("data anterior" in x for x in av)
    assert not any("variação" in x for x in av), av
    av2 = conferir(pg, linhas, idx, {**var, "2021-11": Decimal("2.00")}, "2021-12")
    assert any("nov/2021: variação" in x for x in av2)  # índice que não fecha é apontado
    md = montar(linhas, "INCC-DI", 2, "2021-12", idx["2021-12"], "teste", "", "75")
    assert "| 1 | Entrada | 24/10/2021 | 1.000,00 | set/2021 | 100,00 | 1,030300 | 1.030,30 | **1.030,30** |" in md
    assert "75% do total corrigido:** R$ 1.537,80" in md
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
