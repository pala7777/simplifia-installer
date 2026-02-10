"""Logs command - shows execution logs."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from .doctor import get_simplifia_path

console = Console()

def get_db_path() -> Path:
    """Get path to SQLite database."""
    return get_simplifia_path() / "state.db"

def show_logs(pack_id: Optional[str] = None, lines: int = 20):
    """Show execution logs from SQLite."""
    
    db_path = get_db_path()
    
    if not db_path.exists():
        console.print("[yellow]Nenhum log encontrado ainda.[/]")
        console.print("[dim]Os logs aparecem após usar os workflows.[/]")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if interactions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='interactions'
        """)
        
        if not cursor.fetchone():
            console.print("[yellow]Tabela de logs não existe ainda.[/]")
            console.print("[dim]Execute [bold]simplifia test <pack>[/] para gerar logs.[/]")
            conn.close()
            return
        
        # Fetch logs
        query = """
            SELECT created_at, pack_id, workflow_id, intent, status, message_preview
            FROM interactions
        """
        params = []
        
        if pack_id:
            query += " WHERE pack_id = ?"
            params.append(pack_id)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(lines)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            console.print("[yellow]Nenhum log encontrado.[/]")
            return
        
        # Display
        table = Table(title=f"📜 Últimos {len(rows)} Logs")
        table.add_column("Data/Hora", style="dim")
        table.add_column("Pack", style="cyan")
        table.add_column("Workflow", style="purple")
        table.add_column("Intenção", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Preview")
        
        for row in rows:
            created_at, pack, workflow, intent, status, preview = row
            # Format datetime
            try:
                dt = datetime.fromisoformat(created_at)
                dt_str = dt.strftime("%d/%m %H:%M")
            except:
                dt_str = str(created_at)[:16]
            
            table.add_row(
                dt_str,
                pack or "-",
                workflow or "-",
                intent or "-",
                status or "-",
                (preview or "")[:30] + "..." if preview and len(preview) > 30 else preview or "-"
            )
        
        console.print(table)
        
    except sqlite3.Error as e:
        console.print(f"[red]Erro ao ler logs: {e}[/]")
