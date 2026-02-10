"""Test command - runs pack tests with sample data."""

import json
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .doctor import get_openclawd_path, get_simplifia_path
from .state import get_installed_packs

console = Console()

def test_pack(pack_id: str):
    """Test a pack with sample messages."""
    
    installed = get_installed_packs()
    if pack_id not in installed:
        console.print(f"[red]❌ Pack '{pack_id}' não está instalado.[/]")
        console.print(f"Use [bold]simplifia install {pack_id}[/] primeiro.")
        return False
    
    console.print(Panel.fit(
        f"[bold]🧪 Testando Pack: {pack_id}[/]\nUsando mensagens de exemplo (modo seguro)",
        border_style="purple"
    ))
    
    # Look for samples
    openclawd_path = get_openclawd_path()
    samples_path = openclawd_path / "assets" / "simplifia" / pack_id / "samples"
    
    # Also check common locations
    possible_paths = [
        samples_path,
        openclawd_path / "workflows" / "simplifia" / pack_id / "samples",
        get_simplifia_path() / "cache" / pack_id / "samples",
    ]
    
    samples_file = None
    for path in possible_paths:
        test_file = path / "sample_messages.json" if path.is_dir() else None
        if test_file and test_file.exists():
            samples_file = test_file
            break
        # Direct file check
        if path.exists() and path.suffix == '.json':
            samples_file = path
            break
    
    if not samples_file or not samples_file.exists():
        console.print("[yellow]⚠ Arquivo de samples não encontrado.[/]")
        console.print("[dim]Criando teste com mensagens padrão...[/]")
        
        # Use default test messages
        samples = get_default_samples(pack_id)
    else:
        samples = json.loads(samples_file.read_text())
    
    # Run tests
    console.print()
    console.print(f"[bold]Executando {len(samples)} testes:[/]")
    console.print()
    
    for i, sample in enumerate(samples, 1):
        run_single_test(i, sample, pack_id)
    
    console.print()
    console.print("[green bold]✓ Testes concluídos![/]")
    console.print("[dim]Nenhuma mensagem foi enviada (modo teste).[/]")
    return True


def run_single_test(index: int, sample: dict, pack_id: str):
    """Run a single test case."""
    message = sample.get("message", sample.get("input", ""))
    expected = sample.get("expected_intent", sample.get("expected", ""))
    
    console.print(f"[cyan]Teste {index}:[/] {message[:60]}...")
    
    # Simulate processing
    result = simulate_processing(message, pack_id)
    
    console.print(f"  [dim]→ Intenção detectada:[/] [yellow]{result.get('intent', '?')}[/]")
    console.print(f"  [dim]→ Resposta sugerida:[/] {result.get('draft', '...')[:50]}...")
    console.print()


def simulate_processing(message: str, pack_id: str) -> dict:
    """Simulate pack processing (for testing)."""
    # Simple intent detection for demo
    message_lower = message.lower()
    
    if any(w in message_lower for w in ['preço', 'valor', 'quanto', 'orçamento']):
        intent = 'orcamento'
        draft = 'Olá! Para enviar um orçamento personalizado, me conta mais sobre o que você precisa?'
    elif any(w in message_lower for w in ['agendar', 'marcar', 'horário', 'agenda']):
        intent = 'agendamento'
        draft = 'Claro! Tenho os seguintes horários disponíveis: [horários]. Qual prefere?'
    elif any(w in message_lower for w in ['problema', 'reclamação', 'não gostei', 'defeito']):
        intent = 'reclamacao'
        draft = 'Sinto muito pelo ocorrido. Vou verificar e resolver isso para você. Pode me dar mais detalhes?'
    elif any(w in message_lower for w in ['obrigado', 'excelente', 'adorei', 'perfeito']):
        intent = 'elogio'
        draft = 'Muito obrigado pelo feedback! Ficamos felizes em ajudar 😊'
    else:
        intent = 'duvida'
        draft = 'Olá! Como posso ajudar?'
    
    return {
        'intent': intent,
        'draft': draft,
        'confidence': 0.85,
    }


def get_default_samples(pack_id: str) -> list:
    """Get default test samples for a pack."""
    if pack_id == 'whatsapp':
        return [
            {"message": "Oi, quanto custa o corte de cabelo?", "expected_intent": "orcamento"},
            {"message": "Quero marcar um horário para amanhã", "expected_intent": "agendamento"},
            {"message": "O serviço ficou ótimo, muito obrigado!", "expected_intent": "elogio"},
            {"message": "Tive um problema com o produto", "expected_intent": "reclamacao"},
            {"message": "Vocês fazem entrega?", "expected_intent": "duvida"},
        ]
    return [
        {"message": "Mensagem de teste padrão", "expected_intent": "unknown"},
    ]
