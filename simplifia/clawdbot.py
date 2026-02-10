"""Clawdbot Docker management commands."""

import os
import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

def get_clawdbot_dir() -> Path:
    """Get Clawdbot installation directory."""
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:
        base = Path.home()
    return base / '.simplifia' / 'clawdbot'


def get_assets_dir() -> Path:
    """Get assets directory from package."""
    return Path(__file__).parent.parent / 'assets' / 'clawdbot'


def clawdbot_doctor():
    """Check if Docker is available and Clawdbot can run."""
    console.print(Panel.fit(
        "[bold]🩺 Clawdbot Doctor[/]\nVerificando ambiente Docker...",
        border_style="cyan"
    ))
    
    checks = []
    
    # Check Docker
    docker_available = shutil.which('docker') is not None
    checks.append(("Docker instalado", docker_available, "docker"))
    
    # Check Docker running
    docker_running = False
    if docker_available:
        try:
            result = subprocess.run(['docker', 'info'], capture_output=True, timeout=10)
            docker_running = result.returncode == 0
        except:
            pass
    checks.append(("Docker rodando", docker_running, "docker info"))
    
    # Check docker-compose
    compose_available = shutil.which('docker-compose') is not None or shutil.which('docker') is not None
    checks.append(("Docker Compose", compose_available, "docker compose"))
    
    # Check if Clawdbot installed
    clawdbot_dir = get_clawdbot_dir()
    clawdbot_installed = (clawdbot_dir / 'docker-compose.yml').exists()
    checks.append(("Clawdbot instalado", clawdbot_installed, str(clawdbot_dir)))
    
    # Print results
    console.print()
    all_ok = True
    for name, ok, detail in checks:
        status = "[green]✓[/]" if ok else "[red]✗[/]"
        console.print(f"  {status} {name} [dim]({detail})[/]")
        if not ok:
            all_ok = False
    
    console.print()
    
    if all_ok:
        console.print("[green bold]✓ Ambiente pronto![/]")
    else:
        if not docker_available:
            console.print("[yellow]⚠ Instale o Docker: https://docs.docker.com/get-docker/[/]")
        elif not docker_running:
            console.print("[yellow]⚠ Inicie o Docker Desktop ou o serviço Docker[/]")
        elif not clawdbot_installed:
            console.print("[yellow]⚠ Use [bold]simplifia clawdbot install --docker[/] para instalar[/]")
    
    return all_ok


def clawdbot_install(use_docker: bool = True):
    """Install Clawdbot via Docker."""
    if not use_docker:
        console.print("[yellow]Por enquanto só suportamos instalação via Docker.[/]")
        console.print("Use: [bold]simplifia clawdbot install --docker[/]")
        return False
    
    console.print(Panel.fit(
        "[bold]🐳 Instalando Clawdbot (Docker)[/]",
        border_style="cyan"
    ))
    
    # Check Docker
    if not shutil.which('docker'):
        console.print("[red]❌ Docker não encontrado![/]")
        console.print("Instale: https://docs.docker.com/get-docker/")
        return False
    
    # Create directory
    clawdbot_dir = get_clawdbot_dir()
    clawdbot_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy files
    assets_dir = get_assets_dir()
    
    compose_src = assets_dir / 'docker-compose.yml'
    env_src = assets_dir / 'env.example'
    
    compose_dst = clawdbot_dir / 'docker-compose.yml'
    env_dst = clawdbot_dir / '.env'
    
    if compose_src.exists():
        shutil.copy2(compose_src, compose_dst)
        console.print(f"[green]✓ docker-compose.yml → {compose_dst}[/]")
    else:
        console.print("[red]❌ docker-compose.yml não encontrado nos assets![/]")
        return False
    
    # Create .env if not exists
    if not env_dst.exists() and env_src.exists():
        shutil.copy2(env_src, env_dst)
        console.print(f"[green]✓ .env criado em {env_dst}[/]")
    
    # Ask for token
    console.print()
    console.print("[yellow]⚠ Configure seu token do Clawdbot no arquivo .env[/]")
    console.print(f"   Edite: [bold]{env_dst}[/]")
    
    # Pull image
    console.print()
    if Confirm.ask("Baixar imagem Docker agora?", default=True):
        console.print("[dim]Baixando imagem (pode demorar)...[/]")
        try:
            subprocess.run(
                ['docker', 'compose', 'pull'],
                cwd=clawdbot_dir,
                check=True
            )
            console.print("[green]✓ Imagem baixada![/]")
        except subprocess.CalledProcessError:
            # Try old docker-compose
            try:
                subprocess.run(
                    ['docker-compose', 'pull'],
                    cwd=clawdbot_dir,
                    check=True
                )
                console.print("[green]✓ Imagem baixada![/]")
            except:
                console.print("[yellow]⚠ Não foi possível baixar a imagem agora.[/]")
                console.print("   Será baixada no primeiro start.")
    
    console.print()
    console.print("[green bold]✓ Clawdbot instalado![/]")
    console.print()
    console.print("Próximos passos:")
    console.print(f"  1. Edite [bold]{env_dst}[/] com seu token")
    console.print("  2. Execute [bold]simplifia clawdbot start[/]")
    
    return True


def clawdbot_start():
    """Start Clawdbot container."""
    clawdbot_dir = get_clawdbot_dir()
    
    if not (clawdbot_dir / 'docker-compose.yml').exists():
        console.print("[red]❌ Clawdbot não instalado![/]")
        console.print("Use: [bold]simplifia clawdbot install --docker[/]")
        return False
    
    console.print("[bold cyan]🚀 Iniciando Clawdbot...[/]")
    
    try:
        subprocess.run(
            ['docker', 'compose', 'up', '-d'],
            cwd=clawdbot_dir,
            check=True
        )
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=clawdbot_dir,
                check=True
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Erro ao iniciar: {e}[/]")
            return False
    
    console.print("[green bold]✓ Clawdbot iniciado![/]")
    console.print()
    console.print("Acesse: [bold]http://localhost:18789[/]")
    return True


def clawdbot_stop():
    """Stop Clawdbot container."""
    clawdbot_dir = get_clawdbot_dir()
    
    if not (clawdbot_dir / 'docker-compose.yml').exists():
        console.print("[yellow]Clawdbot não está instalado.[/]")
        return False
    
    console.print("[bold cyan]⏹️ Parando Clawdbot...[/]")
    
    try:
        subprocess.run(
            ['docker', 'compose', 'down'],
            cwd=clawdbot_dir,
            check=True
        )
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ['docker-compose', 'down'],
                cwd=clawdbot_dir,
                check=True
            )
        except:
            pass
    
    console.print("[green]✓ Clawdbot parado.[/]")
    return True


def clawdbot_status():
    """Show Clawdbot container status."""
    clawdbot_dir = get_clawdbot_dir()
    
    if not (clawdbot_dir / 'docker-compose.yml').exists():
        console.print("[yellow]Clawdbot não está instalado.[/]")
        return
    
    console.print("[bold]📊 Status do Clawdbot:[/]")
    console.print()
    
    try:
        subprocess.run(
            ['docker', 'compose', 'ps'],
            cwd=clawdbot_dir
        )
    except:
        try:
            subprocess.run(
                ['docker-compose', 'ps'],
                cwd=clawdbot_dir
            )
        except:
            console.print("[yellow]Não foi possível obter status.[/]")


def clawdbot_logs(lines: int = 50, follow: bool = False):
    """Show Clawdbot logs."""
    clawdbot_dir = get_clawdbot_dir()
    
    if not (clawdbot_dir / 'docker-compose.yml').exists():
        console.print("[yellow]Clawdbot não está instalado.[/]")
        return
    
    cmd = ['docker', 'compose', 'logs', f'--tail={lines}']
    if follow:
        cmd.append('-f')
    
    try:
        subprocess.run(cmd, cwd=clawdbot_dir)
    except:
        cmd[1] = 'docker-compose'
        try:
            subprocess.run(cmd, cwd=clawdbot_dir)
        except:
            console.print("[yellow]Não foi possível obter logs.[/]")


def clawdbot_update():
    """Update Clawdbot to latest version."""
    clawdbot_dir = get_clawdbot_dir()
    
    if not (clawdbot_dir / 'docker-compose.yml').exists():
        console.print("[yellow]Clawdbot não está instalado.[/]")
        return False
    
    console.print("[bold cyan]🔄 Atualizando Clawdbot...[/]")
    
    # Pull new image
    try:
        subprocess.run(
            ['docker', 'compose', 'pull'],
            cwd=clawdbot_dir,
            check=True
        )
    except:
        try:
            subprocess.run(
                ['docker-compose', 'pull'],
                cwd=clawdbot_dir,
                check=True
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Erro ao atualizar: {e}[/]")
            return False
    
    # Restart
    console.print("[dim]Reiniciando...[/]")
    clawdbot_stop()
    clawdbot_start()
    
    console.print("[green bold]✓ Clawdbot atualizado![/]")
    return True


def clawdbot_uninstall():
    """Uninstall Clawdbot."""
    clawdbot_dir = get_clawdbot_dir()
    
    if not clawdbot_dir.exists():
        console.print("[yellow]Clawdbot não está instalado.[/]")
        return
    
    if not Confirm.ask("[red]Remover Clawdbot e todos os dados?[/]", default=False):
        console.print("[dim]Cancelado.[/]")
        return
    
    # Stop first
    clawdbot_stop()
    
    # Remove volume
    try:
        subprocess.run(
            ['docker', 'volume', 'rm', 'simplifia-clawdbot-data'],
            capture_output=True
        )
    except:
        pass
    
    # Remove directory
    shutil.rmtree(clawdbot_dir, ignore_errors=True)
    
    console.print("[green]✓ Clawdbot removido.[/]")
