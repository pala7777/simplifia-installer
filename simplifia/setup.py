"""Setup wizard - Initial configuration for SIMPLIFIA."""

import os
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

CONFIG_FILE = Path.home() / ".simplifia" / "config.json"


def get_config() -> dict:
    """Load existing config or return empty dict."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict):
    """Save config to file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def is_configured() -> bool:
    """Check if initial setup was completed."""
    config = get_config()
    return config.get("setup_complete", False)


def run_setup(force: bool = False, advanced: bool = False):
    """Run the setup wizard.
    
    Args:
        force: Run even if already configured
        advanced: Show all options (default: beginner mode with 3 questions max)
    """
    if is_configured() and not force:
        return True
    
    # Check for non-interactive mode
    if os.environ.get("SIMPLIFIA_NONINTERACTIVE"):
        console.print("[yellow]Modo não-interativo: usando defaults[/]")
        config = {
            "setup_complete": True,
            "mode": "beginner",
            "llm_provider": "openai",
            "llm_configured": False,
        }
        save_config(config)
        return True
    
    console.print()
    console.print(Panel.fit(
        "[bold purple]🚀 Bem-vindo ao SIMPLIFIA![/]\n"
        "Vamos configurar em poucos passos.",
        border_style="purple"
    ))
    console.print()
    
    config = get_config()
    
    # PERGUNTA 1: Modo
    if not advanced:
        console.print("[bold]Pergunta 1 de 3[/]")
        mode = Prompt.ask(
            "Qual modo você prefere?",
            choices=["iniciante", "avancado"],
            default="iniciante"
        )
        advanced = (mode == "avancado")
        config["mode"] = mode
    else:
        config["mode"] = "avancado"
    
    console.print()
    
    # PERGUNTA 2: LLM Provider
    if advanced:
        console.print("[bold]Escolha seu provider de IA:[/]")
        console.print("  1. OpenAI (GPT-4, GPT-3.5)")
        console.print("  2. Anthropic (Claude)")
        console.print("  3. OpenRouter (múltiplos modelos)")
        console.print("  4. Ollama (local, grátis)")
        console.print("  5. Outro / Configurar depois")
        console.print()
        
        provider_choice = Prompt.ask(
            "Qual provider?",
            choices=["1", "2", "3", "4", "5"],
            default="1"
        )
        provider_map = {
            "1": "openai",
            "2": "anthropic", 
            "3": "openrouter",
            "4": "ollama",
            "5": "skip"
        }
        provider = provider_map[provider_choice]
    else:
        console.print("[bold]Pergunta 2 de 3[/]")
        provider = Prompt.ask(
            "Qual IA você vai usar?",
            choices=["openai", "anthropic", "outro"],
            default="openai"
        )
        if provider == "outro":
            provider = "skip"
    
    config["llm_provider"] = provider
    console.print()
    
    # PERGUNTA 3: API Key (if applicable)
    if provider not in ["ollama", "skip"]:
        if advanced:
            console.print(f"[bold]Cole sua API key do {provider.title()}:[/]")
            console.print("[dim](A chave fica salva localmente em ~/.simplifia/config.json)[/]")
        else:
            console.print("[bold]Pergunta 3 de 3[/]")
            console.print(f"[dim]Se não tiver a API key agora, aperte Enter para pular.[/]")
        
        api_key = Prompt.ask(
            f"API key ({provider})",
            default="",
            password=True
        )
        
        if api_key:
            config[f"{provider}_api_key"] = api_key
            config["llm_configured"] = True
            console.print("[green]✓ API key salva[/]")
        else:
            config["llm_configured"] = False
            console.print("[yellow]⚠ Sem API key - você pode adicionar depois[/]")
    elif provider == "ollama":
        config["llm_configured"] = True
        console.print("[green]✓ Ollama não precisa de API key[/]")
    else:
        config["llm_configured"] = False
    
    console.print()
    
    # Advanced-only questions
    if advanced:
        # OpenClawd path
        openclawd_default = str(Path.home() / ".openclawd")
        openclawd_path = Prompt.ask(
            "Pasta do OpenClawd",
            default=openclawd_default
        )
        config["openclawd_path"] = openclawd_path
        
        # Auto-update
        auto_update = Confirm.ask(
            "Verificar atualizações automaticamente?",
            default=True
        )
        config["auto_update"] = auto_update
        
        # Analytics
        analytics = Confirm.ask(
            "Enviar dados anônimos de uso (ajuda a melhorar)?",
            default=False
        )
        config["analytics"] = analytics
        console.print()
    
    # Mark as complete
    config["setup_complete"] = True
    save_config(config)
    
    console.print(Panel.fit(
        "[bold green]✓ Configuração concluída![/]\n\n"
        "Próximos passos:\n"
        "  [bold]simplifia doctor[/]  → Verificar ambiente\n"
        "  [bold]simplifia list[/]    → Ver packs disponíveis\n"
        "  [bold]simplifia install whatsapp[/] → Instalar pack",
        border_style="green"
    ))
    
    return True


def show_config():
    """Display current configuration."""
    config = get_config()
    
    if not config:
        console.print("[yellow]Nenhuma configuração encontrada.[/]")
        console.print("Use [bold]simplifia setup[/] para configurar.")
        return
    
    console.print(Panel.fit("[bold]Configuração atual[/]", border_style="purple"))
    
    # Hide sensitive data
    display_config = config.copy()
    for key in display_config:
        if "api_key" in key and display_config[key]:
            display_config[key] = display_config[key][:8] + "..."
    
    for key, value in display_config.items():
        console.print(f"  {key}: [cyan]{value}[/]")


def reset_config():
    """Reset configuration to defaults."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    console.print("[green]✓ Configuração resetada[/]")
