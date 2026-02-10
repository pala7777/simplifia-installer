"""Update command - updates installed packs."""

from rich.console import Console

from .registry import fetch_registry, get_pack_info
from .state import get_installed_packs
from .install import install_pack

console = Console()

def update_pack(pack_id: str = None, all_packs: bool = False):
    """Update one or all installed packs."""
    
    if all_packs:
        installed = get_installed_packs()
        if not installed:
            console.print("[yellow]Nenhum pack instalado para atualizar.[/]")
            return
        
        console.print(f"[bold purple]🔄 Atualizando {len(installed)} packs...[/]")
        for pid in installed.keys():
            update_single_pack(pid)
        return
    
    if not pack_id:
        console.print("[red]Especifique um pack ou use --all[/]")
        console.print("Exemplo: [bold]simplifia update whatsapp[/]")
        return
    
    update_single_pack(pack_id)


def update_single_pack(pack_id: str):
    """Update a single pack."""
    installed = get_installed_packs()
    
    if pack_id not in installed:
        console.print(f"[yellow]Pack '{pack_id}' não está instalado.[/]")
        console.print(f"Use [bold]simplifia install {pack_id}[/] para instalar.")
        return
    
    current_version = installed[pack_id].get("version", "0.0.0")
    
    # Fetch latest info
    pack_info = get_pack_info(pack_id)
    if not pack_info:
        console.print(f"[red]Pack '{pack_id}' não encontrado no registry.[/]")
        return
    
    latest_version = pack_info.get("latest_version", "0.0.0")
    
    if current_version == latest_version:
        console.print(f"[green]✓ {pack_id} já está na última versão ({current_version})[/]")
        return
    
    console.print(f"[bold purple]🔄 Atualizando {pack_id}: {current_version} → {latest_version}[/]")
    
    # Reinstall with force
    install_pack(pack_id, force=True)
