"""
Test pełnego flow - do momentu pobrania prawdziwego wipAssembleHistoryId
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_full_flow_to_assembly_id():
    print("=== Test pełnego flow do pobrania wipAssembleHistoryId ===\n")
    
    # Dane z pierwszego SN z hmi800.txt
    serial_number = "367499998260110020000578755002225"
    parent_wip_id = 15198803
    child_wip_id = 14950305
    wip_process_step_history_id = 135465479
    
    print(f"Serial Number: {serial_number}")
    print(f"Parent WIP ID: {parent_wip_id}")
    print(f"Child WIP ID: {child_wip_id}")
    print(f"WipProcessStepHistoryId: {wip_process_step_history_id}\n")
    
    # Headers
    user_context = json.loads(os.getenv('USER_CONTEXT', '{}'))
    mendix_token = os.getenv('MENDIX_TOKEN', '')
    
    headers = {
        'Content-Type': 'application/json',
        'UserContext': json.dumps(user_context),
        'MendixToken': mendix_token
    }
    
    # URL
    base_url = os.getenv('PRD_MENDIX_API_URL')
    url = f"{base_url}/api/assembleall/{parent_wip_id}/disassemble"
    
    # PIERWSZE WYWOŁANIE - z wipAssembleHistoryId=1
    body_first = {
        "wipId": child_wip_id,
        "wipAssembleHistoryId": 1,
        "wipProcessStepHistoryId": wip_process_step_history_id
    }
    
    print("="*70)
    print("PIERWSZE WYWOŁANIE")
    print("="*70)
    print(f"URL: {url}")
    print(f"\nBody:")
    print(json.dumps(body_first, indent=2))
    print("\nWysyłanie requestu...\n")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=body_first,
            verify=False
        )
        
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            print("✓ Sukces!\n")
            
            data = response.json()
            
            # Szukaj wipAssembleHistoryId w itemsAssembled
            if 'itemsAssembled' in data and len(data['itemsAssembled']) > 0:
                for item in data['itemsAssembled']:
                    if item.get('childWipId') == child_wip_id:
                        real_wip_assemble_history_id = item.get('wipAssembleHistoryId')
                        
                        print("="*70)
                        print("ZNALEZIONO PRAWDZIWE wipAssembleHistoryId!")
                        print("="*70)
                        print(f"childWipId: {item.get('childWipId')}")
                        print(f"wipAssembleHistoryId: {real_wip_assemble_history_id}")
                        print(f"serialNumberSubAssembly: {item.get('serialNumberSubAssembly')}")
                        print(f"material: {item.get('material')}")
                        print(f"mustBeRemoved: {item.get('mustBeRemoved')}")
                        print("="*70)
                        
                        # DRUGIE WYWOŁANIE - z prawdziwym wipAssembleHistoryId
                        body_second = {
                            "wipId": child_wip_id,
                            "wipAssembleHistoryId": real_wip_assemble_history_id,
                            "wipProcessStepHistoryId": wip_process_step_history_id
                        }
                        
                        print(f"\n{'='*70}")
                        print("DRUGIE WYWOŁANIE (NIE WYKONUJĘ - TYLKO POKAZUJĘ)")
                        print("="*70)
                        print(f"URL: {url}")
                        print(f"\nBody:")
                        print(json.dumps(body_second, indent=2))
                        print("\n⚠ To wywołanie wykonałoby rzeczywiste odlinkowanie!")
                        print("="*70)
                        
                        return
            
            print("⚠ Nie znaleziono dziecka w itemsAssembled")
            print(f"\nPełna odpowiedź:")
            print(json.dumps(data, indent=2))
            
        else:
            print(f"❌ Błąd: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_flow_to_assembly_id()
