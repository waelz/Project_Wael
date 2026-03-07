# Framework Config Manager

Outil Python pour développeurs de framework — gestion de configuration multi-environnement via YAML, validation et système de plugins.

## Structure du projet

```
Project_Wael/
├── config/
│   ├── framework.yaml     # Configuration de base
│   ├── dev.yaml           # Overrides environnement dev
│   └── prod.yaml          # Overrides environnement prod
├── framework/
│   ├── config_loader.py   # Chargement et fusion des configs YAML
│   ├── validator.py       # Validation de la configuration
│   └── plugin_manager.py  # Gestion des plugins
├── tests/
│   ├── test_config_loader.py
│   ├── test_validator.py
│   └── test_plugin_manager.py
├── requirements.txt
└── pytest.ini
```

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```python
from framework import load_config, validate_config, PluginManager

# Charger la configuration d'un environnement
config = load_config(env="dev")   # ou "prod"

# Valider la configuration
errors = validate_config(config)
if errors:
    for err in errors:
        print(f"[ERREUR] {err}")

# Utiliser le gestionnaire de plugins
pm = PluginManager()
pm.register("auth", lambda opts: {"token_expiry": opts.get("token_expiry", 3600)})
pm.load_from_config(config)

auth = pm.get("auth")
print(pm.list_active())
```

## Lancer les tests

```bash
pytest
```

## Concepts

### config_loader — Fusion de configs YAML
La fonction `load_config(env)` charge `framework.yaml` (base) puis fusionne les valeurs de `{env}.yaml` par-dessus via `deep_merge`. Les clés imbriquées sont fusionnées récursivement ; les listes sont remplacées.

### validator — Validation de structure
`validate_config(config)` vérifie la présence des champs requis, la validité du `log_level`, des ports et des workers. Retourne une liste d'erreurs (vide si OK).

### plugin_manager — Plugins pilotés par la config
`PluginManager` permet d'enregistrer des handlers Python sous un nom, puis de les activer automatiquement selon les entrées `plugins` du YAML (`enabled: true`).
