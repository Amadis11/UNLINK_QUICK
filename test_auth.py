#!/usr/bin/env python3
"""
Test script - pobieranie UserToken z External API
"""

from api_client import ExternalAPIClient

def test_authentication():
    print("=== Test autentykacji External API (STG) ===\n")
    
    # Stwórz klienta
    client = ExternalAPIClient('STG')
    
    print(f"URL: {client.base_url}")
    print(f"Username: {client.env_config['username']}")
    print(f"Password: {'*' * len(client.env_config['password'])}\n")
    
    # Spróbuj się zaautentykować
    print("Próba autentykacji...")
    if client.authenticate():
        print(f"\n✓ Sukces!")
        print(f"UserToken: {client.user_token[:50]}..." if len(client.user_token) > 50 else f"UserToken: {client.user_token}")
        return True
    else:
        print("\n✗ Błąd autentykacji")
        return False

if __name__ == "__main__":
    test_authentication()
