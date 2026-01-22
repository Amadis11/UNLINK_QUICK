"""
API Client dla komunikacji z Mendix API i External API
Obsługuje autentykację i requesty do obu endpointów
"""

import requests
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config import ENVIRONMENTS, USER_CONTEXT, MENDIX_TOKEN, MENDIX_TOKEN

# Wyłącz ostrzeżenia SSL (dla korporacyjnych proxy/certyfikatów)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ExternalAPIClient:
    """Klient dla External API - do pobierania genealogii WIP"""
    
    TOKEN_CACHE_FILE = '.token_cache.json'
    TOKEN_VALID_HOURS = 8
    
    def __init__(self, environment: str = 'STG'):
        self.environment = environment
        self.env_config = ENVIRONMENTS[environment]['external_api']
        self.base_url = self.env_config['base_url']
        self.session = requests.Session()
        self.session.auth = (self.env_config['username'], self.env_config['password'])
        self.session.verify = False  # Wyłącz weryfikację SSL dla korporacyjnego proxy
        self.user_token = None
        
        # Spróbuj załadować token z cache
        self._load_cached_token()
    
    def _load_token_cache(self) -> Dict:
        """Ładuje cache tokenów z pliku JSON"""
        if os.path.exists(self.TOKEN_CACHE_FILE):
            try:
                with open(self.TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_token_cache(self, cache: Dict):
        """Zapisuje cache tokenów do pliku JSON"""
        try:
            with open(self.TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"⚠ Nie udało się zapisać cache tokenu: {e}")
    
    def _load_cached_token(self):
        """Ładuje token z cache jeśli jest ważny (max 8h)"""
        cache = self._load_token_cache()
        
        if self.environment in cache:
            token_data = cache[self.environment]
            cached_token = token_data.get('token')
            cached_timestamp = token_data.get('timestamp')
            
            if cached_token and cached_timestamp:
                try:
                    token_time = datetime.fromisoformat(cached_timestamp)
                    hours_old = (datetime.now() - token_time).total_seconds() / 3600
                    
                    # Token ważny 8h
                    if hours_old < self.TOKEN_VALID_HOURS:
                        self.user_token = cached_token
                        self._set_token_cookie(cached_token)
                        print(f"✓ Używam cache'owanego tokenu (ważny jeszcze {self.TOKEN_VALID_HOURS - int(hours_old)}h)")
                        return True
                    else:
                        print(f"⚠ Token wygasł ({int(hours_old)}h temu) - wymagana nowa autentykacja")
                except Exception as e:
                    print(f"⚠ Błąd podczas ładowania cache: {e}")
        return False
    
    def _save_token_to_cache(self, token: str):
        """Zapisuje token do cache z timestampem"""
        cache = self._load_token_cache()
        
        cache[self.environment] = {
            'token': token,
            'timestamp': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=self.TOKEN_VALID_HOURS)).isoformat()
        }
        
        self._save_token_cache(cache)
    
    def _set_token_cookie(self, token: str):
        """Ustawia token w ciastkach - token już zawiera 'UserToken=' prefix"""
        # Token przychodzi w formacie "UserToken=BQAAAA..."
        # Musimy wyciągnąć wartość po znaku =
        if '=' in token:
            cookie_value = token.split('=', 1)[1]
        else:
            cookie_value = token
        
        self.session.cookies.set('UserToken', cookie_value)
    
    def authenticate(self, force: bool = False) -> bool:
        """
        Pobiera UserToken przez AD sign in
        Używa Basic Authorization (username/password)
        Token jest cache'owany na 8h w pliku .token_cache.json
        
        Args:
            force: Wymuś nową autentykację nawet jeśli token jest w cache
            
        Returns:
            True jeśli autentykacja się powiodła, False w przeciwnym razie
        """
        # Jeśli mamy ważny token i nie wymuszamy, użyj go
        if not force and self.user_token:
            return True
        
        try:
            url = f"{self.base_url}/api/user/adsignin"
            response = self.session.get(url)
            response.raise_for_status()
            
            # Token jest zwracany jako text/plain w formacie "UserToken=BQAAAA..."
            self.user_token = response.text.strip()
            
            # Ustaw token w ciastkach
            self._set_token_cookie(self.user_token)
            
            # Zapisz do cache
            self._save_token_to_cache(self.user_token)
            
            print(f"✓ Autentykacja udana - otrzymano nowy UserToken (ważny 8h)")
            return True
        except requests.exceptions.RequestException as e:
            print(f"✗ Błąd podczas autentykacji: {e}")
            return False
    
    def set_user_token(self, token: str):
        """Ustawia UserToken ręcznie (jeśli masz token z innego źródła)"""
        self.user_token = token
        self._set_token_cookie(token)
    
    def get_genealogy(self, wip_id: int) -> Optional[Dict]:
        """
        Pobiera genealogię WIP - listę wszystkich zlinkowanych elementów
        
        Args:
            wip_id: ID WIP do sprawdzenia
            
        Returns:
            Dict z genealogią lub None w przypadku błędu
        """
        try:
            url = f"{self.base_url}/api/Wips/{wip_id}/genealogy"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania genealogii dla WIP {wip_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response: {e.response.text[:200]}")
            return None
    
    def get_wip_info(self, wip_id: int) -> Optional[Dict]:
        """Pobiera informacje o WIP"""
        try:
            url = f"{self.base_url}/wip/{wip_id}"  # TODO: Verify endpoint
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania info o WIP {wip_id}: {e}")
            return None
    
    def get_wip_id_by_serial_number(self, serial_number: str, site_name: str, 
                                    customer_name: str = None, material_name: str = None) -> Optional[List[Dict]]:
        """
        Pobiera WIP ID po Serial Number
        
        Args:
            serial_number: Numer seryjny WIP (obowiązkowe)
            site_name: Nazwa site (obowiązkowe)
            customer_name: Nazwa klienta (opcjonalne)
            material_name: Nazwa materiału (opcjonalne)
            
        Returns:
            Lista Dict z WIP ID i dodatkowymi informacjami lub None w przypadku błędu
        """
        try:
            url = f"{self.base_url}/api/Wips/GetWipIdBySerialNumber"
            
            # Przygotuj parametry
            params = {
                'SiteName': site_name,
                'SerialNumber': serial_number
            }
            
            if customer_name:
                params['CustomerName'] = customer_name
            if material_name:
                params['MaterialName'] = material_name
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania WIP ID dla SN {serial_number}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response Headers: {dict(e.response.headers)}")
                print(f"Response Body: {e.response.text}")
            return None
    
    def get_operation_histories(self, wip_id: int) -> Optional[Dict]:
        """
        Pobiera historię operacji WIP (OperationHistories)
        
        Args:
            wip_id: ID WIP
            
        Returns:
            Dict z historią operacji lub None w przypadku błędu
        """
        try:
            url = f"{self.base_url}/api/Wips/{wip_id}/operationhistories"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas pobierania operation histories dla WIP {wip_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response: {e.response.text[:200]}")
            return None
    
    def find_assembly_operation(self, wip_id: int) -> Optional[int]:
        """
        Znajduje WipProcessStepHistoryId dla ostatniej operacji Assembly z AssembledItems
        
        Args:
            wip_id: ID WIP
            
        Returns:
            WipProcessStepHistoryId lub None jeśli nie znaleziono
        """
        operation_data = self.get_operation_histories(wip_id)
        
        if not operation_data or 'Wips' not in operation_data:
            return None
        
        wips = operation_data['Wips']
        if not wips or len(wips) == 0:
            return None
        
        wip = wips[0]
        operations = wip.get('OperationHistories', [])
        
        # Szukaj operacji z AssembledItems (od najnowszej)
        for operation in reversed(operations):
            assembled_items = operation.get('AssembledItems', [])
            if assembled_items and len(assembled_items) > 0:
                wip_process_step_history_id = operation.get('WipProcessStepHistoryId')
                if wip_process_step_history_id:
                    print(f"✓ Znaleziono operację Assembly: RouteStep='{operation.get('RouteStepName')}', WipProcessStepHistoryId={wip_process_step_history_id}")
                    print(f"  Assembled Items: {len(assembled_items)} elementów")
                    return wip_process_step_history_id
        
        print(f"⚠ Nie znaleziono operacji Assembly z AssembledItems dla WIP {wip_id}")
        return None


class MendixAPIClient:
    """Klient dla Mendix API - do odlinkowania WIP"""
    
    def __init__(self, environment: str = 'STG'):
        self.environment = environment
        self.env_config = ENVIRONMENTS[environment]['mendix_api']
        self.base_url = self.env_config['base_url']
        self.session = requests.Session()
        self.session.verify = False  # Wyłącz weryfikację SSL dla korporacyjnego proxy
        self.mendix_token = MENDIX_TOKEN if MENDIX_TOKEN else None
        self.user_context = USER_CONTEXT
    
    def set_mendix_token(self, token: str):
        """Ustawia MendixToken w headerach"""
        self.mendix_token = token
        self.session.headers.update({'MendixToken': token})
    
    def set_user_context(self, user_context: Dict):
        """Ustawia user context"""
        self.user_context = user_context
    
    def disassemble_wip(self, parent_wip_id: int, child_wip_id: int, wip_assemble_history_id: int = None, 
                        wip_process_step_history_id: int = None, auto_find_history: bool = True) -> Dict:
        """
        Odlinkowanie WIP (disassemble)
        Dwu-etapowy proces:
        1. Pierwsze wywołanie z WipProcessStepHistoryId aby uzyskać wipAssembleHistoryId
        2. Drugie wywołanie z pełnymi danymi aby faktycznie odlinkować
        
        Args:
            parent_wip_id: ID WIP rodzica (używane w URL)
            child_wip_id: ID WIP dziecka do odlinkowania (używane w body)
            wip_assemble_history_id: ID historii assembly (opcjonalne, zostanie automatycznie znalezione)
            wip_process_step_history_id: ID historii process step (opcjonalne, można podać dowolną wartość dla pierwszego wywołania)
            auto_find_history: Jeśli True i brak wipProcessStepHistoryId, szuka go w operation histories (może nie zadziałać)
            
        Returns:
            Dict z wynikiem operacji
        """
        # KROK 1: Znajdź WipProcessStepHistoryId jeśli nie podano i auto_find włączone
        if wip_process_step_history_id is None and auto_find_history:
            external_client = ExternalAPIClient(self.environment)
            if external_client.authenticate():
                wip_process_step_history_id = external_client.find_assembly_operation(parent_wip_id)
                if wip_process_step_history_id is None:
                    # Jeśli nie znaleziono, użyj dowolnej wartości - API zwróci prawdziwą w odpowiedzi
                    print(f"  ⚠ Nie znaleziono WipProcessStepHistoryId, użyję wartości 1 dla pierwszego wywołania")
                    wip_process_step_history_id = 1
            else:
                # Jeśli nie udało się zaautentykować, użyj wartości domyślnej
                print(f"  ⚠ Nie udało się zaautentykować, użyję wartości 1 dla pierwszego wywołania")
                wip_process_step_history_id = 1
        elif wip_process_step_history_id is None:
            # Jeśli auto_find wyłączone i nie podano, użyj 1
            wip_process_step_history_id = 1
        
        # KROK 2: Pierwsze wywołanie - pobierz wipAssembleHistoryId
        if wip_assemble_history_id is None:
            print(f"  Krok 1: Pobieranie wipAssembleHistoryId...")
            
            url = f"{self.base_url}/api/assembleall/{parent_wip_id}/disassemble"
            
            # Pierwsze wywołanie z wipAssembleHistoryId = 1 (żeby przeszło i dostać właściwe ID)
            payload_first = {
                "wipId": child_wip_id,
                "wipAssembleHistoryId": 1,
                "wipProcessStepHistoryId": wip_process_step_history_id
            }
            
            headers = {
                'Content-Type': 'application/json',
                'UserContext': json.dumps(self.user_context)
            }
            
            if self.mendix_token:
                headers['MendixToken'] = self.mendix_token
            
            try:
                response_first = self.session.post(url, json=payload_first, headers=headers)
                # Może zwrócić błąd, ale w odpowiedzi będzie wipAssembleHistoryId
                
                if response_first.status_code == 200 and response_first.text:
                    data = response_first.json()
                    
                    # Szukaj wipAssembleHistoryId w itemsAssembled dla konkretnego child_wip_id
                    items_assembled = data.get('itemsAssembled', [])
                    if items_assembled and len(items_assembled) > 0:
                        # Szukaj elementu z odpowiednim childWipId
                        found_item = None
                        for item in items_assembled:
                            if item.get('childWipId') == child_wip_id:
                                found_item = item
                                break
                        
                        if found_item:
                            wip_assemble_history_id = found_item.get('wipAssembleHistoryId')
                            if wip_assemble_history_id:
                                print(f"  ✓ Znaleziono wipAssembleHistoryId: {wip_assemble_history_id} dla child WIP {child_wip_id}")
                            else:
                                return {
                                    'success': False,
                                    'parent_wip_id': parent_wip_id,
                                    'child_wip_id': child_wip_id,
                                    'error': 'Nie znaleziono wipAssembleHistoryId w znalezionym elemencie',
                                    'status_code': response_first.status_code,
                                    'response': data
                                }
                        else:
                            return {
                                'success': False,
                                'parent_wip_id': parent_wip_id,
                                'child_wip_id': child_wip_id,
                                'error': f'Nie znaleziono child_wip_id {child_wip_id} w itemsAssembled',
                                'status_code': response_first.status_code,
                                'response': data
                            }
                    else:
                        return {
                            'success': False,
                            'parent_wip_id': parent_wip_id,
                            'child_wip_id': child_wip_id,
                            'error': 'Brak itemsAssembled w odpowiedzi',
                            'status_code': response_first.status_code,
                            'response': data
                        }
                else:
                    return {
                        'success': False,
                        'parent_wip_id': parent_wip_id,
                        'child_wip_id': child_wip_id,
                        'error': f'Błąd podczas pobierania wipAssembleHistoryId: {response_first.status_code}',
                        'status_code': response_first.status_code,
                        'response': response_first.text
                    }
                    
            except requests.exceptions.RequestException as e:
                return {
                    'success': False,
                    'parent_wip_id': parent_wip_id,
                    'child_wip_id': child_wip_id,
                    'error': f'Błąd podczas pierwszego wywołania: {str(e)}',
                    'status_code': None
                }
        
        # KROK 3: Drugie wywołanie - właściwe disassemble z pełnymi danymi
        print(f"  Krok 2: Disassemble z wipAssembleHistoryId={wip_assemble_history_id}, wipProcessStepHistoryId={wip_process_step_history_id}")
        
        url = f"{self.base_url}/api/assembleall/{parent_wip_id}/disassemble"
        
        payload = {
            "wipId": child_wip_id,
            "wipAssembleHistoryId": wip_assemble_history_id,
            "wipProcessStepHistoryId": wip_process_step_history_id
        }
        
        headers = {
            'Content-Type': 'application/json',
            'UserContext': json.dumps(self.user_context)
        }
        
        if self.mendix_token:
            headers['MendixToken'] = self.mendix_token
        
        # DEBUG: Wyświetl szczegóły requestu
        print(f"\n=== DEBUG REQUEST ===")
        print(f"URL: {url}")
        print(f"Method: POST")
        print(f"\nHeaders:")
        for key, value in headers.items():
            if key == 'UserContext':
                print(f"  {key}: {value[:100]}..." if len(value) > 100 else f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")
        print(f"\nPayload:")
        print(f"  {json.dumps(payload, indent=2)}")
        print(f"=====================\n")
        
        try:
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {
                'success': True,
                'parent_wip_id': parent_wip_id,
                'child_wip_id': child_wip_id,
                'status_code': response.status_code,
                'response': response.json() if response.text else None,
                'wip_assemble_history_id': wip_assemble_history_id,
                'wip_process_step_history_id': wip_process_step_history_id
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'parent_wip_id': parent_wip_id,
                'child_wip_id': child_wip_id,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                'response': getattr(e.response, 'text', None) if hasattr(e, 'response') else None
            }
    
    def disassemble_multiple_wips(self, parent_child_pairs: List[tuple]) -> List[Dict]:
        """
        Odlinkowanie wielu WIPów
        
        Args:
            parent_child_pairs: Lista tupli (parent_wip_id, child_wip_id) do odlinkowania
            
        Returns:
            Lista wyników dla każdego WIPa
        """
        results = []
        for parent_wip_id, child_wip_id in parent_child_pairs:
            print(f"Odlinkowywanie dziecka {child_wip_id} od rodzica {parent_wip_id}...")
            result = self.disassemble_wip(parent_wip_id, child_wip_id)
            results.append(result)
            if result['success']:
                print(f"  ✓ Sukces")
            else:
                print(f"  ✗ Błąd: {result.get('error', 'Unknown error')}")
        return results
