"""ASCII-safe output helpers for Windows compatibility."""

import os
import sys

# Detect Windows
IS_WINDOWS = os.name == 'nt'

# Force UTF-8 on Windows (but use ASCII-safe characters)
if IS_WINDOWS:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def print_header(title: str):
    """Print a header box."""
    width = max(len(title) + 4, 50)
    print("")
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    print("")


def print_section(title: str):
    """Print a section header."""
    print("")
    print(f"--- {title} ---")
    print("")


def print_ok(msg: str):
    """Print success message."""
    print(f"  [OK] {msg}")


def print_warn(msg: str):
    """Print warning message."""
    print(f"  [!] {msg}")


def print_error(msg: str):
    """Print error message."""
    print(f"  [X] {msg}")


def print_info(msg: str):
    """Print info message."""
    print(f"      {msg}")


def print_step(msg: str):
    """Print step message."""
    print(f"  [>] {msg}")


def print_next(msg: str):
    """Print next step recommendation."""
    print(f"  --> {msg}")


def print_divider():
    """Print a divider line."""
    print("")
    print("-" * 50)
    print("")


def ask_choice(prompt: str, options: list[str], default: int = 0) -> int:
    """Ask user to choose from options. Returns index."""
    print(f"\n{prompt}")
    for i, opt in enumerate(options):
        marker = "*" if i == default else " "
        print(f"  {marker} [{i+1}] {opt}")
    
    while True:
        try:
            response = input(f"\nEscolha [1-{len(options)}] (Enter = {default+1}): ").strip()
            if not response:
                return default
            choice = int(response) - 1
            if 0 <= choice < len(options):
                return choice
        except (ValueError, KeyboardInterrupt):
            pass
        print("  Opcao invalida. Tente novamente.")


def ask_input(prompt: str, default: str = "", secret: bool = False) -> str:
    """Ask for text input."""
    hint = f" [{default}]" if default else ""
    try:
        if secret:
            import getpass
            response = getpass.getpass(f"{prompt}{hint}: ")
        else:
            response = input(f"{prompt}{hint}: ")
        return response.strip() or default
    except (KeyboardInterrupt, EOFError):
        return default


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """Ask yes/no question."""
    hint = "[S/n]" if default else "[s/N]"
    try:
        response = input(f"{prompt} {hint}: ").strip().lower()
        if not response:
            return default
        return response in ('s', 'y', 'sim', 'yes')
    except (KeyboardInterrupt, EOFError):
        return default
