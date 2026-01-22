#!/usr/bin/env python3
"""
Test script - szukanie wipAssembleHistoryId
"""

from api_client import ExternalAPIClient
from config import get_site_name
import json

def test_find_assembly_id():
    print("=== Test szukania wipAssembleHistoryId ===\n")
    
    # Stwórz klienta i autentykuj
    client = ExternalAPIClient('PRD')
    
    if not client.authenticate():
        print("❌ Nie udało się zaautentykować")
        return
    
    print("✓ Autentykacja OK\n")
    
    # Pierwszy serial number z pliku
    test_serial = "367499998260110020000578755002225"
    
    print(f"Site Name: {get_site_name()}")
    print(f"Serial Number: {test_serial}\n")
    
    # 1. Pobierz WIP ID po Serial Number
    print("KROK 1: Pobieranie Parent WIP ID...")
    wip_result = client.get_wip_id_by_serial_number(
        serial_number=test_serial,
        site_name=get_site_name()
    )
    
    if not wip_result or len(wip_result) == 0:
        print("❌ Nie znaleziono WIP")
        return
    
    parent_wip_id = wip_result[0].get('WipId')
    print(f"✓ Parent WIP ID: {parent_wip_id}\n")
    
    # 2. Pobierz genealogię
    print("KROK 2: Pobieranie genealogii...")
    genealogy = client.get_genealogy(parent_wip_id)
    
    if not genealogy or 'WipGenealogy' not in genealogy:
        print("❌ Nie znaleziono genealogii")
        return
    
    items = genealogy['WipGenealogy']
    children = [item for item in items if item.get('Level', 0) > 0]
    print(f"✓ Znaleziono {len(items)} pozycji w genealogii")
    print(f"✓ Dzieci (Level > 0): {len(children)}\n")
    
    if not children:
        print("❌ Brak dzieci")
        return
    
    # Wybierz pierwsze dziecko do testu
    child = children[0]
    child_wip_id = child.get('WipId')
    child_sn = child.get('SerialNumber')
    child_level = child.get('Level')
    
    print(f"TESTOWE DZIECKO:")
    print(f"  WipId: {child_wip_id}")
    print(f"  SerialNumber: {child_sn}")
    print(f"  Level: {child_level}\n")
    
    # 3. Pobierz operation histories dla PARENT
    print(f"KROK 3: Pobieranie operation histories dla PARENT WIP {parent_wip_id}...")
    operation_histories = client.get_operation_histories(parent_wip_id)
    
    if not operation_histories:
        print("❌ Nie znaleziono operation histories")
        return
    
    print(f"✓ Pobrano {len(operation_histories)} operation histories\n")
    
    # Zapisz do pliku dla analizy
    with open('operation_histories_debug.json', 'w', encoding='utf-8') as f:
        json.dump(operation_histories, f, indent=2, ensure_ascii=False)
    print("✓ Operation histories zapisane do: operation_histories_debug.json\n")
    
    # 4. find_assembly_idsembly operation dla tego dziecka
    print(f"KROK 4: Szukanie Assembly operation dla dziecka {child_wip_id}...")
    assembly_op = client.find_assembly_operation(operation_histories, child_wip_id)
    
    if assembly_op:
        print(f"✓ ZNALEZIONO Assembly operation!")
        print(f"\nSzczegóły:")
        print(f"  wipProcessStepHistoryId: {assembly_op.get('wipProcessStepHistoryId')}")
        print(f"  OperationName: {assembly_op.get('OperationName')}")
        print(f"  AssembledItems count: {len(assembly_op.get('AssembledItems', []))}")
        
        # Pokaż assembled items
        assembled_items = assembly_op.get('AssembledItems', [])
        print(f"\n  AssembledItems dla tego dziecka:")
        for idx, item in enumerate(assembled_items, 1):
            print(f"    [{idx}] ChildWipId: {item.get('ChildWipId')}")
            print(f"        wipAssembleHistoryId: {item.get('wipAssembleHistoryId')}")
            print(f"        ChildSerialNumber: {item.get('ChildSerialNumber')}")
            print(f"        ParentSerialNumber: {item.get('ParentSerialNumber')}")
    else:
        print(f"❌ NIE ZNALEZIONO Assembly operation dla dziecka {child_wip_id}")
        print(f"\nAnaliza wszystkich Assembly operations:")
        
        assembly_ops = [op for op in operation_histories if op.get('OperationName') == 'Assembly']
        print(f"Znaleziono {len(assembly_ops)} operacji Assembly\n")
        
        for idx, op in enumerate(assembly_ops[:3], 1):  # Pokaż pierwsze 3
            print(f"  [{idx}] wipProcessStepHistoryId: {op.get('wipProcessStepHistoryId')}")
            print(f"      AssembledItems: {len(op.get('AssembledItems', []))}")
            assembled_items = op.get('AssembledItems', [])
            if assembled_items:
                print(f"      Przykładowe ChildWipId: {assembled_items[0].get('ChildWipId')}")
                print(f"      Przykładowe wipAssembleHistoryId: {assembled_items[0].get('wipAssembleHistoryId')}")
            print()
        
        if len(assembly_ops) > 3:
            print(f"  ... i {len(assembly_ops) - 3} więcej Assembly operations\n")

if __name__ == "__main__":
    test_find_assembly_id()
