#!/usr/bin/env bash
# Instala ou atualiza a skill de cumprimento provisório no Claude Code (Mac e Linux). Não pede senha de administrador.
#   curl -fsSL https://raw.githubusercontent.com/MagnoAguiar11/skill-cumprimento-provisorio/main/instalar.sh | bash
set -euo pipefail
REPO="https://github.com/MagnoAguiar11/skill-cumprimento-provisorio"
SKILLS="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DESTINO="$SKILLS/cumprimento-provisorio"

echo "== Skill de cumprimento provisório"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "== Instalando o uv (ele cuida do Python e das bibliotecas)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ -L "$DESTINO" ]; then
  echo "A skill já está instalada por atalho em $DESTINO (cópia de desenvolvimento). Nada foi alterado."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
echo "== Baixando a versão mais recente do GitHub"
curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP"
mkdir -p "$SKILLS"
rm -rf "$DESTINO"
cp -R "$TMP/skill-cumprimento-provisorio-main/cumprimento-provisorio" "$DESTINO"
echo "   instalada em $DESTINO"

echo "== Preparando o Python e as bibliotecas (na primeira vez demora alguns minutos)"
uv run --no-project --quiet --python 3.12 --with "markitdown[pdf]==0.1.9" --with pypdf==5.1.0 --with pillow==10.4.0 \
  --with pypdfium2==4.30.0 --with python-docx==1.1.2 python -c "print('   bibliotecas prontas')"
for s in astreintes correcao ler_processo montar_kit gerar_docx conferir_citacoes demonstrativo_pdf destacar_expediente; do
  printf "   %-22s " "$s"
  uv run --no-project --quiet --python 3.12 python "$DESTINO/scripts/$s.py" --teste 2>&1 | tail -1
done
echo "== Pronto. Abra uma sessão nova do Claude Code, anexe o PDF do processo e os prints da aba Expedientes"
echo "   e peça: \"Faça o cumprimento provisório deste processo\"."
