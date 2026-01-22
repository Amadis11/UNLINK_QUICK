#!/usr/bin/env python3
"""
Test script - pobieranie genealogii WIP po Serial Number
"""

from api_client import ExternalAPIClient
from config import SITE_NAME

def test_genealogy():
    print("=== Test genealogii WIP ===\n")
    
    # Stwórz klienta i autentykuj
    client = ExternalAPIClient('STG')
    
    if not client.authenticate():
        print("Nie udało się zaautentykować")
        return
    
    # Testowy serial number
    test_serial = "367499998250320140017728737910445"
    
    print(f"Site Name: {SITE_NAME}")
    print(f"Serial Number: {test_serial}\n")
    
    # 1. Pobierz WIP ID po Serial Number
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
    
    # 2. Pobierz genealogię
    print("2. Pobieranie genealogii...")
    genealogy = client.get_genealogy(wip_id)
    
    if not genealogy:
        print("✗ Nie znaleziono genealogii")
        return
    
    # Wyświetl genealogię
    if 'WipGenealogy' in genealogy:
        items = genealogy['WipGenealogy']
        print(f"✓ Znaleziono {len(items)} elementów w genealogii:\n")
        
        # Sortuj po Level (hierarchia)
        items_sorted = sorted(items, key=lambda x: x.get('Level', 0))
        
        for item in items_sorted:
            level = item.get('Level', 0)
            indent = "  " * level
            
            print(f"{indent}├─ Level {level}:")
            print(f"{indent}   WIP ID: {item.get('WipId')}")
            print(f"{indent}   Serial Number: {item.get('SerialNumber')}")
            print(f"{indent}   Material: {item.get('MaterialName')} (ID: {item.get('MaterialId')})")
            print(f"{indent}   Type: {item.get('PhoenixMaterialType')}")
            print(f"{indent}   Assembled: {item.get('AssembledDateTime')}")
            print(f"{indent}   Location: {item.get('AssembledLocation')}")
            
            # Pokaż parent relationship
            if item.get('ParentItemId') and item.get('ParentItemId') != 0:
                print(f"{indent}   Parent Item ID: {item.get('ParentItemId')}")
            
            # Pokaż data collections jeśli są
            dc = item.get('DataCollections', [])
            if dc and len(dc) > 0:
                print(f"{indent}   Data Collections: {len(dc)} entries")
            
            print()
    else:
        print("✗ Brak danych genealogii w odpowiedzi")
        print(f"Response keys: {list(genealogy.keys())}")

if __name__ == "__main__":
    test_genealogy()
