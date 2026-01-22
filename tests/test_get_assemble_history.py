"""
Test - szukanie wipAssembleHistoryId przez External API
"""
import requests
import json
from api_client import ExternalAPIClient

def test_get_assemble_history():
    print("=== Test pobierania wipAssembleHistoryId ===\n")
    
    parent_wip_id = 15198803
    child_wip_id = 14950305
    
    print(f"Parent WIP ID: {parent_wip_id}")
    print(f"Child WIP ID: {child_wip_id}\n")
    
    client = ExternalAPIClient('PRD')
    
    if not client.authenticate():
        print("❌ Błąd autentykacji")
        return
    
    print("✓ Autentykacja OK\n")
    
    # Próba 1: GET /api/Wips/{parent}/assemblehistory
    print("Próba 1: /api/Wips/{parent}/assemblehistory")
    try:
        url = f"{client.base_url}/api/Wips/{parent_wip_id}/assemblehistory"
        response = client.session.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            with open('assemblehistory_parent.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Zapisano do: assemblehistory_parent.json")
            print(f"Preview: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Błąd: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("\n" + "="*70 + "\n")
    
    # Próba 2: GET /api/Wips/{child}/assemblehistory
    print("Próba 2: /api/Wips/{child}/assemblehistory")
    try:
        url = f"{client.base_url}/api/Wips/{child_wip_id}/assemblehistory"
        response = client.session.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            with open('assemblehistory_child.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Zapisano do: assemblehistory_child.json")
            print(f"Preview: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Błąd: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_get_assemble_history()
