# Instala ou atualiza a skill de cumprimento provisorio no Claude Code (Windows 10/11). Nao pede senha de administrador.
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/MagnoAguiar11/skill-cumprimento-provisorio/main/instalar.ps1 | iex"
$repo = "https://github.com/MagnoAguiar11/skill-cumprimento-provisorio"
$skills = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME ".claude\skills" }
$destino = Join-Path $skills "cumprimento-provisorio"

Write-Host "== Skill de cumprimento provisorio"
$env:Path = "$HOME\.local\bin;$env:Path"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "== Instalando o uv (ele cuida do Python e das bibliotecas)"
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$HOME\.local\bin;$env:Path"
}

if ((Test-Path $destino) -and (Get-Item $destino).LinkType) {
    Write-Host "A skill ja esta instalada por atalho em $destino (copia de desenvolvimento). Nada foi alterado."
    return
}

$tmp = Join-Path $env:TEMP ("skill-cp-" + [guid]::NewGuid())
New-Item -ItemType Directory $tmp | Out-Null
Write-Host "== Baixando a versao mais recente do GitHub"
Invoke-WebRequest "$repo/archive/refs/heads/main.zip" -OutFile "$tmp\skill.zip" -UseBasicParsing
Expand-Archive "$tmp\skill.zip" $tmp
New-Item -ItemType Directory -Force $skills | Out-Null
if (Test-Path $destino) { Remove-Item -Recurse -Force $destino }
Copy-Item -Recurse "$tmp\skill-cumprimento-provisorio-main\cumprimento-provisorio" $destino
Remove-Item -Recurse -Force $tmp
Write-Host "   instalada em $destino"

# Windows ARM: usa o Python x64 (emulado), que tem todos os pacotes prontos
$py = if ("$env:PROCESSOR_ARCHITECTURE$env:PROCESSOR_ARCHITEW6432" -match "ARM64") { "cpython-3.12-windows-x86_64-none" } else { "3.12" }
Write-Host "== Preparando o Python e as bibliotecas (na primeira vez demora alguns minutos)"
& uv run --no-project --quiet --python $py --with "markitdown[pdf]==0.1.9" --with pypdf==5.1.0 --with pillow==10.4.0 `
    --with pypdfium2==4.30.0 --with python-docx==1.1.2 python -c "print('   bibliotecas prontas')" 2>&1 | Select-Object -Last 1
foreach ($s in "astreintes", "correcao", "ler_processo", "montar_kit", "gerar_docx", "conferir_citacoes", "demonstrativo_pdf", "destacar_expediente") {
    $r = & uv run --no-project --quiet --python $py python "$destino\scripts\$s.py" --teste 2>&1 | Select-Object -Last 1
    Write-Host ("   {0,-22} {1}" -f $s, $r)
}
Write-Host "== Pronto. Abra uma sessao nova do Claude Code, anexe o PDF do processo e os prints da aba Expedientes"
Write-Host "   e peca: ""Faca o cumprimento provisorio deste processo""."
