# Instala ou atualiza a skill de cumprimento provisorio no Claude Code (Windows 10/11). Nao pede senha de administrador.
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/MagnoAguiar11/skill-cumprimento-provisorio/main/instalar.ps1 | iex"
# Rodado de dentro de uma copia do repositorio (powershell -ExecutionPolicy Bypass -File instalar.ps1), instala a partir dela.
#
# O uv e o caminho preferido (traz o Python 3.12). Se ele nao instalar (rede que bloqueia o site dele, por exemplo),
# a skill segue com o Python do computador (py ou python). O resultado sai na ultima linha.

function Achar-Uv {
    # O instalador do uv so muda o PATH dos terminais abertos depois; por isso a busca olha as pastas de costume.
    $cands = @()
    $cmd = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { $cands += $cmd.Source }
    $cands += (Join-Path $HOME ".local\bin\uv.exe"), (Join-Path $HOME ".cargo\bin\uv.exe"), (Join-Path $HOME "scoop\shims\uv.exe")
    if ($env:LOCALAPPDATA) { $cands += (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\uv.exe") }
    if ($env:APPDATA) {
        $cands += @(Get-ChildItem (Join-Path $env:APPDATA "Python\Python3*\Scripts\uv.exe") -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending | ForEach-Object { $_.FullName })
    }
    foreach ($c in $cands) { if ($c -and (Test-Path $c -PathType Leaf)) { return $c } }
    return $null
}

function Achar-Python {
    # py (lancador do python.org) ou um python.exe de verdade; o "python" da pasta WindowsApps so abre a Microsoft Store.
    $teste = "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
    if (Get-Command py -CommandType Application -ErrorAction SilentlyContinue) {
        & py -3 -c $teste 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return , @("py", "-3") }
    }
    foreach ($n in "python", "python3") {
        $c = Get-Command $n -CommandType Application -ErrorAction SilentlyContinue |
            Where-Object { $_.Source -notlike "*WindowsApps*" } | Select-Object -First 1
        if ($c) {
            & $c.Source -c $teste 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return , @($c.Source) }
        }
    }
    return $null
}

function Rodar($cmd, [string[]]$resto) {
    # Roda o Python escolhido (uv run ... python, py -3 ou python.exe) e devolve as linhas da saida como texto.
    $exe = $cmd[0]
    $pre = @($cmd | Select-Object -Skip 1)
    & $exe @pre @resto 2>&1 | ForEach-Object { "$_" }
}

function Anotar($texto) { Add-Content -Path $script:log -Value $texto -Encoding UTF8 }

function Falhou($msg) {
    Write-Host ""
    Write-Host "RESULTADO: FALHOU. $msg"
    Write-Host "   Detalhes em $script:log"
}

function Instalar {
    $repo = "https://github.com/MagnoAguiar11/skill-cumprimento-provisorio"
    $skills = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME ".claude\skills" }
    $destino = Join-Path $skills "cumprimento-provisorio"
    $cache = if ($env:CUMPRIMENTO_AMBIENTE) { $env:CUMPRIMENTO_AMBIENTE } else { Join-Path $env:LOCALAPPDATA "skill-cumprimento-provisorio" }
    New-Item -ItemType Directory -Force $cache | Out-Null
    $script:log = Join-Path $cache "instalacao.log"
    Set-Content -Path $script:log -Value "" -Encoding UTF8
    $env:PYTHONUTF8 = "1"
    try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }  # acentos da saida do Python

    Write-Host "== Skill de cumprimento provisorio"

    # 1. A skill (primeiro, porque o resto usa os scripts dela)
    $origem = $null
    if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "cumprimento-provisorio\SKILL.md"))) {
        $origem = Join-Path $PSScriptRoot "cumprimento-provisorio"
    }
    if ((Test-Path $destino) -and (Get-Item $destino).LinkType) {
        Write-Host "== A skill esta instalada por atalho em $destino (copia de desenvolvimento): os arquivos nao foram trocados."
    } else {
        $tmp = Join-Path $env:TEMP ("skill-cp-" + [guid]::NewGuid())
        New-Item -ItemType Directory $tmp | Out-Null
        try {
            if (-not $origem) {
                Write-Host "== Baixando a versao mais recente do GitHub"
                try {
                    Invoke-WebRequest "$repo/archive/refs/heads/main.zip" -OutFile "$tmp\skill.zip" -UseBasicParsing
                    Expand-Archive "$tmp\skill.zip" $tmp
                } catch {
                    Anotar "$_"
                    Falhou "Nao consegui baixar a skill do GitHub. Confira a internet e rode de novo."
                    return
                }
                $origem = "$tmp\skill-cumprimento-provisorio-main\cumprimento-provisorio"
            } else {
                Write-Host "== Instalando a partir da copia local: $origem"
            }
            try {
                New-Item -ItemType Directory -Force $skills | Out-Null
                if (Test-Path $destino) { Remove-Item -Recurse -Force $destino }
                Copy-Item -Recurse $origem $destino
            } catch {
                Anotar "$_"
                Falhou "Nao consegui copiar a skill para $destino."
                return
            }
        } finally {
            Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
        }
        Write-Host "   instalada em $destino"
    }

    # 2. O uv
    $uv = Achar-Uv
    if ($uv) {
        Write-Host "== uv ja instalado: $uv"
    } else {
        Write-Host "== Instalando o uv (ele cuida do Python e das bibliotecas)"
        & powershell -NoProfile -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" 2>&1 |
            ForEach-Object { Anotar "$_" }
        $uv = Achar-Uv
        if (-not $uv) {
            $base = Achar-Python
            if ($base) {
                Write-Host "   o instalador oficial do uv nao funcionou; tentando pelo pip"
                Rodar $base @("-m", "pip", "install", "--user", "--disable-pip-version-check", "-q", "uv") | ForEach-Object { Anotar $_ }
                $uv = Achar-Uv
            }
        }
        if ($uv) { Write-Host "   uv instalado em $uv" }
        else { Write-Host "   o uv nao instalou (motivo no log). Sigo sem ele, com o Python do computador." }
    }

    # 3. O Python que roda os scripts. Windows ARM: o Python x64 (emulado), que tem todos os pacotes prontos.
    $pyuv = if ("$env:PROCESSOR_ARCHITECTURE$env:PROCESSOR_ARCHITEW6432" -match "ARM64") { "cpython-3.12-windows-x86_64-none" } else { "3.12" }
    $rodar = $null
    $como = $null
    if ($uv) {
        Write-Host "== Baixando o Python 3.12 pelo uv (na primeira vez demora alguns minutos)"
        & $uv run --no-project --quiet --python $pyuv python -c "pass" 2>&1 | ForEach-Object { Anotar "$_" }
        if ($LASTEXITCODE -eq 0) {
            $rodar = @($uv, "run", "--no-project", "--quiet", "--python", $pyuv, "python")
            $como = "& `"$uv`" run --no-project --python $pyuv python"
        } else {
            Write-Host "   o uv nao conseguiu baixar o Python 3.12; sigo com o Python do computador"
        }
    }
    if (-not $rodar) {
        $base = Achar-Python
        if ($base) { $rodar = $base; $como = ($base -join " ") }
    }
    if (-not $rodar) {
        Falhou ("Este computador nao tem Python e o uv nao instalou. Instale o Python 3.12 pelo site " +
            "https://www.python.org/downloads/ (marque 'Add python.exe to PATH') e rode este instalador de novo.")
        return
    }

    Write-Host "== Preparando as bibliotecas (na primeira vez demora alguns minutos)"
    Rodar $rodar @((Join-Path $destino "scripts\ambiente.py")) | ForEach-Object { Anotar $_; Write-Host "   $_" }
    if ($LASTEXITCODE -ne 0) {
        Falhou "O Python da skill nao ficou pronto (motivo acima)."
        return
    }

    # 4. Testes
    Write-Host "== Testando os scripts"
    $erros = 0
    foreach ($s in "astreintes", "correcao", "ler_processo", "montar_kit", "gerar_docx", "conferir_citacoes", "demonstrativo_pdf", "destacar_expediente") {
        $saida = @(Rodar $rodar @((Join-Path $destino "scripts\$s.py"), "--teste"))
        $cod = $LASTEXITCODE
        Write-Host ("   {0,-22} {1}" -f $s, ($saida | Select-Object -Last 1))
        if ($cod -ne 0) {
            $erros++
            Anotar ("--- $s --teste`r`n" + ($saida -join "`r`n"))
        }
    }
    if ($erros -gt 0) {
        Falhou "$erros teste(s) nao passaram."
        return
    }

    Write-Host "== Para rodar os scripts neste computador: $como scripts\<script>.py"
    Write-Host "== Pronto. Abra uma sessao nova do Claude Code, anexe o PDF do processo e os prints da aba Expedientes"
    Write-Host "   e peca: ""Faca o cumprimento provisorio deste processo""."
    Write-Host "RESULTADO: OK"
}

Instalar
