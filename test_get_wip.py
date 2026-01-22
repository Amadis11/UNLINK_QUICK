#!/usr/bin/env python3
"""
Test script - pobieranie WIP ID po Serial Number
"""

from api_client import ExternalAPIClient
from config import SITE_NAME

def test_get_wip_by_serial():
    print("=== Test pobierania WIP ID po Serial Number ===\n")
    
    # Stwórz klienta i autentykuj
    client = ExternalAPIClient('STG')
    
    if not client.authenticate():
        print("Nie udało się zaautentykować")
        return
    
    # Testowy serial number (możesz zmienić)
    test_serial = "367499998250320140017728737910445"
    
    print(f"Site Name: {SITE_NAME}")
    print(f"Serial Number: {test_serial}\n")
    
    print("Pobieranie WIP ID...")
    result = client.get_wip_id_by_serial_number(
        serial_number=test_serial,
        site_name=SITE_NAME
    )
    
    if result:
        print(f"\n✓ Znaleziono {len(result)} WIP(ów):\n")
        for wip in result:
            print(f"  WIP ID: {wip.get('WipId')}")
            print(f"  Serial Number: {wip.get('SerialNumber')}")
            print(f"  Customer: {wip.get('CustomerName')}")
            print(f"  Material: {wip.get('MaterialName')}")
            print(f"  Is Assembled: {wip.get('IsAssembled')}")
            if wip.get('Panel'):
                print(f"  Panel: {wip.get('Panel')}")
            print()
    else:
        print("\n✗ Nie znaleziono WIP")

if __name__ == "__main__":
    test_get_wip_by_serial()
