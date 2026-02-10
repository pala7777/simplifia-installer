# SIMPLIFIA Installer

🚀 Instala packs de automação no OpenClawd em 1 minuto.

## Instalação

### Mac / Linux

```bash
curl -fsSL https://install.simplifia.com | bash
```

### Windows (PowerShell)

```powershell
irm https://install.simplifia.com | iex
```

### Via pip (manual)

```bash
pip install simplifia
```

## Uso

```bash
# Verificar ambiente
simplifia doctor

# Listar packs disponíveis
simplifia list

# Instalar um pack
simplifia install whatsapp

# Testar com exemplos (sem risco)
simplifia test whatsapp

# Ver status dos packs instalados
simplifia status

# Atualizar um pack
simplifia update whatsapp

# Atualizar todos os packs
simplifia update --all

# Ver logs de execução
simplifia logs
simplifia logs --pack whatsapp --lines 50
```

## Estrutura de Pastas

O installer cria/usa as seguintes pastas:

```
~/.simplifia/
├── installed.json    # Estado dos packs instalados
├── state.db          # SQLite com dados operacionais
└── cache/            # Cache de downloads

~/.openclawd/
├── workflows/simplifia/<pack>/   # Workflows executáveis
├── rules/simplifia/<pack>/       # Regras e configs
└── assets/simplifia/<pack>/      # Assets e templates
```

## Desenvolvimento

```bash
# Clone
git clone https://github.com/pala7777/simplifia-installer
cd simplifia-installer

# Instalar em modo dev
pip install -e .

# Rodar
simplifia --help
```

## License

MIT
