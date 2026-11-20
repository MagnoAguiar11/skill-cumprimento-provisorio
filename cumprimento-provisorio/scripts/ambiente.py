#!/usr/bin/env python3
"""Acha (ou prepara) o Python com as bibliotecas que os scripts da skill usam, em qualquer computador.

Os scripts não chamam o uv direto: pedem a este módulo para rodar um trecho de código com os pacotes
de que precisam. A ordem é esta:
  1. o uv, no PATH ou nas pastas onde os instaladores o põem (~/.local/bin, ~/.cargo/bin, Homebrew,
     pip --user), mesmo que o terminal do Claude Code ainda não o enxergue;
  2. sem uv, ou se ele não conseguir baixar o Python, um Python próprio da skill (venv) criado com o
     python3 do computador. As bibliotecas vêm do PyPI na primeira vez. Nada pede senha de administrador.

  python3 ambiente.py              prepara e testa tudo (o instalador roda isto; pode rodar de novo)
  python3 ambiente.py --status     mostra o que está em uso, sem instalar nada
  python3 ambiente.py --sem-uv     prepara o Python próprio mesmo havendo uv
"""
import argparse
import glob
import json
import os
import shutil
import site
import subprocess
import sys
from pathlib import Path

# Python 3.12 fixo no uv (o mais novo nem sempre tem os pacotes). No Windows ARM, a versão x64, que o Windows
# emula: vários pacotes (cryptography, pyclipper) não têm versão pronta para ARM e não compilam sem o Visual C++.
ARM_WIN = os.name == "nt" and "ARM64" in os.environ.get("PROCESSOR_ARCHITECTURE", "") + os.environ.get("PROCESSOR_ARCHITEW6432", "")
PYTHON_UV = ["--python", "cpython-3.12-windows-x86_64-none" if ARM_WIN else "3.12"]
UTF8 = {"encoding": "utf-8", "errors": "replace", "env": {**os.environ, "PYTHONUTF8": "1"}}  # Windows: sem isso o texto sai em cp1252

MARKITDOWN = "markitdown[pdf]==0.1.9"  # pede Python 3.10 ou mais novo
BASICOS = ["pypdf==5.1.0", "pillow==10.4.0", "pypdfium2==4.30.0", "python-docx==1.1.2"]
TODOS = [MARKITDOWN] + BASICOS
IMPORTS = {"markitdown": "markitdown", "pypdf": "pypdf", "pillow": "PIL", "pypdfium2": "pypdfium2", "python-docx": "docx"}
# Ordem de preferência para o Python próprio: 3.12 é o testado; 3.9 (o do Mac) não roda o MarkItDown.
PREFERENCIA = [(3, 12), (3, 11), (3, 10), (3, 13)]

AJUDA = ("Para resolver: rode  python3 \"{script}\"  e mostre a saída. Ele procura o uv e, sem ele, monta um "
         "Python próprio da skill (precisa de internet só na primeira vez).")


class SemAmbiente(Exception):
    """Não há como rodar o código com estes pacotes neste computador."""


class PacoteIndisponivel(SemAmbiente):
    """O pacote não existe para o Python disponível (ex.: MarkItDown no Python 3.9)."""


# ---------------------------------------------------------------------------------------------------------
# Onde ficam as coisas

def pasta():
    """Pasta de trabalho do ambiente. Fica fora da pasta da skill, para sobreviver às atualizações."""
    if os.environ.get("CUMPRIMENTO_AMBIENTE"):
        return Path(os.environ["CUMPRIMENTO_AMBIENTE"])
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "skill-cumprimento-provisorio"


def _config():
    try:
        return json.loads((pasta() / "ambiente.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(cfg):
    pasta().mkdir(parents=True, exist_ok=True)
    (pasta() / "ambiente.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def _executavel(c):
    return bool(c) and Path(c).is_file() and os.access(str(c), os.X_OK)


def achar_uv():
    """Caminho do uv, mesmo fora do PATH (o instalador do uv só muda o PATH dos terminais abertos depois)."""
    exe = "uv.exe" if os.name == "nt" else "uv"
    home = Path.home()
    cands = [_config().get("uv"), os.environ.get("UV_EXE"), shutil.which("uv")]
    for var in ("UV_INSTALL_DIR", "XDG_BIN_HOME"):
        if os.environ.get(var):
            cands += [Path(os.environ[var]) / exe, Path(os.environ[var]) / "bin" / exe]
    cands += [home / ".local" / "bin" / exe, home / ".cargo" / "bin" / exe]
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local")
        roaming = Path(os.environ.get("APPDATA") or home / "AppData" / "Roaming")
        cands += [local / "Microsoft" / "WinGet" / "Links" / exe, home / "scoop" / "shims" / exe]
        cands += sorted(glob.glob(str(roaming / "Python" / "Python3*" / "Scripts" / exe)), reverse=True)  # pip --user
    else:
        cands += ["/opt/homebrew/bin/uv", "/usr/local/bin/uv", "/home/linuxbrew/.linuxbrew/bin/uv"]
        cands += sorted(glob.glob(str(home / "Library" / "Python" / "3.*" / "bin" / "uv")), reverse=True)  # pip --user no Mac
    try:
        cands.append(Path(site.getuserbase()) / ("Scripts" if os.name == "nt" else "bin") / exe)
    except Exception:  # noqa: BLE001 - alguns Pythons embutidos não têm site.getuserbase
        pass
    return next((str(c) for c in cands if _executavel(c)), None)


def _cmd_uv(uv, pacotes):
    com = []
    for p in pacotes:
        com += ["--with", p]
    return [uv, "run", "--no-project", "--quiet", *PYTHON_UV, *com, "python"]


def _uv_funciona(uv):
    """O uv consegue abrir o Python 3.12? (falha quando a rede bloqueia o download do Python)"""
    try:
        r = subprocess.run([uv, "run", "--no-project", "--quiet", *PYTHON_UV, "python", "-c", "pass"],
                           capture_output=True, timeout=600, **UTF8)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


# ---------------------------------------------------------------------------------------------------------
# Python próprio da skill (venv), quando não há uv

def _versao(cmd):
    try:
        r = subprocess.run(cmd + ["-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
                           capture_output=True, timeout=30, **UTF8)
        if r.returncode == 0:
            return tuple(int(x) for x in r.stdout.strip().split("."))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def _mac_sem_ferramentas():
    """No Mac, /usr/bin/python3 sem as Ferramentas de Linha de Comando abre uma janela pedindo para instalar."""
    if sys.platform != "darwin":
        return False
    try:
        return subprocess.run(["xcode-select", "-p"], capture_output=True, timeout=10).returncode != 0
    except (OSError, subprocess.TimeoutExpired):
        return True


def _candidatos():
    cands = [[sys.executable]]
    if os.name == "nt":
        if shutil.which("py"):
            cands += [["py", "-%d.%d" % v] for v in PREFERENCIA]
        cands += [[c] for c in (shutil.which("python"), shutil.which("python3")) if c and "WindowsApps" not in c]
        return cands
    for v in ["%d.%d" % v for v in PREFERENCIA] + ["3"]:
        cands += [[c] for c in (shutil.which("python" + v), "/opt/homebrew/bin/python" + v, "/usr/local/bin/python" + v,
                                "/Library/Frameworks/Python.framework/Versions/%s/bin/python3" % v) if _executavel(c)]
    cands.append(["/usr/bin/python3"])
    stub = _mac_sem_ferramentas()  # sem as ferramentas, o /usr/bin/python3 do Mac só abre a janela de instalação
    return [c for c in cands if _executavel(c[0]) and not (stub and c[0].startswith("/usr/bin/"))]


def _nota(v):
    """Menor é melhor: 3.12, 3.11, 3.10, 3.13, depois o mais novo, por último 3.9 e 3.8."""
    if v in PREFERENCIA:
        return (0, PREFERENCIA.index(v))
    return (1, -v[1]) if v >= (3, 10) else (2, -v[1])


def _melhor_python():
    vistos, achados = set(), []
    for c in _candidatos():
        chave = tuple(c)
        if chave in vistos:
            continue
        vistos.add(chave)
        v = _versao(c)
        if v and v >= (3, 8):
            achados.append((_nota(v), v, c))
    if not achados:
        return None, None
    _, v, c = min(achados, key=lambda x: x[0])
    return c, v


def _venv_python(dir_):
    return dir_ / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _avisar(msg):
    print(msg, file=sys.stderr, flush=True)


def _criar_venv(cfg):
    base, v = _melhor_python()
    if not base:
        raise SemAmbiente("Não há Python 3.8 ou mais novo neste computador, nem o uv.")
    dir_ = pasta() / "venv"
    if dir_.exists():
        shutil.rmtree(dir_, ignore_errors=True)
    _avisar("Preparando o Python próprio da skill (Python %d.%d; só na primeira vez)..." % v)
    r = subprocess.run(base + ["-m", "venv", str(dir_)], capture_output=True, **UTF8)
    vpy = _venv_python(dir_)
    if r.returncode != 0 or not vpy.exists():
        raise SemAmbiente("Não consegui criar o Python próprio da skill com %s:\n%s"
                          % (" ".join(base), (r.stderr or r.stdout)[-800:]))
    subprocess.run([str(vpy), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-q", "--upgrade", "pip"],
                   capture_output=True, **UTF8)  # o pip antigo do Python do Mac às vezes não acha os pacotes prontos
    cfg["venv"] = {"python": str(vpy), "versao": list(v), "base": base, "instalados": []}
    _gravar(cfg)
    return cfg


def _sem_versao(p):
    return p.split("==")[0]


def _pip(vpy, pacotes):
    cmd = [vpy, "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-q"]
    r = subprocess.run(cmd + pacotes, capture_output=True, **UTF8)
    if r.returncode != 0:  # versão fixada sem pacote pronto para este Python: tenta a mais nova compatível
        r2 = subprocess.run(cmd + [_sem_versao(p) for p in pacotes], capture_output=True, **UTF8)
        if r2.returncode != 0:
            return (r.stderr or r.stdout)[-1200:]
    return None


def _venv(pacotes):
    cfg = _config()
    venv = cfg.get("venv") or {}
    if not (venv.get("python") and Path(venv["python"]).exists() and _versao([venv["python"]])):
        cfg = _criar_venv(cfg)
        venv = cfg["venv"]
    versao = tuple(venv["versao"])
    if MARKITDOWN in pacotes and versao < (3, 10):
        raise PacoteIndisponivel("O MarkItDown pede Python 3.10 ou mais novo; o Python próprio da skill é %d.%d." % versao)
    faltam = [p for p in pacotes if p not in venv["instalados"] and p not in venv.get("falharam", [])]
    if faltam:
        _avisar("Instalando as bibliotecas da skill (%s; só na primeira vez)..." % ", ".join(_sem_versao(p) for p in faltam))
        erro = _pip(venv["python"], faltam)
        if erro:
            if MARKITDOWN in faltam and len(faltam) > 1:  # o MarkItDown falha sozinho (ex.: Windows sem Visual C++)
                outros = [p for p in faltam if p != MARKITDOWN]
                if not _pip(venv["python"], outros):
                    venv["instalados"] += outros
                    venv.setdefault("falharam", []).append(MARKITDOWN)
                    _gravar(cfg)
                    raise PacoteIndisponivel("O MarkItDown não instalou neste computador:\n" + erro)
            if faltam == [MARKITDOWN]:
                venv.setdefault("falharam", []).append(MARKITDOWN)
                _gravar(cfg)
                raise PacoteIndisponivel("O MarkItDown não instalou neste computador:\n" + erro)
            raise SemAmbiente("Não consegui instalar %s (confira a internet):\n%s" % (", ".join(faltam), erro))
        venv["instalados"] += faltam
        _gravar(cfg)
    if MARKITDOWN in pacotes and MARKITDOWN in venv.get("falharam", []):
        raise PacoteIndisponivel("O MarkItDown não instalou neste computador (veja python3 ambiente.py --status).")
    return [venv["python"]]


# ---------------------------------------------------------------------------------------------------------
# O que os scripts usam

def comando(pacotes):
    """Comando que abre o Python com estes pacotes; acrescente "-c", código e argumentos."""
    cfg = _config()
    if cfg.get("modo") != "venv":
        uv = achar_uv()
        if uv:
            return _cmd_uv(uv, pacotes)
    try:
        return _venv(pacotes)
    except PacoteIndisponivel:
        raise
    except SemAmbiente as e:
        raise SemAmbiente(str(e) + "\n" + AJUDA.format(script=Path(__file__).resolve()))


def rodar(pacotes, argumentos, **kw):
    """subprocess.run do Python com os pacotes. Se o uv falhar por não conseguir abrir o Python
    (rede bloqueada, por exemplo), passa a usar o Python próprio da skill e tenta de novo."""
    opcoes = {"capture_output": True, **UTF8, **kw}
    cmd = comando(pacotes)
    r = subprocess.run(cmd + list(argumentos), **opcoes)
    if r.returncode != 0 and len(cmd) > 1 and cmd[1] == "run" and not _uv_funciona(cmd[0]):
        _avisar("O uv não conseguiu abrir o Python 3.12; a skill passa a usar o Python próprio dela.\n"
                + (r.stderr or "")[-600:])
        cfg = _config()
        cfg["modo"] = "venv"
        _gravar(cfg)
        r = subprocess.run(_venv(pacotes) + list(argumentos), **opcoes)
    return r


def falhar(e):
    """Mensagem única para o advogado quando não há ambiente."""
    sys.exit("Não consegui preparar o Python da skill neste computador.\n" + str(e))


# ---------------------------------------------------------------------------------------------------------
# Linha de comando: preparar e mostrar o estado

TESTE = "import " + ", ".join(sorted(set(IMPORTS.values()))) + "; print('ok')"


def preparar(sem_uv=False):
    cfg = _config()
    uv = None if sem_uv else achar_uv()
    if uv:
        print("uv encontrado: " + uv)
        print("Baixando o Python 3.12 e as bibliotecas pelo uv (na primeira vez demora alguns minutos)...", flush=True)
        r = subprocess.run(_cmd_uv(uv, TODOS) + ["-c", TESTE], capture_output=True, **UTF8)
        if r.returncode == 0:
            cfg.update(modo="uv", uv=uv)
            _gravar(cfg)
            print("ok: ambiente pronto pelo uv (Python 3.12, MarkItDown e demais bibliotecas)")
            return 0
        if _uv_funciona(uv):  # o Python abriu: só o MarkItDown falhou (ex.: Windows sem Visual C++)
            r2 = subprocess.run(_cmd_uv(uv, BASICOS) + ["-c", "import pypdf, PIL, pypdfium2, docx; print('ok')"],
                                capture_output=True, **UTF8)
            if r2.returncode == 0:
                cfg.update(modo="uv", uv=uv)
                _gravar(cfg)
                print("ok: ambiente pronto pelo uv. Aviso: o MarkItDown não rodou aqui; o processo será lido pelo pypdfium2.")
                return 0
        print("O uv não conseguiu preparar o Python. Motivo:\n" + (r.stderr or r.stdout).strip()[-800:])
        print("Sigo sem o uv, com um Python próprio da skill.")
    else:
        print("uv não encontrado: sigo com um Python próprio da skill.")
    cfg["modo"] = "venv"
    cfg.pop("venv", None)  # recria do zero, para não herdar um ambiente quebrado
    _gravar(cfg)
    try:
        _venv(BASICOS)
    except SemAmbiente as e:
        print("FALHOU: " + str(e))
        if sys.platform == "darwin" and _mac_sem_ferramentas():
            print("No Mac, instale as Ferramentas de Linha de Comando (rode: xcode-select --install) e rode o instalador de novo.")
        return 1
    venv = _config()["venv"]
    aviso = ""
    try:
        _venv([MARKITDOWN])
    except PacoteIndisponivel as e:
        aviso = " Aviso: %s O processo será lido pelo pypdfium2, com o mesmo mapa de IDs." % str(e).splitlines()[0]
    print("ok: ambiente pronto no Python próprio da skill (Python %d.%d em %s).%s" % (tuple(venv["versao"]) + (pasta(), aviso)))
    return 0


def status():
    cfg = _config()
    uv = achar_uv()
    print("uv: " + (uv or "não encontrado"))
    print("modo gravado: " + cfg.get("modo", "nenhum (o instalador ainda não preparou)"))
    v = cfg.get("venv")
    if v:
        print("Python próprio: %s (Python %d.%d)" % (v["python"], *v["versao"]))
        print("   instalados: " + (", ".join(v["instalados"]) or "nenhum"))
        if v.get("falharam"):
            print("   não instalaram: " + ", ".join(v["falharam"]))
    em_uso = "uv" if (cfg.get("modo") != "venv" and uv) else "Python próprio da skill"
    print("em uso pelos scripts: " + em_uso)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", action="store_true", help="mostra o que está em uso, sem instalar nada")
    ap.add_argument("--sem-uv", action="store_true", help="prepara o Python próprio mesmo havendo uv")
    a = ap.parse_args()
    sys.exit(status() if a.status else preparar(a.sem_uv))


if __name__ == "__main__":
    main()
