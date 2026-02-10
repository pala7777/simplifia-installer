"""Uninstall command - removes installed packs."""

import os
import shutil
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

from .doctor import get_simplifia_path
from .state import get_installed_packs, mark_uninstalled

console = Console()

def uninstall_pack(pack_id: str, keep_data: bool = False):
    """Uninstall a pack."""
    
    installed = get_installed_packs()
    
    if pack_id not in installed:
        console.print(f"[yellow]Pack '{pack_id}' não está instalado.[/]")
        return False
    
    pack_info = installed[pack_id]
    console.print(f"[bold]🗑️ Removendo {pack_info.get('name', pack_id)} v{pack_info.get('version', '?')}[/]")
    
    # Confirm
    if not Confirm.ask("Tem certeza?", default=False):
        console.print("[dim]Cancelado.[/]")
        return False
    
    simplifia_path = get_simplifia_path()
    
    # Remove pack folders
    folders_to_remove = [
        simplifia_path / "workflows" / pack_id,
        simplifia_path / "rules" / pack_id,
        simplifia_path / "assets" / pack_id,
    ]
    
    for folder in folders_to_remove:
        if folder.exists():
            try:
                shutil.rmtree(folder)
                console.print(f"[green]✓ Removido: {folder}[/]")
            except Exception as e:
                console.print(f"[yellow]⚠ Não foi possível remover {folder}: {e}[/]")
    
    # Remove from state
    mark_uninstalled(pack_id)
    console.print(f"[green]✓ Registro removido de installed.json[/]")
    
    # SQLite data
    if not keep_data:
        console.print("[dim]Dados do SQLite mantidos (use --keep-data=false para remover)[/]")
    else:
        console.print("[dim]Dados do SQLite preservados[/]")
    
    console.print()
    console.print(f"[green bold]✓ Pack {pack_id} removido com sucesso![/]")
    return True
