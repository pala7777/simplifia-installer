"""Doctor command - verifies environment is ready."""

import os
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def get_simplifia_path() -> Path:
    """Get SIMPLIFIA config path (cross-platform)."""
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:  # Unix
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

def run_doctor():
    """Run environment checks."""
    console.print(Panel.fit(
        "[bold]🩺 SIMPLIFIA Doctor[/]\nVerificando seu ambiente...",
        border_style="purple"
    ))
    
    checks = []
    docker_installed = False
    docker_running = False
    clawdbot_running = False
    
    # Check 1: Python version
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    py_ok = sys.version_info >= (3, 9)
    checks.append(("Python >= 3.9", py_ok, f"v{py_version}"))
    
    # Check 2: Docker
    docker_installed, docker_running = check_docker_available()
    if docker_running:
        checks.append(("Docker", True, "instalado e rodando"))
        clawdbot_running = check_clawdbot_running()
    elif docker_installed:
        checks.append(("Docker", False, "instalado mas não está rodando"))
    else:
        checks.append(("Docker", False, "não instalado"))
    
    # Check 3: Clawdbot runtime (only if Docker is running)
    if docker_running:
        if clawdbot_running:
            checks.append(("Motor Clawdbot", True, "rodando"))
        else:
            checks.append(("Motor Clawdbot", False, "não iniciado"))
    
    # Check 4: SIMPLIFIA directory (create if missing)
    simplifia_path = get_simplifia_path()
    if not simplifia_path.exists():
        simplifia_path.mkdir(parents=True, exist_ok=True)
        (simplifia_path / 'cache').mkdir(exist_ok=True)
    checks.append(("Pasta SIMPLIFIA", simplifia_path.exists(), str(simplifia_path)))
    
    # Check 5: Write permissions
    can_write = os.access(simplifia_path, os.W_OK) if simplifia_path.exists() else False
    checks.append(("Permissão de escrita", can_write, str(simplifia_path)))
    
    # Check 6: curl available
    has_curl = shutil.which('curl') is not None
    checks.append(("curl disponível", has_curl, "para downloads"))
    
    # Print results
    console.print()
    all_ok = True
    for name, ok, detail in checks:
        status = "[green]✓[/]" if ok else "[red]✗[/]"
        detail_str = f"[dim]({detail})[/]" if detail else ""
        console.print(f"  {status} {name} {detail_str}")
        if not ok:
            all_ok = False
    
    console.print()
    
    # Docker-specific messages
    if not docker_installed:
        console.print("[yellow]⚠ Instale o Docker Desktop (obrigatório para rodar o motor).[/]")
        console.print("  → Windows/Mac: [link]https://docker.com/products/docker-desktop[/link]")
        console.print("  → Linux: [dim]sudo apt install docker.io[/dim]")
        console.print()
    elif not docker_running:
        console.print("[yellow]⚠ Docker está instalado mas não está rodando.[/]")
        if os.name == 'nt':
            console.print("  → Abra o Docker Desktop e aguarde ele iniciar.")
        else:
            console.print("  → Execute: [dim]sudo systemctl start docker[/dim]")
        console.print()
    elif not clawdbot_running:
        console.print("[yellow]⚠ Motor Clawdbot não está rodando.[/]")
        console.print("  → Execute: [bold]simplifia clawdbot start[/bold]")
        console.print()
    
    if all_ok:
        console.print("[green bold]✓ Ambiente pronto![/] Use [bold]simplifia install whatsapp[/] para começar.")
    else:
        console.print("[yellow]Alguns itens precisam de atenção (veja acima).[/]")
    
    return all_ok, docker_installed, docker_running, clawdbot_running
