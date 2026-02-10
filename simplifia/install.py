"""Install command - downloads and installs packs."""

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .doctor import get_openclawd_path, get_simplifia_path
from .registry import fetch_registry, get_pack_info
from .state import mark_installed

console = Console()

def install_pack(pack_id: str, force: bool = False):
    """Install a pack from the registry."""
    
    # Get pack info from registry
    pack_info = get_pack_info(pack_id)
    if not pack_info:
        console.print(f"[red]❌ Pack '{pack_id}' não encontrado no registry.[/]")
        console.print("Use [bold]simplifia list[/] para ver packs disponíveis.")
        return False
    
    zip_url = pack_info.get("zip_url")
    expected_sha = pack_info.get("sha256")
    version = pack_info.get("latest_version", "unknown")
    
    if not zip_url:
        console.print(f"[red]❌ Pack '{pack_id}' ainda não tem release disponível.[/]")
        return False
    
    console.print(f"[bold purple]📦 Instalando {pack_info.get('name', pack_id)} v{version}[/]")
    
    # Create temp directory for download
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_path = tmpdir / f"{pack_id}.zip"
        
        # Download
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Baixando pack...", total=None)
            
            try:
                with httpx.stream("GET", zip_url, timeout=60, follow_redirects=True) as r:
                    r.raise_for_status()
                    with open(zip_path, "wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)
            except httpx.HTTPError as e:
                console.print(f"[red]❌ Erro no download: {e}[/]")
                return False
            
            progress.update(task, description="Download concluído!")
        
        # Verify SHA256 if provided
        if expected_sha:
            actual_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            if actual_sha != expected_sha:
                console.print(f"[red]❌ Verificação SHA256 falhou![/]")
                console.print(f"  Esperado: {expected_sha}")
                console.print(f"  Recebido: {actual_sha}")
                return False
            console.print("[green]✓ SHA256 verificado[/]")
        
        # Extract
        extract_path = tmpdir / "extracted"
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Read pack.json from extracted content
        pack_json_path = extract_path / "pack.json"
        if not pack_json_path.exists():
            # Try one level deeper
            for subdir in extract_path.iterdir():
                if subdir.is_dir():
                    pack_json_path = subdir / "pack.json"
                    if pack_json_path.exists():
                        extract_path = subdir
                        break
        
        if not pack_json_path.exists():
            console.print("[red]❌ pack.json não encontrado no pacote![/]")
            return False
        
        pack_config = json.loads(pack_json_path.read_text())
        
        # Install files
        openclawd_path = get_openclawd_path()
        install_config = pack_config.get("install", {}).get("copy_to", {})
        
        for folder_type, dest_pattern in install_config.items():
            src = extract_path / folder_type
            if src.exists():
                dest = Path(os.path.expanduser(dest_pattern))
                dest.mkdir(parents=True, exist_ok=True)
                
                # Copy contents
                for item in src.iterdir():
                    if item.is_file():
                        shutil.copy2(item, dest / item.name)
                    elif item.is_dir():
                        shutil.copytree(item, dest / item.name, dirs_exist_ok=True)
                
                console.print(f"[green]✓ {folder_type}/ → {dest}[/]")
        
        # Run SQLite migrations if needed
        db_config = pack_config.get("install", {}).get("db", {})
        if db_config.get("type") == "sqlite":
            run_sqlite_migrations(extract_path, db_config)
        
        # Mark as installed
        mark_installed(pack_id, {
            "name": pack_config.get("name", pack_id),
            "version": pack_config.get("version", version),
            "installed_at": datetime.now().isoformat(),
        })
        
        # Generate first run report
        generate_first_run_report(pack_id, pack_config, version)
        
        console.print()
        console.print(f"[green bold]✓ Pack {pack_id} instalado com sucesso![/]")
        console.print(f"  Use [bold]simplifia test {pack_id}[/] para testar.")
        console.print(f"  Relatório: [dim]~/.simplifia/RELATORIO-PRIMEIRO-USO.md[/]")
        return True


def generate_first_run_report(pack_id: str, pack_config: dict, version: str):
    """Generate first run report markdown file."""
    from .doctor import get_simplifia_path
    
    report_path = get_simplifia_path() / "RELATORIO-PRIMEIRO-USO.md"
    
    report = f"""# SIMPLIFIA - Relatório de Instalação

**Pack:** {pack_config.get('name', pack_id)}
**Versão:** {version}
**Instalado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Arquivos instalados

### Workflows
- `~/.simplifia/workflows/{pack_id}/`

### Regras
- `~/.simplifia/rules/{pack_id}/`

### Assets
- `~/.simplifia/assets/{pack_id}/`

## Comandos úteis

```bash
# Testar o pack
simplifia test {pack_id}

# Ver status
simplifia status

# Atualizar
simplifia update {pack_id}

# Ver logs
simplifia logs
```

## Modo Seguro

Os blueprints geram **rascunhos e sugestões**. Você revisa antes de enviar.
Nada é enviado automaticamente por padrão.

## Suporte

- Portal: https://simplifia.vercel.app
- Documentação: https://simplifia.vercel.app/downloads
"""
    
    report_path.write_text(report)
    console.print(f"[dim]📄 Relatório salvo em {report_path}[/]")


def run_sqlite_migrations(extract_path: Path, db_config: dict):
    """Run SQLite migrations."""
    import sqlite3
    
    db_path = Path(os.path.expanduser(db_config.get("path", "~/.simplifia/state.db")))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    migrations = db_config.get("migrations", [])
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for migration_file in migrations:
        migration_path = extract_path / migration_file
        if migration_path.exists():
            sql = migration_path.read_text()
            try:
                cursor.executescript(sql)
                console.print(f"[green]✓ Migration: {migration_file}[/]")
            except sqlite3.Error as e:
                console.print(f"[yellow]⚠ Migration {migration_file}: {e}[/]")
    
    conn.commit()
    conn.close()
