"""
Test pierwszego wywołania disassemble - pozyskanie prawdziwego wipAssembleHistoryId
"""
import requests
import json
import os
from dotenv import load_dotenv

# Załaduj .env
load_dotenv()

def test_first_disassemble_call():
    print("=== Test pierwszego wywołania disassemble ===\n")
    
    # Dane z naszego testu
    parent_wip_id = 15198803
    child_wip_id = 14950305
    wip_process_step_history_id = 135465479
    entity_id = 14950305  # Z AssembledItems -> EntityId
    
    print(f"Parent WIP ID: {parent_wip_id}")
    print(f"Child WIP ID: {child_wip_id}")
    print(f"WipProcessStepHistoryId: {wip_process_step_history_id}")
    print(f"EntityId (z AssembledItems): {entity_id}\n")
    
    # Przygotuj headers
    user_context = json.loads(os.getenv('USER_CONTEXT', '{}'))
    mendix_token = os.getenv('MENDIX_TOKEN', '')
    
    headers = {
        'Content-Type': 'application/json',
        'UserContext': json.dumps(user_context),
        'MendixToken': mendix_token
    }
    
    print("Headers:")
    print(f"  UserContext: {json.dumps(user_context)}")
    print(f"  MendixToken: {mendix_token}\n")
    
    # Przygotuj body - PIERWSZE WYWOŁANIE
    # Twardo kodowane wipAssembleHistoryId = 1 (żeby przeszło i dostać właściwe ID)
    body = {
        "wipId": child_wip_id,
        "wipAssembleHistoryId": 1,
        "wipProcessStepHistoryId": wip_process_step_history_id
    }
    
    print("PIERWSZE WYWOŁANIE - Body (wipAssembleHistoryId=1):")
    print(json.dumps(body, indent=2))
    print()
    
    # URL
    base_url = os.getenv('PRD_MENDIX_API_URL')
    url = f"{base_url}/api/assembleall/{parent_wip_id}/disassemble"
    
    print(f"URL: {url}\n")
    
    # Wykonaj request
    print("Wysyłanie requestu...\n")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=body,
            verify=False
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}\n")
        
        if response.status_code == 200:
            print("✓ Sukces!\n")
            
            # Sprawdź czy odpowiedź jest JSON
            try:
                response_data = response.json()
                print("Response JSON:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                # Zapisz do pliku
                with open('first_disassemble_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                print("\n✓ Odpowiedź zapisana do: first_disassemble_response.json")
                
                # Szukaj wipAssembleHistoryId w odpowiedzi
                print("\n" + "="*70)
                print("ANALIZA ODPOWIEDZI:")
                if isinstance(response_data, dict):
                    if 'wipAssembleHistoryId' in response_data:
                        real_id = response_data['wipAssembleHistoryId']
                        print(f"✓ Znaleziono wipAssembleHistoryId: {real_id}")
                        print(f"\nDRUGIE WYWOŁANIE powinno użyć:")
                        print(f"  wipAssembleHistoryId: {real_id}")
                    else:
                        print("⚠ Brak 'wipAssembleHistoryId' w odpowiedzi")
                        print(f"Dostępne klucze: {list(response_data.keys())}")
                else:
                    print(f"⚠ Odpowiedź nie jest dictionary: {type(response_data)}")
                print("="*70)
                
            except json.JSONDecodeError:
                print("Response Text:")
                print(response.text)
        else:
            print("❌ Błąd!\n")
            print("Response Text:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_first_disassemble_call()
