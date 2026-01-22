"""
Configuration for WIP Unlink Application
Wszystkie dane pobierane z pliku .env dla bezpieczeństwa
"""

import os
import json
from dotenv import load_dotenv

# Załaduj zmienne z pliku .env
load_dotenv()

# Pobierz środowisko z .env
DEFAULT_ENVIRONMENT = os.getenv('ENVIRONMENT', 'STG')

# Pobierz Site Name z .env
SITE_NAME = os.getenv('SITE_NAME', 'Kwidzyn')

# Pobierz Mendix Token z .env
MENDIX_TOKEN = os.getenv('MENDIX_TOKEN', '')


def get_site_name():
    """Zwraca nazwę site"""
    return SITE_NAME


def get_env_config(env: str):
    """Pobiera konfigurację dla danego środowiska z .env"""
    if env not in ['STG', 'PRD']:
        raise ValueError(f"Nieprawidłowe środowisko: {env}. Użyj 'STG' lub 'PRD'")
    
    return {
        'external_api': {
            'base_url': os.getenv(f'{env}_EXTERNAL_API_URL'),
            'username': os.getenv('EXTERNAL_API_USERNAME'),
            'password': os.getenv('EXTERNAL_API_PASSWORD')
        },
        'mendix_api': {
            'base_url': os.getenv(f'{env}_MENDIX_API_URL'),
        }
    }


# Struktura środowisk - teraz dynamicznie z .env
ENVIRONMENTS = {
    'STG': get_env_config('STG'),
    'PRD': get_env_config('PRD')
}

# User Context (dla Mendix API) - pobiera z .env jako JSON
USER_CONTEXT = json.loads(os.getenv('USER_CONTEXT', '{}'))


def get_current_environment():
    """Zwraca aktualnie ustawione środowisko"""
    return DEFAULT_ENVIRONMENT


def set_environment(env: str):
    """
    Ustawia środowisko dla bieżącej sesji
    UWAGA: To nie zmienia .env, tylko zmienną w pamięci
    """
    global DEFAULT_ENVIRONMENT
    if env in ENVIRONMENTS:
        DEFAULT_ENVIRONMENT = env
        return True
    return False


def validate_config():
    """Sprawdza czy wszystkie wymagane zmienne środowiskowe są ustawione"""
    required_vars = [
        'ENVIRONMENT',
        'SITE_NAME',
        'STG_EXTERNAL_API_URL', 'PRD_EXTERNAL_API_URL',
        'STG_MENDIX_API_URL', 'PRD_MENDIX_API_URL',
        'EXTERNAL_API_USERNAME', 'EXTERNAL_API_PASSWORD',
        'USER_CONTEXT'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("⚠️  UWAGA: Brakujące zmienne w pliku .env:")
        for var in missing:
            print(f"   - {var}")
        print("\nSkopiuj .env.example do .env i uzupełnij dane!")
        return False
    
    return True
