"""SIMPLIFIA CLI - Main entry point."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .doctor import run_doctor
from .registry import fetch_registry, list_packs
from .install import install_pack
from .update import update_pack
from .state import get_installed_packs, get_pack_status
from .test import test_pack
from .logs import show_logs

app = typer.Typer(
    name="simplifia",
    help="🚀 SIMPLIFIA Installer - Instala packs de automação no OpenClawd",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold purple]SIMPLIFIA[/] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Mostra a versão do installer"
    ),
):
    """🚀 SIMPLIFIA Installer - Automação sem código."""
    pass


@app.command()
def doctor():
    """🩺 Verifica se o ambiente está pronto para usar SIMPLIFIA."""
    run_doctor()


@app.command("list")
def list_available():
    """📦 Lista packs disponíveis para instalação."""
    list_packs()


@app.command()
def install(
    pack: str = typer.Argument(..., help="Nome do pack (ex: whatsapp, freelancers)"),
    force: bool = typer.Option(False, "--force", "-f", help="Reinstala mesmo se já existir"),
):
    """⬇️ Instala um pack no OpenClawd."""
    install_pack(pack, force=force)


@app.command()
def update(
    pack: str = typer.Argument(None, help="Nome do pack (ou --all para todos)"),
    all_packs: bool = typer.Option(False, "--all", "-a", help="Atualiza todos os packs instalados"),
):
    """🔄 Atualiza um pack (ou todos) para a última versão."""
    update_pack(pack, all_packs=all_packs)


@app.command()
def status():
    """📊 Mostra status dos packs instalados."""
    installed = get_installed_packs()
    
    if not installed:
        console.print("[yellow]Nenhum pack instalado ainda.[/]")
        console.print("Use [bold]simplifia install whatsapp[/] para começar!")
        return
    
    table = Table(title="Packs Instalados")
    table.add_column("Pack", style="cyan")
    table.add_column("Versão", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Última Atualização")
    
    for pack_id, info in installed.items():
        status = get_pack_status(pack_id)
        table.add_row(
            info.get("name", pack_id),
            info.get("version", "?"),
            status,
            info.get("installed_at", "?")
        )
    
    console.print(table)


@app.command()
def uninstall(
    pack: str = typer.Argument(..., help="Nome do pack para remover"),
    keep_data: bool = typer.Option(False, "--keep-data", help="Mantém dados do SQLite"),
):
    """🗑️ Remove um pack instalado."""
    from .uninstall import uninstall_pack
    uninstall_pack(pack, keep_data=keep_data)


@app.command()
def test(
    pack: str = typer.Argument(..., help="Nome do pack para testar"),
):
    """🧪 Testa um pack com mensagens de exemplo (sem risco)."""
    test_pack(pack)


@app.command()
def logs(
    pack: str = typer.Argument(None, help="Filtrar por pack"),
    lines: int = typer.Option(20, "--lines", "-n", help="Número de linhas"),
):
    """📜 Mostra logs de execução."""
    show_logs(pack, lines)


# Clawdbot subcommands
clawdbot_app = typer.Typer(
    name="clawdbot",
    help="🐳 Gerenciar Clawdbot (Docker)",
)
app.add_typer(clawdbot_app, name="clawdbot")


@clawdbot_app.command("doctor")
def clawdbot_doctor_cmd():
    """🩺 Verifica se Docker está pronto para Clawdbot."""
    from .clawdbot import clawdbot_doctor
    clawdbot_doctor()


@clawdbot_app.command("install")
def clawdbot_install_cmd(
    docker: bool = typer.Option(True, "--docker", "-d", help="Instalar via Docker"),
):
    """⬇️ Instala Clawdbot via Docker."""
    from .clawdbot import clawdbot_install
    clawdbot_install(use_docker=docker)


@clawdbot_app.command("start")
def clawdbot_start_cmd():
    """🚀 Inicia o container do Clawdbot."""
    from .clawdbot import clawdbot_start
    clawdbot_start()


@clawdbot_app.command("stop")
def clawdbot_stop_cmd():
    """⏹️ Para o container do Clawdbot."""
    from .clawdbot import clawdbot_stop
    clawdbot_stop()


@clawdbot_app.command("status")
def clawdbot_status_cmd():
    """📊 Mostra status do Clawdbot."""
    from .clawdbot import clawdbot_status
    clawdbot_status()


@clawdbot_app.command("logs")
def clawdbot_logs_cmd(
    lines: int = typer.Option(50, "--lines", "-n", help="Número de linhas"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Seguir logs em tempo real"),
):
    """📜 Mostra logs do Clawdbot."""
    from .clawdbot import clawdbot_logs
    clawdbot_logs(lines=lines, follow=follow)


@clawdbot_app.command("update")
def clawdbot_update_cmd():
    """🔄 Atualiza Clawdbot para última versão."""
    from .clawdbot import clawdbot_update
    clawdbot_update()


@clawdbot_app.command("uninstall")
def clawdbot_uninstall_cmd():
    """🗑️ Remove Clawdbot."""
    from .clawdbot import clawdbot_uninstall
    clawdbot_uninstall()


if __name__ == "__main__":
    app()
