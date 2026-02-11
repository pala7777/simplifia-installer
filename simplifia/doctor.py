"""Doctor command - verifies environment is ready."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Detect Windows and use plain mode (ASCII-safe)
IS_WINDOWS = os.name == 'nt'
USE_PLAIN_MODE = IS_WINDOWS

# Configure Rich for Windows compatibility
if USE_PLAIN_MODE:
    # Force UTF-8 on Windows
    if IS_WINDOWS:
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

from rich.console import Console

# Create console with Windows-safe settings
console = Console(
    force_terminal=True,
    no_color=USE_PLAIN_MODE,
    emoji=not USE_PLAIN_MODE,
    highlight=not USE_PLAIN_MODE,
)


def get_openclawd_path() -> Path:
    """Get OpenClawd base path (cross-platform).
    
    Note: This is kept for compatibility but OpenClawd is no longer required.
    SIMPLIFIA now uses ~/.simplifia as the primary installation path.
    """
    if IS_WINDOWS:
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:
        base = Path.home()
    return base / '.openclawd'


def get_simplifia_path() -> Path:
    """Get SIMPLIFIA config path (cross-platform)."""
    if IS_WINDOWS:
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:
        base = Path.home()
    return base / '.simplifia'


def check_docker_available() -> tuple[bool, bool]:
    """Check if Docker is installed and running.
    
    Returns:
        (installed, running) - tuple of bools
    """
    # Check if docker command exists
    if shutil.which('docker') is None:
        return False, False
    
    # Check if Docker daemon is running
    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            timeout=10
        )
        return True, result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return True, False


def check_clawdbot_running() -> bool:
    """Check if Clawdbot container is running."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=clawdbot', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return 'clawdbot' in result.stdout
    except Exception:
        return False


def _print_check(name: str, ok: bool, detail: str = ""):
    """Print a check result in ASCII-safe format."""
    status = "[OK]" if ok else "[X]"
    color = "green" if ok else "red"
    detail_str = f" ({detail})" if detail else ""
    
    if USE_PLAIN_MODE:
        print(f"  {status} {name}{detail_str}")
    else:
        status_fmt = f"[{color}]{status}[/{color}]"
        console.print(f"  {status_fmt} {name}[dim]{detail_str}[/dim]")


def _print_warning(msg: str):
    """Print a warning message."""
    if USE_PLAIN_MODE:
        print(f"  [!] {msg}")
    else:
        console.print(f"  [yellow]! {msg}[/yellow]")


def _print_info(msg: str):
    """Print an info message."""
    if USE_PLAIN_MODE:
        print(f"      {msg}")
    else:
        console.print(f"      [dim]{msg}[/dim]")


def _print_action(msg: str):
    """Print an action/next step message."""
    if USE_PLAIN_MODE:
        print(f"  --> {msg}")
    else:
        console.print(f"  [cyan]--> {msg}[/cyan]")


def run_doctor():
    """Run environment checks."""
    # Header
    if USE_PLAIN_MODE:
        print("")
        print("=" * 50)
        print("  SIMPLIFIA Doctor - Verificando seu ambiente...")
        print("=" * 50)
    else:
        console.print()
        console.print("[bold purple]SIMPLIFIA Doctor[/] - Verificando seu ambiente...")
        console.print()
    
    checks = []
    docker_installed = False
    docker_running = False
    clawdbot_running = False
    
    # Check 1: Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    py_ok = sys.version_info >= (3, 9)
    checks.append(("Python >= 3.9", py_ok, f"v{py_version}"))
    
    # Check 2: Docker
    docker_installed, docker_running = check_docker_available()
    if docker_running:
        checks.append(("Docker", True, "instalado e rodando"))
        clawdbot_running = check_clawdbot_running()
    elif docker_installed:
        checks.append(("Docker", False, "instalado mas NAO esta rodando"))
    else:
        checks.append(("Docker", False, "nao instalado"))
    
    # Check 3: Clawdbot runtime (only if Docker is running)
    if docker_running:
        if clawdbot_running:
            checks.append(("Motor Clawdbot", True, "rodando"))
        else:
            checks.append(("Motor Clawdbot", False, "nao iniciado"))
    
    # Check 4: SIMPLIFIA directory (create if missing)
    simplifia_path = get_simplifia_path()
    if not simplifia_path.exists():
        simplifia_path.mkdir(parents=True, exist_ok=True)
        (simplifia_path / 'cache').mkdir(exist_ok=True)
    checks.append(("Pasta SIMPLIFIA", simplifia_path.exists(), str(simplifia_path)))
    
    # Check 5: Write permissions
    can_write = os.access(simplifia_path, os.W_OK) if simplifia_path.exists() else False
    checks.append(("Permissao de escrita", can_write, str(simplifia_path)))
    
    # Check 6: curl available
    has_curl = shutil.which('curl') is not None
    checks.append(("curl disponivel", has_curl, "para downloads"))
    
    # Print results
    print("")
    all_ok = True
    for name, ok, detail in checks:
        _print_check(name, ok, detail)
        if not ok:
            all_ok = False
    
    print("")
    
    # Docker-specific messages (UX-focused)
    automation_ready = docker_running and clawdbot_running
    
    if not docker_installed:
        if USE_PLAIN_MODE:
            print("  [OK] SimplifIA instalado.")
            print("  [!] Automacao ainda nao ativada: Docker Desktop nao instalado.")
            print("")
            print("  --> Proximo passo:")
            print("      1. Instale o Docker Desktop: https://docker.com/products/docker-desktop")
            print("      2. Abra o Docker Desktop e aguarde 'Docker is running'")
            print("      3. Execute: simplifia doctor")
        else:
            console.print("  [green][OK][/green] SimplifIA instalado.")
            console.print("  [yellow][!] Automacao ainda nao ativada: Docker Desktop nao instalado.[/yellow]")
            console.print()
            console.print("  [cyan]--> Proximo passo:[/cyan]")
            console.print("      1. Instale o Docker Desktop: https://docker.com/products/docker-desktop")
            console.print("      2. Abra o Docker Desktop e aguarde 'Docker is running'")
            console.print("      3. Execute: [bold]simplifia doctor[/bold]")
        print("")
        
    elif not docker_running:
        if USE_PLAIN_MODE:
            print("  [OK] SimplifIA instalado.")
            print("  [!] Automacao ainda nao ativada: Docker Desktop nao esta rodando.")
            print("")
            print("  --> Proximo passo:")
            print("      1. Abra o Docker Desktop e aguarde 'Docker is running'")
            print("      2. Execute: simplifia doctor")
        else:
            console.print("  [green][OK][/green] SimplifIA instalado.")
            console.print("  [yellow][!] Automacao ainda nao ativada: Docker Desktop nao esta rodando.[/yellow]")
            console.print()
            console.print("  [cyan]--> Proximo passo:[/cyan]")
            console.print("      1. Abra o Docker Desktop e aguarde 'Docker is running'")
            console.print("      2. Execute: [bold]simplifia doctor[/bold]")
        print("")
        
    elif not clawdbot_running:
        if USE_PLAIN_MODE:
            print("  [OK] SimplifIA instalado.")
            print("  [OK] Docker rodando.")
            print("  [!] Motor Clawdbot nao iniciado.")
            print("")
            print("  --> Execute: simplifia clawdbot start")
        else:
            console.print("  [green][OK][/green] SimplifIA instalado.")
            console.print("  [green][OK][/green] Docker rodando.")
            console.print("  [yellow][!] Motor Clawdbot nao iniciado.[/yellow]")
            console.print()
            console.print("  [cyan]--> Execute:[/cyan] [bold]simplifia clawdbot start[/bold]")
        print("")
    
    # Final status
    if automation_ready:
        if USE_PLAIN_MODE:
            print("  ============================================")
            print("  [OK] Ambiente pronto!")
            print("  ============================================")
            print("")
            print("  Para instalar o pack WhatsApp:")
            print("      simplifia install whatsapp")
        else:
            console.print("  [green bold]==========================================")
            console.print("  [OK] Ambiente pronto!")
            console.print("  ==========================================[/green bold]")
            console.print()
            console.print("  Para instalar o pack WhatsApp:")
            console.print("      [bold]simplifia install whatsapp[/bold]")
    else:
        if USE_PLAIN_MODE:
            print("  Dica: Se voce instalou Docker agora, feche e reabra o Terminal")
            print("        e rode: simplifia doctor")
        else:
            console.print("  [dim]Dica: Se voce instalou Docker agora, feche e reabra o Terminal[/dim]")
            console.print("  [dim]      e rode: simplifia doctor[/dim]")
    
    print("")
    
    return all_ok, docker_installed, docker_running, clawdbot_running
