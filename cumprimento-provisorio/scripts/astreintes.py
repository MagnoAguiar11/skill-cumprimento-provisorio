#!/usr/bin/env python3
"""Prazo para cumprir, dias de descumprimento e valor das astreintes.

Contagem conservadora: na dúvida, considera o dia como não útil e empurra as datas
para frente. A multa sai um pouco menor, mas a conta não dá margem a impugnação.

Exemplos:
  python3 astreintes.py --ciencia 2026-03-02 --prazo 5 --diaria 500 --teto 30000
  python3 astreintes.py --envio-domicilio 2026-02-20 --prazo 48h --diaria 1000 --referencia 12000
  python3 astreintes.py --inicio-multa 2026-03-10 --diaria 500 --mudanca 2026-05-02:1000 --cumprido-em 2026-06-01
  python3 astreintes.py --teste
"""
import argparse
from datetime import date, timedelta
from decimal import Decimal

UM = timedelta(days=1)


def pascoa(ano):
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    return date(ano, mes, (h + l - 7 * m + 114) % 31 + 1)


def nao_util(d, extras):
    if d.weekday() >= 5 or d in extras:
        return True
    fixos = {(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (12, 8), (12, 25)}
    if d.year >= 2024:
        fixos.add((11, 20))  # Lei 14.759/2023
    if (d.month, d.day) in fixos:
        return True
    if (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20):
        return True  # art. 220 do CPC: prazos suspensos de 20/12 a 20/01
    p = pascoa(d.year)
    # Carnaval e Quarta de Cinzas, Quarta/Quinta/Sexta-feira Santa, Corpus Christi
    return (d - p).days in (-48, -47, -46, -4, -3, -2, 60)


def proximo_util(d, extras):
    while nao_util(d, extras):
        d += UM
    return d


def vencimento(ciencia, prazo, corridos, extras):
    """Art. 231, § 3º, e art. 224 do CPC: exclui o dia da comunicação e inclui o do vencimento."""
    if corridos:
        return proximo_util(ciencia + timedelta(days=prazo), extras)
    d, n = ciencia, 0
    while n < prazo:
        d += UM
        if not nao_util(d, extras):
            n += 1
    return d


def brl(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def br(d):
    return d.strftime("%d/%m/%Y")


def calcular(inicio, fim, diaria, mudancas=(), teto=None, referencia=None, extras=frozenset()):
    """Soma a multa dia a dia de inicio a fim (inclusive) e aplica o limite.
    Também soma só os dias úteis, porque o STJ ainda não definiu como contar os dias de multa."""
    tabela = sorted([(inicio, diaria)] + list(mudancas))
    total, dias, d, atingiu = Decimal(0), 0, inicio, None
    total_uteis, dias_uteis = Decimal(0), 0
    while d <= fim:
        valor = [v for (desde, v) in tabela if desde <= d][-1]
        total += valor
        dias += 1
        if not nao_util(d, extras):
            total_uteis += valor
            dias_uteis += 1
        if teto is not None and atingiu is None and total >= teto:
            atingiu = d
        d += UM
    if teto is not None:
        executado = min(total, teto)
        motivo = "teto fixado na decisão" if total > teto else "abaixo do teto da decisão"
    elif referencia is not None and total > referencia:
        executado, motivo = referencia, "limitado ao valor da obrigação principal, sem teto na decisão"
    else:
        executado, motivo = total, "sem limitação"
    return dict(dias=dias, total=total, executado=executado, motivo=motivo, teto_atingido_em=atingiu,
                dias_uteis=dias_uteis, total_uteis=total_uteis)


def _data(s):
    return date.fromisoformat(s)


def _mudanca(s):
    d, v = s.split(":")
    return (_data(d), Decimal(v))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ciencia", type=_data, help="data em que o devedor tomou ciência da decisão (consulta no Domicílio, juntada do mandado etc.)")
    ap.add_argument("--envio-domicilio", type=_data, help="data do envio ao Domicílio Judicial Eletrônico, quando não houve consulta (ciência tácita em 10 dias corridos)")
    ap.add_argument("--prazo", help="prazo para cumprir: número de dias (ex.: 5) ou horas (ex.: 48h)")
    ap.add_argument("--corridos", action="store_true", help="a decisão fixou o prazo em dias corridos")
    ap.add_argument("--inicio-multa", type=_data, help="primeiro dia de multa, quando já conhecido (dispensa ciência e prazo)")
    ap.add_argument("--diaria", type=Decimal, help="valor da multa por dia")
    ap.add_argument("--mudanca", type=_mudanca, action="append", default=[], help="AAAA-MM-DD:VALOR — novo valor diário a partir dessa data (majoração ou redução)")
    ap.add_argument("--cumprido-em", type=_data, help="data em que a obrigação foi cumprida (a multa para no dia anterior)")
    ap.add_argument("--ate", type=_data, default=date.today(), help="último dia de multa, se ainda descumprida (padrão: hoje)")
    ap.add_argument("--teto", type=Decimal, help="limite máximo fixado na decisão")
    ap.add_argument("--referencia", type=Decimal, help="valor da obrigação principal (valor da causa ou do contrato), usado só quando não há teto")
    ap.add_argument("--feriados", default="", help="feriados locais e dias sem expediente, separados por vírgula (AAAA-MM-DD)")
    ap.add_argument("--teste", action="store_true", help="roda a autoverificação")
    a = ap.parse_args()
    if a.teste:
        return _teste()
    extras = {_data(x) for x in a.feriados.split(",") if x.strip()}
    linhas, notas = [], []

    if a.inicio_multa:
        inicio = a.inicio_multa
    else:
        if a.envio_domicilio:
            tacita = a.envio_domicilio + timedelta(days=10)
            ciencia = proximo_util(tacita, extras)
            linhas.append(("Envio ao Domicílio Judicial Eletrônico", br(a.envio_domicilio)))
            linhas.append(("Ciência tácita (10 dias corridos, art. 5º, § 3º, da Lei 11.419/2006)", br(ciencia)))
            if ciencia != tacita:
                notas.append(f"O 10º dia caiu em {br(tacita)}, dia não útil; a conta usou o dia útil seguinte (mais conservador).")
        elif a.ciencia:
            ciencia = proximo_util(a.ciencia, extras)
            linhas.append(("Ciência da decisão pelo devedor", br(ciencia)))
            if ciencia != a.ciencia:
                notas.append(f"A ciência em {br(a.ciencia)} foi em dia não útil; vale o dia útil seguinte (art. 5º, § 2º, da Lei 11.419/2006).")
        else:
            ap.error("informe --ciencia, --envio-domicilio ou --inicio-multa")
        if not a.prazo:
            ap.error("informe --prazo")
        if a.prazo.lower().endswith("h"):
            horas = int(a.prazo[:-1])
            venc = ciencia + timedelta(days=-(-horas // 24))
            linhas.append(("Prazo para cumprir", f"{horas} horas — até {br(venc)}"))
            notas.append("Prazo em horas: a conta arredonda para o dia inteiro seguinte. Confira a hora da ciência no expediente.")
        else:
            n = int(a.prazo)
            venc = vencimento(ciencia, n, a.corridos, extras)
            tipo = "corridos" if a.corridos else "úteis"
            linhas.append(("Prazo para cumprir", f"{n} dias {tipo} — venceu em {br(venc)}"))
            if not a.corridos:
                alt = vencimento(ciencia, n, True, extras)
                if alt < venc:
                    notas.append(f"Em dias corridos o prazo teria vencido em {br(alt)} e a multa começaria {(venc - alt).days} dia(s) antes.")
        inicio = venc + UM

    if a.diaria is None:
        for k, v in linhas:
            print(f"{k}: {v}")
        print(f"Multa começa a correr em: {br(inicio)}")
        return
    fim = a.cumprido_em - UM if a.cumprido_em else a.ate
    r = calcular(inicio, fim, a.diaria, a.mudanca, a.teto, a.referencia, extras)
    if r["dias_uteis"] != r["dias"]:
        notas.append(f"Se cada dia de multa contasse só em dia útil: {r['dias_uteis']} dias, {brl(r['total_uteis'])} acumulados.")

    linhas.append(("Multa corre de", f"{br(inicio)} a {br(fim)}" + (f" (cumprida em {br(a.cumprido_em)})" if a.cumprido_em else "")))
    linhas.append(("Dias de descumprimento", str(r["dias"])))
    linhas.append(("Multa diária", brl(a.diaria) + "".join(f"; {brl(v)} a partir de {br(d)}" for d, v in sorted(a.mudanca))))
    linhas.append(("Total acumulado", brl(r["total"])))
    if a.teto is not None:
        linhas.append(("Teto fixado na decisão", brl(a.teto) + (f" — atingido em {br(r['teto_atingido_em'])}" if r["teto_atingido_em"] else "")))
    elif a.referencia is not None:
        linhas.append(("Valor da obrigação principal", brl(a.referencia)))
    linhas.append(("Valor executado", f"{brl(r['executado'])} ({r['motivo']})"))

    print("| Item | Valor |\n|---|---|")
    for k, v in linhas:
        print(f"| {k} | {v} |")
    if notas:
        print()
        for n in notas:
            print(f"- {n}")
    print("\n- Valores nominais, sem correção monetária nem juros.")
    print("- Contagem conservadora: fins de semana, feriados nacionais, 08/12, Carnaval e Quarta de Cinzas, Quarta a Sexta-feira Santa, Corpus Christi e 20/12 a 20/01 contam como não úteis. Feriados locais só entram com --feriados.")


def _teste():
    x = set()
    assert pascoa(2026) == date(2026, 4, 5) and pascoa(2027) == date(2027, 3, 28)
    assert nao_util(date(2026, 2, 17), x) and nao_util(date(2026, 6, 4), x)  # Carnaval, Corpus Christi
    assert nao_util(date(2026, 11, 20), x) and not nao_util(date(2023, 11, 20), x)
    # 5 dias úteis a partir de segunda 02/03/2026: vence segunda 09/03
    assert vencimento(date(2026, 3, 2), 5, False, x) == date(2026, 3, 9)
    # 5 corridos caem no sábado 07/03 -> segunda 09/03
    assert vencimento(date(2026, 3, 2), 5, True, x) == date(2026, 3, 9)
    # recesso: ciência 18/12/2026 -> 21, 22, 25, 26 e 27/01/2027
    assert vencimento(date(2026, 12, 18), 5, False, x) == date(2027, 1, 27)
    # feriado local informado pelo usuário
    assert vencimento(date(2026, 3, 2), 5, False, {date(2026, 3, 5)}) == date(2026, 3, 10)
    # 10 dias de R$ 500 = 5.000; teto 3.000 atingido no 6º dia
    r = calcular(date(2026, 3, 10), date(2026, 3, 19), Decimal(500), teto=Decimal(3000))
    assert r["dias"] == 10 and r["total"] == 5000 and r["executado"] == 3000 and r["teto_atingido_em"] == date(2026, 3, 15)
    # 10/03 (ter) a 19/03 (qui): 8 dias úteis
    assert r["dias_uteis"] == 8 and r["total_uteis"] == 4000
    # majoração em 15/03: 5 x 500 + 5 x 1.000
    r = calcular(date(2026, 3, 10), date(2026, 3, 19), Decimal(500), [(date(2026, 3, 15), Decimal(1000))])
    assert r["total"] == 7500 and r["executado"] == 7500
    # sem teto e acima da obrigação principal: limita à referência
    r = calcular(date(2026, 3, 10), date(2026, 3, 19), Decimal(500), referencia=Decimal(4000))
    assert r["executado"] == 4000 and "obrigação principal" in r["motivo"]
    # cumprida antes de vencer: zero dias
    assert calcular(date(2026, 3, 10), date(2026, 3, 9), Decimal(500))["dias"] == 0
    assert brl(Decimal("1234567.5")) == "R$ 1.234.567,50"
    print("ok: todos os testes passaram")


if __name__ == "__main__":
    main()
