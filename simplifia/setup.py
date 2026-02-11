"""Setup wizard - Initial configuration for SIMPLIFIA."""

import os
import json
from pathlib import Path

from .output import (
    print_header, print_ok, print_warn, print_info, print_next,
    print_divider, ask_choice, ask_input, ask_yes_no, IS_WINDOWS
)

if IS_WINDOWS:
    CONFIG_FILE = Path(os.environ.get('USERPROFILE', '~')) / ".simplifia" / "config.json"
else:
    CONFIG_FILE = Path.home() / ".simplifia" / "config.json"


def get_config() -> dict:
    """Load existing config or return empty dict."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}
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
        print("  [>] Modo nao-interativo: usando defaults")
        config = {
            "setup_complete": True,
            "mode": "iniciante",
            "provider": "openai",
            "api_key": "",
        }
        save_config(config)
        return True
    
    print_header("Bem-vindo ao SIMPLIFIA!")
    print("  Vamos configurar em poucos passos.")
    print("  (A IA e paga a parte - voce usa sua propria API key)")
    print("")
    
    config = get_config()
    
    # PERGUNTA 1: Modo
    print("--- Pergunta 1 de 3 ---")
    mode_idx = ask_choice(
        "Qual modo voce prefere?",
        ["Iniciante (recomendado)", "Avancado (todas as opcoes)"],
        default=0
    )
    mode = "avancado" if mode_idx == 1 else "iniciante"
    config["mode"] = mode
    advanced = (mode == "avancado")
    
    # PERGUNTA 2: Provider
    print("")
    print("--- Pergunta 2 de 3 ---")
    
    if advanced:
        provider_idx = ask_choice(
            "Qual provider de IA voce vai usar?",
            [
                "OpenAI (GPT-4, ChatGPT)",
                "Anthropic (Claude)",
                "OpenRouter (multiplos modelos)",
                "Ollama (local, gratis)",
                "Configurar depois"
            ],
            default=0
        )
        provider_map = ["openai", "anthropic", "openrouter", "ollama", "skip"]
        provider = provider_map[provider_idx]
    else:
        provider_idx = ask_choice(
            "Qual IA voce vai usar?",
            ["OpenAI (ChatGPT)", "Anthropic (Claude)", "Configurar depois"],
            default=0
        )
        provider_map = ["openai", "anthropic", "skip"]
        provider = provider_map[provider_idx]
    
    config["provider"] = provider
    
    # PERGUNTA 3: API Key
    print("")
    print("--- Pergunta 3 de 3 ---")
    
    if provider in ["ollama", "skip"]:
        if provider == "ollama":
            print_ok("Ollama nao precisa de API key")
            config["api_key"] = ""
        else:
            print_info("Voce pode configurar a API key depois com: simplifia setup --force")
            config["api_key"] = ""
    else:
        print(f"  Cole sua API key do {provider.title()}.")
        print("  (Se nao tiver agora, aperte Enter para pular)")
        print("")
        
        # Get API key URLs
        key_urls = {
            "openai": "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com/settings/keys",
            "openrouter": "https://openrouter.ai/keys"
        }
        if provider in key_urls:
            print_info(f"Pegue sua chave em: {key_urls[provider]}")
            print("")
        
        api_key = ask_input(f"API key ({provider})", secret=True)
        
        if api_key:
            config["api_key"] = api_key
            print_ok("API key salva")
        else:
            config["api_key"] = ""
            print_warn("Sem API key - voce pode adicionar depois")
            print_info("Execute: simplifia setup --force")
    
    # Mark complete
    config["setup_complete"] = True
    save_config(config)
    
    print_divider()
    print_ok("Configuracao concluida!")
    print("")
    print("  Proximos passos:")
    print("")
    print("      simplifia doctor           -> Verificar ambiente")
    print("      simplifia install whatsapp -> Instalar pack WhatsApp")
    print("")
    print_info("Lembrete: A IA (OpenAI/Claude) e paga a parte.")
    print_info("Voce controla seus gastos diretamente na conta deles.")
    print("")
    
    return True


def show_config():
    """Display current configuration."""
    config = get_config()
    
    if not config:
        print_warn("Nenhuma configuracao encontrada.")
        print_info("Use: simplifia setup")
        return
    
    print_header("Configuracao atual")
    
    # Hide sensitive data
    for key, value in config.items():
        display_value = value
        if "key" in key.lower() and value and len(str(value)) > 10:
            display_value = str(value)[:8] + "..."
        print(f"  {key}: {display_value}")
    
    print("")


def reset_config():
    """Reset configuration to defaults."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    print_ok("Configuracao resetada")
    print_info("Execute: simplifia setup")
