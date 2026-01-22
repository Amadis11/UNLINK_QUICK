#!/usr/bin/env python3
"""
Test script - disassemble WIP (manual test)
Test z konkretnym body podanym przez użytkownika
"""

from api_client import MendixAPIClient
import os

def test_disassemble_manual():
    print("=== Test Disassemble API (Dwustopniowy) ===\n")
    
    # WIP ID rodzica (używany w URL)
    parent_wip_id = 4585913
    
    # Child WIP ID do odlinkowania
    child_wip_id = 4463232
    
    # WipProcessStepHistoryId (znany)
    wip_process_step_history_id = 30139162
    
    print(f"Parent WIP ID (URL): {parent_wip_id}")
    print(f"Child WIP ID (Body): {child_wip_id}")
    print(f"WipProcessStepHistoryId: {wip_process_step_history_id}\n")
    
    # Stwórz klienta Mendix
    client = MendixAPIClient('STG')
    
    # Sprawdź token z .env
    mendix_token_env = os.getenv('MENDIX_TOKEN', '')
    print(f"MendixToken z .env: {mendix_token_env if mendix_token_env else 'BRAK'}")
    
    # Jeśli token nie jest załadowany, ustaw go ręcznie
    if not client.mendix_token and mendix_token_env:
        print(f"Ustawiam token ręcznie...")
        client.set_mendix_token(mendix_token_env)
    
    print(f"Mendix API URL: {client.base_url}")
    print(f"MendixToken from client: {client.mendix_token if client.mendix_token else 'BRAK'}")
    print(f"UserContext: userId={client.user_context.get('userId')}, userName={client.user_context.get('userName')}\n")
    
    print("=== Dwustopniowy proces disassemble ===")
    print("Krok 1: Wywołanie z wipProcessStepHistoryId aby pobrać wipAssembleHistoryId")
    print("Krok 2: Wywołanie z pobranym wipAssembleHistoryId aby wykonać disassemble\n")
    
    # Wykonaj disassemble BEZ podawania wipAssembleHistoryId
    # Program sam wykona dwustopniowy proces
    print("Wywołanie disassemble...")
    result = client.disassemble_wip(
        parent_wip_id=parent_wip_id,
        child_wip_id=child_wip_id,
        wip_process_step_history_id=wip_process_step_history_id,
        auto_find_history=False  # Nie szukaj WipProcessStepHistoryId, użyj podanego
    )
    
    print("\n=== Wynik ===")
    if result['success']:
        print("✓ Sukces!")
        print(f"Status Code: {result['status_code']}")
        if result.get('response'):
            print(f"Response: {result['response']}")
    else:
        print("✗ Błąd!")
        print(f"Error: {result.get('error')}")
        print(f"Status Code: {result.get('status_code')}")
        if result.get('response'):
            print(f"Response: {result['response']}")

if __name__ == "__main__":
    test_disassemble_manual()
