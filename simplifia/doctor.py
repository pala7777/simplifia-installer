"""Doctor command - verifies environment is ready."""

import os
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def get_openclawd_path() -> Path:
    """Get OpenClawd base path (cross-platform)."""
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:  # Unix
        base = Path.home()
    return base / '.openclawd'

def get_simplifia_path() -> Path:
    """Get SIMPLIFIA config path (cross-platform)."""
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:  # Unix
        base = Path.home()
    return base / '.simplifia'

def run_doctor():
    """Run environment checks."""
    console.print(Panel.fit(
        "[bold]🩺 SIMPLIFIA Doctor[/]\nVerificando seu ambiente...",
        border_style="purple"
    ))
    
    checks = []
    
    # Check 1: Python version
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    py_ok = sys.version_info >= (3, 9)
    checks.append(("Python >= 3.9", py_ok, f"v{py_version}"))
    
    # Check 2: OpenClawd directory
    openclawd_path = get_openclawd_path()
    openclawd_exists = openclawd_path.exists()
    checks.append(("OpenClawd instalado", openclawd_exists, str(openclawd_path)))
    
    # Check 3: SIMPLIFIA directory (create if missing)
    simplifia_path = get_simplifia_path()
    if not simplifia_path.exists():
        simplifia_path.mkdir(parents=True, exist_ok=True)
        (simplifia_path / 'cache').mkdir(exist_ok=True)
    checks.append(("Pasta SIMPLIFIA", simplifia_path.exists(), str(simplifia_path)))
    
    # Check 4: Write permissions
    can_write = os.access(simplifia_path, os.W_OK) if simplifia_path.exists() else False
    checks.append(("Permissão de escrita", can_write, str(simplifia_path)))
    
    # Check 5: curl or httpx available
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
    
    if all_ok:
        console.print("[green bold]✓ Ambiente pronto![/] Use [bold]simplifia install whatsapp[/] para começar.")
    else:
        console.print("[yellow]⚠ Alguns itens precisam de atenção.[/]")
        if not openclawd_exists:
            console.print("  → Instale o OpenClawd primeiro: [link]https://openclawd.com[/link]")
    
    return all_ok
