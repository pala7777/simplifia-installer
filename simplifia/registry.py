"""Registry - fetches and manages pack manifest."""

import json
from typing import Optional
import httpx
from rich.console import Console
from rich.table import Table

console = Console()

# Default registry URL (GitHub raw)
REGISTRY_URL = "https://raw.githubusercontent.com/pala7777/simplifia-packs/main/manifest.json"

_cached_registry = None

def fetch_registry(force_refresh: bool = False) -> dict:
    """Fetch the pack registry from GitHub."""
    global _cached_registry
    
    if _cached_registry and not force_refresh:
        return _cached_registry
    
    try:
        with console.status("[bold purple]Buscando registry...[/]"):
            response = httpx.get(REGISTRY_URL, timeout=30)
            response.raise_for_status()
            _cached_registry = response.json()
            return _cached_registry
    except httpx.HTTPError as e:
        console.print(f"[red]Erro ao buscar registry: {e}[/]")
        # Return empty registry on error
        return {"packs": []}
    except json.JSONDecodeError:
        console.print("[red]Erro: manifest.json inválido[/]")
        return {"packs": []}

def get_pack_info(pack_id: str) -> Optional[dict]:
    """Get info for a specific pack."""
    registry = fetch_registry()
    for pack in registry.get("packs", []):
        if pack.get("id") == pack_id:
            return pack
    return None

def list_packs():
    """List all available packs."""
    registry = fetch_registry()
    packs = registry.get("packs", [])
    
    if not packs:
        console.print("[yellow]Nenhum pack disponível no momento.[/]")
        return
    
    table = Table(title="📦 Packs Disponíveis")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nome", style="white")
    table.add_column("Versão", style="green")
    table.add_column("Descrição")
    
    for pack in packs:
        table.add_row(
            pack.get("id", "?"),
            pack.get("name", "?"),
            pack.get("latest_version", "?"),
            pack.get("release_notes", "")[:50] + "..." if len(pack.get("release_notes", "")) > 50 else pack.get("release_notes", "")
        )
    
    console.print(table)
    console.print()
    console.print("[dim]Use [bold]simplifia install <pack_id>[/] para instalar.[/]")
