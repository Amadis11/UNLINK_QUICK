#!/usr/bin/env python3
"""
Test script - znalezienie WipProcessStepHistoryId dla operacji Assembly
"""

from api_client import ExternalAPIClient
from config import SITE_NAME

def test_find_assembly_operation():
    print("=== Test znajdowania operacji Assembly ===\n")
    
    # Stwórz klienta i autentykuj
    client = ExternalAPIClient('STG')
    
    if not client.authenticate():
        print("Nie udało się zaautentykować")
        return
    
    # Testowy serial number
    test_serial = "367499998250320140017728737910445"
    
    print(f"Site Name: {SITE_NAME}")
    print(f"Serial Number: {test_serial}\n")
    
    # 1. Pobierz WIP ID
    print("1. Pobieranie WIP ID...")
    wip_result = client.get_wip_id_by_serial_number(
        serial_number=test_serial,
        site_name=SITE_NAME
    )
    
    if not wip_result or len(wip_result) == 0:
        print("✗ Nie znaleziono WIP")
        return
    
    wip_id = wip_result[0].get('WipId')
    print(f"✓ WIP ID: {wip_id}\n")
    
    # 2. Pobierz operation histories
    print("2. Pobieranie operation histories...")
    operation_data = client.get_operation_histories(wip_id)
    
    if not operation_data:
        print("✗ Nie znaleziono operation histories")
        return
    
    print(f"Response keys: {list(operation_data.keys())}")
    print(f"Response: {operation_data}\n")
    
    wips = operation_data.get('Wips', [])
    if wips:
        wip = wips[0]
        operations = wip.get('OperationHistories', [])
        print(f"✓ Znaleziono {len(operations)} operacji\n")
        
        # Wyświetl operacje z AssembledItems
        print("3. Operacje z AssembledItems:")
        for op in operations:
            assembled_items = op.get('AssembledItems', [])
            if assembled_items:
                print(f"   RouteStep: {op.get('RouteStepName')}")
                print(f"   WipProcessStepHistoryId: {op.get('WipProcessStepHistoryId')}")
                print(f"   DateTime: {op.get('EndDateTime')}")
                print(f"   Assembled Items:")
                for item in assembled_items:
                    print(f"     - {item.get('Identifier')} (Material: {item.get('Material')}, EntityId: {item.get('EntityId')})")
                print()
    
    # 3. Znajdź automatycznie
    print("4. Automatyczne znalezienie WipProcessStepHistoryId:")
    history_id = client.find_assembly_operation(wip_id)
    
    if history_id:
        print(f"\n✓ Gotowe do disassemble z WipProcessStepHistoryId={history_id}")
    else:
        print("\n✗ Nie znaleziono odpowiedniej operacji")

if __name__ == "__main__":
    test_find_assembly_operation()
