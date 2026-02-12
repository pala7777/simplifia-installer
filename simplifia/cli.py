"""SIMPLIFIA CLI - Main entry point."""

import os
import typer

from . import __version__
from .output import print_header, print_ok, print_warn, print_info, print_next, print_divider

app = typer.Typer(
    name="simplifia",
    help="SIMPLIFIA - Automacao sem codigo com IA",
    add_completion=False,
)


def version_callback(value: bool):
    if value:
        print(f"SIMPLIFIA v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Mostra a versao"
    ),
):
    """SIMPLIFIA - Automacao sem codigo com IA."""
    pass


@app.command()
def setup(
    advanced: bool = typer.Option(False, "--advanced", "-a", help="Modo avancado"),
    force: bool = typer.Option(False, "--force", "-f", help="Reconfigurar"),
):
    """Configura SIMPLIFIA (wizard inicial)."""
    from .setup import run_setup
    run_setup(force=force, advanced=advanced)


@app.command()
def config():
    """Mostra configuracao atual."""
    from .setup import show_config
    show_config()


@app.command("config-reset")
def config_reset():
    """Reseta configuracao para padroes."""
    from .setup import reset_config
    reset_config()


@app.command()
def doctor(
    auto_install: bool = typer.Option(True, "--auto-install/--no-auto-install", 
                                       help="Auto-instalar runtime se Docker disponivel"),
):
    """Verifica se o ambiente esta pronto."""
    from .setup import is_configured, run_setup
    from .doctor import run_doctor
    
    # Ensure setup was done
    if not is_configured():
        run_setup()
    
    all_ok, docker_installed, docker_running, runtime_running = run_doctor()
    
    # Auto-install runtime if Docker is running but runtime not
    if auto_install and docker_running and not runtime_running:
        print("")
        print("  [>] Docker detectado! Instalando motor automaticamente...")
        
        from .clawdbot import clawdbot_install, clawdbot_start
        
        os.environ['SIMPLIFIA_NONINTERACTIVE'] = '1'
        
        try:
            clawdbot_install(use_docker=True)
            clawdbot_start()
            print_ok("Motor Clawdbot instalado e iniciado!")
        except Exception as e:
            print_warn(f"Nao foi possivel instalar automaticamente: {e}")
            print_info("Execute manualmente: simplifia clawdbot install --docker")


@app.command("list")
def list_available():
    """Lista packs disponiveis."""
    from .registry import list_packs
    list_packs()


@app.command()
def activate(
    token: str = typer.Argument(..., help="Token do Telegram (/ativar CODE)"),
    fingerprint: str = typer.Option(None, "--fingerprint", help="Device fingerprint override"),
):
    """Ativa SimplifIA nesta maquina usando token do Telegram."""
    from rich.console import Console
    from rich.table import Table
    from .auth import save_auth
    from .api import activate_token, default_fingerprint, ApiError
    
    console = Console()
    
    try:
        fp = fingerprint or default_fingerprint()
        resp = activate_token(token=token, device_fingerprint=fp)
        
        save_auth(
            session_token=resp.session_token,
            entitlements=resp.entitlements,
            product=resp.product,
            niche=resp.niche,
        )
        
        table = Table(title="SimplifIA Ativado ✅")
        table.add_column("Campo")
        table.add_column("Valor")
        table.add_row("Produto", str(resp.product or "-"))
        table.add_row("Nicho", str(resp.niche or "-"))
        table.add_row("Packs", ", ".join(resp.entitlements) if resp.entitlements else "(nenhum)")
        console.print(table)
        console.print("\n  Proximo: [bold]simplifia install <pack>[/bold]")
        
    except ApiError as e:
        console.print(f"[red]Erro de ativacao:[/red] {e}")
        console.print("\nPegue um token no Telegram: https://t.me/SimplifIABot → /ativar CODIGO")
        raise typer.Exit(code=1)


@app.command("activate-code")
def activate_code(
    code: str = typer.Argument(None, help="Codigo de ativacao"),
    email: str = typer.Option("", "--email", "-e", help="Email (opcional)"),
):
    """Ativa via codigo (metodo antigo, use 'activate' com token do Telegram)."""
    from .license import run_activate
    run_activate(code or "", email)


@app.command()
def license():
    """Mostra status da licenca."""
    from .license import run_license_status
    run_license_status()


@app.command()
def install(
    pack: str = typer.Argument(..., help="Nome do pack (ex: whatsapp)"),
    force: bool = typer.Option(False, "--force", "-f", help="Reinstalar"),
):
    """Instala um pack."""
    from .setup import is_configured, run_setup
    from .install import install_pack
    from .license import check_entitlement_or_exit
    
    if not is_configured():
        run_setup()
    
    # Check entitlement before installing
    if not check_entitlement_or_exit(pack):
        return
    
    install_pack(pack, force=force)


@app.command()
def update(
    pack: str = typer.Argument(None, help="Nome do pack (ou --all)"),
    all_packs: bool = typer.Option(False, "--all", "-a", help="Atualiza todos"),
):
    """Atualiza um pack (ou todos)."""
    from .update import update_pack
    update_pack(pack, all_packs=all_packs)


@app.command()
def status():
    """Mostra status da ativacao, link e packs instalados."""
    from rich.console import Console
    from rich.table import Table
    from .auth import load_auth
    from .api import get_link_status, ApiError
    from .state import get_installed_packs, get_pack_status
    
    console = Console()
    auth = load_auth()
    
    # 1. Activation status
    print_header("Status SimplifIA")
    
    if not auth:
        print_warn("Nao ativado.")
        print_info("Execute: fale com @SimplifIABot → /meuacesso → simplifia activate <TOKEN>")
        return
    
    table = Table(title="Ativacao")
    table.add_column("Campo")
    table.add_column("Valor")
    table.add_row("Produto", auth.product or "-")
    table.add_row("Nicho", auth.niche or "-")
    table.add_row("Packs", ", ".join(auth.entitlements) if auth.entitlements else "(nenhum)")
    table.add_row("Ativado em", auth.created_at or "-")
    console.print(table)
    
    # 2. Device link status
    print("")
    try:
        link_status = get_link_status(auth.session_token)
        if link_status.linked:
            print_ok(f"Dispositivo vinculado ✅ (codigo: ...{link_status.link_code_last4})")
            if link_status.claimed_at:
                print_info(f"  Vinculado em: {link_status.claimed_at[:10]}")
        else:
            print_warn("Dispositivo nao vinculado ao site.")
            print_info("Execute: simplifia link")
    except ApiError as e:
        if "UNAUTHORIZED" in str(e):
            print_warn("Sessao expirada. Execute: simplifia activate <TOKEN>")
        else:
            print_warn(f"Erro ao verificar link: {e}")
    
    # 3. Installed packs
    print("")
    installed = get_installed_packs()
    
    if not installed:
        print_warn("Nenhum pack instalado ainda.")
        print_info("Use: simplifia install whatsapp")
        return
    
    print_header("Packs Instalados")
    
    for pack_id, info in installed.items():
        pack_status = get_pack_status(pack_id)
        print(f"  {info.get('name', pack_id)}")
        print(f"      Versao: {info.get('version', '?')}")
        print(f"      Status: {pack_status}")
        print(f"      Instalado: {info.get('installed_at', '?')}")
        print("")


@app.command()
def link():
    """Vincula este computador ao Assistente Web."""
    import platform
    from datetime import datetime
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from .auth import load_auth
    from .api import start_device_link, ApiError, default_fingerprint
    from . import __version__
    
    console = Console()
    auth = load_auth()
    
    if not auth:
        print_warn("Ative primeiro!")
        print_info("Fale com @SimplifIABot e rode: simplifia activate <TOKEN>")
        raise typer.Exit(code=2)
    
    try:
        # Get link code
        resp = start_device_link(
            session_token=auth.session_token,
            device_fingerprint=default_fingerprint(),
            cli_version=__version__,
            os_name=platform.system().lower(),
        )
        
        # Parse expiration
        try:
            exp_dt = datetime.fromisoformat(resp.expires_at.replace('Z', '+00:00'))
            now = datetime.now(exp_dt.tzinfo)
            minutes_left = int((exp_dt - now).total_seconds() / 60)
            exp_text = f"{minutes_left} minutos" if minutes_left > 0 else "agora"
        except Exception:
            exp_text = "10 minutos"
        
        # Build panel
        content = Text()
        content.append("\n")
        content.append("Codigo: ", style="bold")
        content.append(f"{resp.link_code}", style="bold cyan on dark_blue")
        content.append("\n\n")
        content.append("Acesse: ", style="bold")
        content.append(resp.url, style="underline blue")
        content.append("\n\n")
        content.append(f"Expira em: {exp_text}\n", style="dim")
        
        panel = Panel(
            content,
            title="[bold green]Conectar ao Assistente Web[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        console.print(panel)
        
        # Windows tip
        if platform.system() == "Windows":
            print_info("Dica: Selecione o codigo e pressione Ctrl+C para copiar.")
        
    except ApiError as e:
        if "UNAUTHORIZED" in str(e):
            print_warn("Sessao expirada.")
            print_info("Execute: simplifia activate <TOKEN>")
            raise typer.Exit(code=2)
        elif "RATE_LIMITED" in str(e):
            print_warn("Muitas tentativas. Aguarde alguns minutos.")
            raise typer.Exit(code=1)
        else:
            print_warn(f"Erro: {e}")
            raise typer.Exit(code=1)


@app.command()
def uninstall(
    pack: str = typer.Argument(..., help="Nome do pack"),
    keep_data: bool = typer.Option(False, "--keep-data", help="Manter dados"),
):
    """Remove um pack instalado."""
    from .uninstall import uninstall_pack
    uninstall_pack(pack, keep_data=keep_data)


@app.command()
def test(
    pack: str = typer.Argument(..., help="Nome do pack"),
):
    """Testa um pack com exemplos (sem risco)."""
    from .test import test_pack
    test_pack(pack)


@app.command()
def logs(
    pack: str = typer.Argument(None, help="Filtrar por pack"),
    lines: int = typer.Option(20, "--lines", "-n", help="Numero de linhas"),
):
    """Mostra logs de execucao."""
    from .logs import show_logs
    show_logs(pack, lines)


# ============================================================
# WHATSAPP SUBCOMMANDS
# ============================================================

whatsapp_app = typer.Typer(
    name="whatsapp",
    help="Comandos do pack WhatsApp",
)
app.add_typer(whatsapp_app, name="whatsapp")


@whatsapp_app.command("next")
def whatsapp_next():
    """Mostra o que fazer depois de instalar o pack WhatsApp."""
    print_header("Pack WhatsApp - Proximos Passos")
    
    print("  Voce instalou o pack WhatsApp. Agora:")
    print("")
    print("  1. CONECTAR O WHATSAPP")
    print("     - O pack usa o WhatsApp Web via QR code")
    print("     - Na primeira execucao, escaneie o QR code com seu celular")
    print("     - Recomendacao: use um numero de telefone dedicado para negocios")
    print("")
    print("  2. MODO SEGURO (padrao)")
    print("     - Todas as mensagens sao RASCUNHOS primeiro")
    print("     - Voce APROVA antes de enviar")
    print("     - Nada e enviado automaticamente sem sua permissao")
    print("")
    print("  3. TESTAR SEM RISCO")
    print("     - Execute: simplifia test whatsapp")
    print("     - Isso simula mensagens sem enviar nada de verdade")
    print("")
    print("  4. WORKFLOWS INCLUSOS")
    print("     - Triagem automatica (FAQ + encaminhamento)")
    print("     - Agendamento + confirmacao + lembretes")
    print("     - Orcamento rapido")
    print("     - Pos-venda + pedido de avaliacao")
    print("     - Recuperacao de clientes sumidos")
    print("")
    print("  5. REGRAS DE SEGURANCA")
    print("     - Rate limit: maximo 1 msg/minuto por contato")
    print("     - Anti-spam: nunca repita a mesma mensagem")
    print("     - Sempre peca permissao antes de enviar promocoes")
    print("")
    
    print_divider()
    print_next("Execute: simplifia test whatsapp")
    print("")
    print_info("Lembrete: A IA (OpenAI/Claude) e paga a parte.")
    print_info("Voce controla seus gastos diretamente na conta deles.")
    print("")


@whatsapp_app.command("status")
def whatsapp_status():
    """Mostra status do pack WhatsApp."""
    from .state import get_installed_packs
    
    installed = get_installed_packs()
    
    if 'whatsapp' not in installed:
        print_warn("Pack WhatsApp nao instalado.")
        print_info("Execute: simplifia install whatsapp")
        return
    
    info = installed['whatsapp']
    print_header("Pack WhatsApp - Status")
    print(f"  Versao: {info.get('version', '?')}")
    print(f"  Instalado em: {info.get('installed_at', '?')}")
    print("")
    print_info("Para ver proximos passos: simplifia whatsapp next")
    print("")


# ============================================================
# CLAWDBOT SUBCOMMANDS
# ============================================================

clawdbot_app = typer.Typer(
    name="clawdbot",
    help="Gerenciar Clawdbot (Docker)",
)
app.add_typer(clawdbot_app, name="clawdbot")


@clawdbot_app.command("doctor")
def clawdbot_doctor_cmd():
    """Verifica se Docker esta pronto."""
    from .clawdbot import clawdbot_doctor
    clawdbot_doctor()


@clawdbot_app.command("install")
def clawdbot_install_cmd(
    docker: bool = typer.Option(True, "--docker", "-d", help="Instalar via Docker"),
):
    """Instala Clawdbot via Docker."""
    from .clawdbot import clawdbot_install
    clawdbot_install(use_docker=docker)


@clawdbot_app.command("start")
def clawdbot_start_cmd():
    """Inicia o container do Clawdbot."""
    from .clawdbot import clawdbot_start
    clawdbot_start()


@clawdbot_app.command("stop")
def clawdbot_stop_cmd():
    """Para o container do Clawdbot."""
    from .clawdbot import clawdbot_stop
    clawdbot_stop()


@clawdbot_app.command("status")
def clawdbot_status_cmd():
    """Mostra status do Clawdbot."""
    from .clawdbot import clawdbot_status
    clawdbot_status()


@clawdbot_app.command("logs")
def clawdbot_logs_cmd(
    lines: int = typer.Option(50, "--lines", "-n", help="Numero de linhas"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Seguir logs"),
):
    """Mostra logs do Clawdbot."""
    from .clawdbot import clawdbot_logs
    clawdbot_logs(lines=lines, follow=follow)


@clawdbot_app.command("update")
def clawdbot_update_cmd():
    """Atualiza Clawdbot para ultima versao."""
    from .clawdbot import clawdbot_update
    clawdbot_update()


@clawdbot_app.command("uninstall")
def clawdbot_uninstall_cmd():
    """Remove Clawdbot."""
    from .clawdbot import clawdbot_uninstall
    clawdbot_uninstall()


if __name__ == "__main__":
    app()
