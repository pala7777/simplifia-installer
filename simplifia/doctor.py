"""Doctor command - verifies environment is ready."""

import json
import os
import shutil
import subprocess
from pathlib import Path

from .output import (
    print_header, print_ok, print_warn, print_error, 
    print_info, print_next, print_divider, IS_WINDOWS
)


def get_simplifia_path() -> Path:
    """Get SIMPLIFIA config path (cross-platform)."""
    if IS_WINDOWS:
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:
        base = Path.home()
    return base / '.simplifia'


def get_openclawd_path() -> Path:
    """Get OpenClawd base path (cross-platform).
    
    Note: This is kept for compatibility but OpenClawd is no longer required.
    SIMPLIFIA now uses ~/.simplifia as the primary installation path.
    """
    if IS_WINDOWS:
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:
        base = Path.home()
    return base / '.openclawd'


def check_docker_installed() -> bool:
    """Check if docker command exists."""
    return shutil.which('docker') is not None


def check_docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def check_runtime_running() -> bool:
    """Check if Clawdbot/OpenClaw runtime container is running.
    
    Checks by container status, not by folder existence.
    """
    try:
        # Check for any container with 'clawdbot' or 'openclaw' in name
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return False
        
        containers = result.stdout.lower()
        return 'clawdbot' in containers or 'openclaw' in containers
    except Exception:
        return False


def check_api_key_configured() -> tuple[bool, str]:
    """Check if API key is configured.
    
    Returns:
        (configured, provider) - tuple
    """
    config_path = get_simplifia_path() / 'config.json'
    if not config_path.exists():
        return False, ""
    
    try:
        config = json.loads(config_path.read_text())
        provider = config.get('provider', '')
        api_key = config.get('api_key', '')
        
        if api_key and len(api_key) > 10:
            return True, provider
        return False, provider
    except Exception:
        return False, ""


def get_next_step(docker_installed: bool, docker_running: bool, 
                  runtime_running: bool, api_key_ok: bool) -> str:
    """Determine the recommended next step."""
    
    if not docker_installed:
        return "Instale o Docker Desktop: https://docker.com/products/docker-desktop"
    
    if not docker_running:
        return "Abra o Docker Desktop e aguarde 'Docker is running'"
    
    if not runtime_running:
        return "Execute: simplifia clawdbot start"
    
    if not api_key_ok:
        return "Configure sua API key: simplifia setup"
    
    return "Instale um pack: simplifia install whatsapp"


def run_doctor() -> tuple[bool, bool, bool, bool]:
    """Run environment checks.
    
    Returns:
        (all_ok, docker_installed, docker_running, runtime_running)
    """
    print_header("SIMPLIFIA Doctor")
    
    # Ensure simplifia directory exists
    simplifia_path = get_simplifia_path()
    if not simplifia_path.exists():
        simplifia_path.mkdir(parents=True, exist_ok=True)
        (simplifia_path / 'cache').mkdir(exist_ok=True)
    
    # Check 1: SimplifIA installed (always true if running this)
    print_ok("SimplifIA instalado")
    
    # Check 2: Docker installed
    docker_installed = check_docker_installed()
    if docker_installed:
        print_ok("Docker instalado")
    else:
        print_warn("Docker NAO instalado")
    
    # Check 3: Docker running
    docker_running = False
    if docker_installed:
        docker_running = check_docker_running()
        if docker_running:
            print_ok("Docker rodando")
        else:
            print_warn("Docker instalado, mas NAO esta rodando")
    
    # Check 4: Runtime (container status)
    runtime_running = False
    if docker_running:
        runtime_running = check_runtime_running()
        if runtime_running:
            print_ok("Runtime rodando (container ativo)")
        else:
            print_warn("Runtime nao ativado")
    else:
        print_warn("Runtime nao ativado (faltou Docker)")
    
    # Check 5: API key
    api_key_ok, provider = check_api_key_configured()
    if api_key_ok:
        print_ok(f"API key configurada ({provider})")
    else:
        print_warn("API key nao configurada (opcional agora)")
    
    # Determine overall status
    all_ok = docker_installed and docker_running and runtime_running
    
    print_divider()
    
    # Next step recommendation
    next_step = get_next_step(docker_installed, docker_running, runtime_running, api_key_ok)
    print_next(f"Proximo passo recomendado: {next_step}")
    
    # Additional context messages
    print("")
    if not docker_installed:
        print_info("Docker Desktop e gratuito para uso pessoal.")
        print_info("Baixe em: https://docker.com/products/docker-desktop")
    elif not docker_running:
        print_info("Abra o Docker Desktop no menu Iniciar.")
        print_info("Aguarde aparecer 'Docker is running' na barra de tarefas.")
        print_info("Depois execute: simplifia doctor")
    elif not runtime_running:
        print_info("O runtime e o motor que executa suas automacoes.")
        print_info("Execute: simplifia clawdbot start")
    elif not api_key_ok:
        print_info("A IA (ChatGPT/Claude) e paga a parte - voce usa sua propria API key.")
        print_info("Configure com: simplifia setup")
        print_info("Ou pule por enquanto e configure depois.")
    else:
        print_info("Ambiente pronto! Instale um pack para comecar.")
    
    print("")
    print_info("Lembrete: A IA (OpenAI/Claude) e paga a parte pelo provedor.")
    print_info("Voce controla seus gastos diretamente na conta deles.")
    print("")
    
    return all_ok, docker_installed, docker_running, runtime_running
