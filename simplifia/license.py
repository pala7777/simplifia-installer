"""License management for SimplifIA packs."""

import json
import os
from pathlib import Path
from typing import Optional
import httpx
import typer
from rich.console import Console

from .output import print_ok, print_warn, print_error, print_info, print_header, IS_WINDOWS

console = Console()


def require_session_or_exit() -> dict:
    """Require valid session token or exit with instructions.
    
    Returns:
        Manifest dict with entitlements and packs
        
    Raises:
        typer.Exit: If no auth or session invalid
    """
    from .auth import load_auth
    from .api import get_manifest, ApiError
    
    auth = load_auth()
    if not auth or not auth.session_token:
        console.print("[yellow]Ativacao necessaria.[/yellow]")
        console.print("1) Telegram: https://t.me/SimplifIABot")
        console.print("2) /ativar SEU-CODIGO")
        console.print("3) Depois: simplifia activate <TOKEN>")
        raise typer.Exit(code=2)
    
    try:
        return get_manifest(auth.session_token)
    except ApiError as e:
        if "UNAUTHORIZED" in str(e):
            console.print("[yellow]Sessao expirada ou invalida.[/yellow]")
            console.print("Execute novamente: simplifia activate <TOKEN>")
            raise typer.Exit(code=3)
        raise

# License API endpoint
LICENSE_API = "https://simplifia.vercel.app/api/license"

def get_license_path() -> Path:
    """Get path to license file."""
    if IS_WINDOWS:
        base = Path(os.environ.get('USERPROFILE', '~'))
    else:
        base = Path.home()
    return base / '.simplifia' / 'license.json'


def get_license() -> dict:
    """Load license from file."""
    path = get_license_path()
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def save_license(data: dict):
    """Save license to file."""
    path = get_license_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def get_entitlements() -> list[str]:
    """Get list of entitled packs from license."""
    license_data = get_license()
    return license_data.get('entitlements', [])


def is_pack_entitled(pack_id: str) -> bool:
    """Check if user has entitlement for a pack."""
    entitlements = get_entitlements()
    
    # Base is always available (or make it paid too)
    # For now, let's gate everything except 'base' (free tier)
    if pack_id == 'base':
        return True
    
    return pack_id in entitlements or 'all' in entitlements


def activate_license(code: str, email: str = "") -> tuple[bool, str, list[str]]:
    """Activate a license code.
    
    Args:
        code: The activation code
        email: Optional email for verification
        
    Returns:
        (success, message, entitlements)
    """
    try:
        response = httpx.post(
            f"{LICENSE_API}/activate",
            json={"code": code, "email": email},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Save license locally
            license_data = {
                "code": code,
                "email": email or data.get("email", ""),
                "entitlements": data.get("entitlements", []),
                "activated_at": data.get("activated_at", ""),
                "valid_until": data.get("valid_until", ""),
            }
            save_license(license_data)
            
            return True, data.get("message", "Licenca ativada!"), data.get("entitlements", [])
        
        elif response.status_code == 404:
            return False, "Codigo invalido ou ja utilizado.", []
        
        elif response.status_code == 403:
            return False, "Codigo expirado.", []
        
        else:
            return False, f"Erro ao ativar: {response.status_code}", []
            
    except httpx.TimeoutException:
        return False, "Timeout - verifique sua conexao.", []
    except Exception as e:
        return False, f"Erro: {e}", []


def verify_license() -> tuple[bool, list[str]]:
    """Verify current license with server.
    
    Returns:
        (valid, entitlements)
    """
    license_data = get_license()
    code = license_data.get("code")
    
    if not code:
        return False, []
    
    try:
        response = httpx.post(
            f"{LICENSE_API}/verify",
            json={"code": code},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            entitlements = data.get("entitlements", [])
            
            # Update local cache
            license_data["entitlements"] = entitlements
            save_license(license_data)
            
            return True, entitlements
        
        return False, []
        
    except Exception:
        # If offline, use cached entitlements
        return True, license_data.get("entitlements", [])


def run_activate(code: str = "", email: str = ""):
    """Run activation flow."""
    print_header("Ativar Licenca")
    
    if not code:
        print("  Cole seu codigo de ativacao.")
        print("  (Voce recebeu por email apos a compra)")
        print("")
        code = input("  Codigo: ").strip()
    
    if not code:
        print_warn("Codigo nao informado.")
        return False
    
    if not email:
        email = input("  Email (opcional): ").strip()
    
    print("")
    print("  [>] Verificando...")
    
    success, message, entitlements = activate_license(code, email)
    
    if success:
        print_ok(message)
        print("")
        print("  Packs liberados:")
        for pack in entitlements:
            print(f"      - {pack}")
        print("")
        print_info("Agora voce pode instalar: simplifia install <pack>")
        return True
    else:
        print_error(message)
        print_info("Compre em: https://simplifia.vercel.app/comprar")
        return False


def run_license_status():
    """Show current license status."""
    print_header("Status da Licenca")
    
    license_data = get_license()
    
    if not license_data.get("code"):
        print_warn("Nenhuma licenca ativada.")
        print_info("Ative com: simplifia activate <codigo>")
        print_info("Compre em: https://simplifia.vercel.app/comprar")
        return
    
    print_ok("Licenca ativa")
    print(f"      Email: {license_data.get('email', 'N/A')}")
    print(f"      Ativada em: {license_data.get('activated_at', 'N/A')}")
    print("")
    print("  Packs liberados:")
    for pack in license_data.get("entitlements", []):
        print(f"      - {pack}")
    print("")
    
    # Verify with server
    print("  [>] Verificando com servidor...")
    valid, entitlements = verify_license()
    
    if valid:
        print_ok("Licenca valida")
    else:
        print_warn("Nao foi possivel verificar (offline?)")


def check_entitlement_or_exit(pack_id: str) -> bool:
    """Check entitlement for a pack, exit if not entitled.
    
    Use this before installing a pack.
    Uses new token-based auth (Telegram) with fallback to legacy.
    """
    # Base is always allowed
    if pack_id == 'base':
        return True
    
    # Try new token-based auth first
    try:
        manifest = require_session_or_exit()
        entitlements = manifest.get("entitlements", [])
        
        if pack_id in entitlements or 'all' in entitlements:
            return True
        
        # Not entitled
        console.print(f"[red]Voce nao tem acesso ao pack '{pack_id}'.[/red]")
        console.print("")
        console.print(f"Seus packs: {', '.join(entitlements) if entitlements else '(nenhum)'}")
        console.print("Compre mais em: https://simplifia.com.br/comprar")
        return False
        
    except typer.Exit:
        raise  # Re-raise exit from require_session_or_exit
        
    except Exception:
        # Fall through to legacy check
        pass
    
    # Legacy check (old license.json system)
    if is_pack_entitled(pack_id):
        return True
    
    print_error(f"Voce nao tem acesso ao pack '{pack_id}'.")
    print("")
    print_info("Para liberar este pack:")
    print("      1. Compre em: https://simplifia.com.br/comprar")
    print("      2. Ative via Telegram: @SimplifIABot")
    print("      3. Execute: simplifia activate <TOKEN>")
    print("")
    
    return False
