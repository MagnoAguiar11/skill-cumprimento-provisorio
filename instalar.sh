#!/usr/bin/env bash
# Instala ou atualiza a skill de cumprimento provisório no Claude Code (Mac e Linux). Não pede senha de administrador.
#   curl -fsSL https://raw.githubusercontent.com/MagnoAguiar11/skill-cumprimento-provisorio/main/instalar.sh | bash
# Rodado de dentro de uma cópia do repositório (bash instalar.sh), instala a partir dela, sem baixar de novo.
#
# O uv é o caminho preferido (traz o Python 3.12). Se ele não instalar (rede que bloqueia o site dele, por exemplo),
# a skill segue com um Python próprio, montado com o python3 do computador. O resultado sai na última linha.
set -uo pipefail

principal() {
  REPO="https://github.com/MagnoAguiar11/skill-cumprimento-provisorio"
  SKILLS="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
  DESTINO="$SKILLS/cumprimento-provisorio"
  CACHE="${CUMPRIMENTO_AMBIENTE:-${XDG_CACHE_HOME:-$HOME/.cache}/skill-cumprimento-provisorio}"
  mkdir -p "$CACHE"
  LOG="$CACHE/instalacao.log"
  : > "$LOG"
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT

  falhou() {
    echo
    echo "RESULTADO: FALHOU. $*"
    echo "   Detalhes em $LOG"
    exit 1
  }

  echo "== Skill de cumprimento provisório"

  # 1. A skill (primeiro, porque o resto usa os scripts dela)
  ORIGEM=""
  if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "$(dirname "${BASH_SOURCE[0]}")/cumprimento-provisorio/SKILL.md" ]; then
    ORIGEM="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cumprimento-provisorio"
  fi
  if [ -L "$DESTINO" ]; then
    echo "== A skill está instalada por atalho em $DESTINO (cópia de desenvolvimento): os arquivos não foram trocados."
  else
    if [ -z "$ORIGEM" ]; then
      echo "== Baixando a versão mais recente do GitHub"
      curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" -o "$TMP/skill.tar.gz" >>"$LOG" 2>&1 \
        || falhou "Não consegui baixar a skill do GitHub. Confira a internet e rode de novo."
      tar -xzf "$TMP/skill.tar.gz" -C "$TMP" >>"$LOG" 2>&1 || falhou "O arquivo baixado do GitHub veio corrompido. Rode de novo."
      ORIGEM="$TMP/skill-cumprimento-provisorio-main/cumprimento-provisorio"
    else
      echo "== Instalando a partir da cópia local: $ORIGEM"
    fi
    mkdir -p "$SKILLS" && rm -rf "$DESTINO" && cp -R "$ORIGEM" "$DESTINO" \
      || falhou "Não consegui copiar a skill para $DESTINO."
    echo "   instalada em $DESTINO"
  fi

  # 2. O uv. O instalador dele só muda o PATH dos terminais abertos depois, por isso a busca olha as pastas de costume.
  achar_uv() {
    local c
    for c in "$(command -v uv 2>/dev/null)" "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv" /opt/homebrew/bin/uv /usr/local/bin/uv \
             "$HOME"/Library/Python/3.*/bin/uv; do
      if [ -n "$c" ] && [ -x "$c" ]; then echo "$c"; return 0; fi
    done
    return 1
  }

  # python3 que funciona de verdade. No Mac sem as Ferramentas de Linha de Comando, /usr/bin/python3 só abre uma janela.
  achar_python() {
    local p
    p="$(command -v python3 2>/dev/null)" || return 1
    if [ "$(uname)" = "Darwin" ] && [ "$p" = "/usr/bin/python3" ] && ! xcode-select -p >/dev/null 2>&1; then return 1; fi
    "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1 && echo "$p"
  }

  UV="$(achar_uv)" || UV=""
  if [ -n "$UV" ]; then
    echo "== uv já instalado: $UV"
  else
    echo "== Instalando o uv (ele cuida do Python e das bibliotecas)"
    { curl -fsSL https://astral.sh/uv/install.sh -o "$TMP/uv.sh" && sh "$TMP/uv.sh"; } >>"$LOG" 2>&1
    UV="$(achar_uv)" || UV=""
    if [ -z "$UV" ] && command -v brew >/dev/null 2>&1; then
      echo "   o instalador oficial do uv não funcionou; tentando pelo Homebrew"
      HOMEBREW_NO_AUTO_UPDATE=1 brew install uv >>"$LOG" 2>&1
      UV="$(achar_uv)" || UV=""
    fi
    PY="$(achar_python)" || PY=""
    if [ -z "$UV" ] && [ -n "$PY" ]; then
      echo "   tentando pelo pip"
      "$PY" -m pip install --user --disable-pip-version-check -q uv >>"$LOG" 2>&1
      UV="$(achar_uv)" || UV=""
    fi
    if [ -n "$UV" ]; then
      echo "   uv instalado em $UV"
    else
      echo "   o uv não instalou (motivo no log). Sigo sem ele, com um Python próprio da skill."
    fi
  fi

  # 3. O Python que roda os scripts e as bibliotecas
  PY="$(achar_python)" || PY=""
  if [ -n "$PY" ]; then
    RODAR=("$PY")
    COMO="python3"
  elif [ -n "$UV" ]; then
    RODAR=("$UV" run --no-project --quiet --python 3.12 python)
    COMO="$UV run --no-project --python 3.12 python"
  else
    if [ "$(uname)" = "Darwin" ]; then
      falhou "Este Mac não tem Python e o uv não instalou. Rode no Terminal: xcode-select --install (instala o Python da Apple, sem senha) e depois rode este instalador de novo."
    fi
    falhou "Este computador não tem python3 (3.8 ou mais novo) e o uv não instalou. Instale o python3 e rode de novo."
  fi

  echo "== Preparando o Python e as bibliotecas (na primeira vez demora alguns minutos)"
  "${RODAR[@]}" "$DESTINO/scripts/ambiente.py" 2>&1 | tee -a "$LOG" | sed 's/^/   /'
  [ "${PIPESTATUS[0]}" -eq 0 ] || falhou "O Python da skill não ficou pronto (motivo acima)."

  # 4. Testes
  echo "== Testando os scripts"
  ERROS=0
  for s in astreintes correcao ler_processo montar_kit gerar_docx conferir_citacoes demonstrativo_pdf destacar_expediente; do
    printf "   %-22s " "$s"
    saida="$("${RODAR[@]}" "$DESTINO/scripts/$s.py" --teste 2>&1)"
    cod=$?
    echo "$saida" | tail -1
    if [ $cod -ne 0 ]; then
      ERROS=$((ERROS + 1))
      printf '\n--- %s --teste\n%s\n' "$s" "$saida" >>"$LOG"
    fi
  done
  [ $ERROS -eq 0 ] || falhou "$ERROS teste(s) não passaram."

  echo "== Para rodar os scripts neste computador: $COMO scripts/<script>.py"
  echo "== Pronto. Abra uma sessão nova do Claude Code, anexe o PDF do processo e os prints da aba Expedientes"
  echo "   e peça: \"Faça o cumprimento provisório deste processo\"."
  echo "RESULTADO: OK"
}

# A função inteira é lida antes de rodar; a entrada fechada impede que um programa filho leia o resto do script.
principal "$@" </dev/null
