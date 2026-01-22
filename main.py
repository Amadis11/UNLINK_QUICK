#!/usr/bin/env python3
"""
WIP Unlink Application
Aplikacja do odlinkowania WIP przez Mendix API
"""

import argparse
import json
import os
import logging
import threading
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from api_client import MendixAPIClient, ExternalAPIClient
from config import DEFAULT_ENVIRONMENT, get_current_environment, validate_config, get_site_name


def setup_logger(log_file: str = None) -> logging.Logger:
    """Konfiguruje logger dla aplikacji"""
    if log_file is None:
        # Utwórz folder logs jeśli nie istnieje
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f'logs/unlink_app_{timestamp}.log'
    
    # Konfiguracja loggera
    logger = logging.getLogger('WIPUnlink')
    logger.setLevel(logging.INFO)
    
    # Handler do pliku
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Handler do konsoli
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format - thread-safe
    formatter = logging.Formatter('%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s', 
                                 datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Dodaj handlery jeśli jeszcze nie ma
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


def process_single_serial_number(serial_number: str, environment: str, 
                                 ext_client: ExternalAPIClient,
                                 mendix_client: MendixAPIClient,
                                 logger: logging.Logger,
                                 counter: Dict) -> Dict:
    """
    Przetwarza pojedynczy numer seryjny
    Thread-safe funkcja do przetwarzania w wielowątkowości
    
    Args:
        serial_number: Numer seryjny do przetworzenia
        environment: Środowisko STG/PRD
        ext_client: Klient External API
        mendix_client: Klient Mendix API
        logger: Logger aplikacji
        counter: Słownik z licznikiem postępu (thread-safe z lockiem)
        
    Returns:
        Dict z wynikiem przetwarzania
    """
    # Usuń BOM i whitespace
    serial_number = serial_number.strip().lstrip('\ufeff')
    
    # Zwiększ licznik (thread-safe)
    with counter['lock']:
        counter['processed'] += 1
        current = counter['processed']
        total = counter['total']
    
    thread_name = threading.current_thread().name
    logger.info(f"[{current}/{total}] [{thread_name}] Rozpoczęcie przetwarzania SN: {serial_number}")
    print(f"[{current}/{total}] [{thread_name}] Przetwarzanie SN: {serial_number}")
    
    result = {
        'serial_number': serial_number,
        'timestamp': datetime.now().isoformat(),
        'environment': environment,
        'thread': thread_name,
        'success': False,
        'error': None,
        'details': {}
    }
    
    try:
        # 1. Pobierz WIP ID
        wip_data = ext_client.get_wip_id_by_serial_number(serial_number, get_site_name())
        if not wip_data or not isinstance(wip_data, list) or len(wip_data) == 0:
            result['error'] = 'WIP nie znaleziony dla podanego numeru seryjnego'
            logger.warning(f"[{thread_name}] SN {serial_number}: {result['error']}")
            print(f"  [{thread_name}] ⚠ {result['error']}")
            return result
        
        parent_wip_id = wip_data[0].get('WipId')
        if not parent_wip_id:
            result['error'] = 'Brak WipId w odpowiedzi'
            logger.warning(f"[{thread_name}] SN {serial_number}: {result['error']}")
            print(f"  [{thread_name}] ⚠ {result['error']}")
            return result
        
        result['details']['parent_wip_id'] = parent_wip_id
        logger.info(f"[{thread_name}] SN {serial_number}: Parent WIP ID: {parent_wip_id}")
        print(f"  [{thread_name}] ✓ Parent WIP ID: {parent_wip_id}")
        
        # 2. Pobierz genealogię
        genealogy = ext_client.get_genealogy(parent_wip_id)
        if not genealogy or 'WipGenealogy' not in genealogy:
            result['error'] = 'Nie znaleziono genealogii'
            logger.warning(f"[{thread_name}] SN {serial_number}: {result['error']}")
            print(f"  [{thread_name}] ⚠ {result['error']}")
            return result
        
        items = genealogy['WipGenealogy']
        children = [item for item in items if item.get('Level', 0) > 0]
        
        if not children:
            result['error'] = 'Brak dzieci do odlinkowania'
            logger.warning(f"[{thread_name}] SN {serial_number}: {result['error']}")
            print(f"  [{thread_name}] ⚠ {result['error']}")
            return result
        
        result['details']['children_count'] = len(children)
        result['details']['children'] = []
        logger.info(f"[{thread_name}] SN {serial_number}: Znaleziono {len(children)} dzieci")
        print(f"  [{thread_name}] ✓ Znaleziono {len(children)} dzieci")
        
        # 3. Odlinkuj każde dziecko
        all_children_success = True
        for child in children:
            child_wip_id = child.get('WipId')
            child_sn = child.get('SerialNumber', 'N/A')
            
            if not child_wip_id:
                continue
            
            logger.info(f"[{thread_name}] SN {serial_number}: Odlinkowywanie dziecka {child_wip_id} ({child_sn})")
            print(f"    [{thread_name}] Odlinkowywanie {child_wip_id} ({child_sn})...")
            
            disassemble_result = mendix_client.disassemble_wip(
                parent_wip_id=parent_wip_id,
                child_wip_id=child_wip_id,
                auto_find_history=True
            )
            
            child_result = {
                'child_wip_id': child_wip_id,
                'child_serial_number': child_sn,
                'success': disassemble_result.get('success', False),
                'error': disassemble_result.get('error')
            }
            
            result['details']['children'].append(child_result)
            
            if disassemble_result.get('success'):
                logger.info(f"[{thread_name}] SN {serial_number}: Dziecko {child_wip_id} odlinkowane pomyślnie")
                print(f"      [{thread_name}] ✓ Sukces")
            else:
                logger.error(f"[{thread_name}] SN {serial_number}: Błąd odlinkowania dziecka {child_wip_id}: {disassemble_result.get('error')}")
                print(f"      [{thread_name}] ✗ Błąd: {disassemble_result.get('error', 'Unknown')}")
                all_children_success = False
        
        result['success'] = all_children_success
        if result['success']:
            logger.info(f"[{thread_name}] SN {serial_number}: Przetworzono pomyślnie")
            print(f"  [{thread_name}] ✅ Przetworzono pomyślnie\n")
        else:
            result['error'] = 'Niektóre dzieci nie zostały odlinkowane'
            logger.warning(f"[{thread_name}] SN {serial_number}: {result['error']}")
            print(f"  [{thread_name}] ⚠ {result['error']}\n")
            
    except Exception as e:
        result['error'] = f'Nieoczekiwany błąd: {str(e)}'
        logger.error(f"[{thread_name}] SN {serial_number}: {result['error']}")
        print(f"  [{thread_name}] ❌ {result['error']}\n")
    
    return result


def read_wip_ids_from_file(file_path: str) -> List[int]:
    """
    Odczytuje listę WIP IDs z pliku
    Obsługuje formaty: CSV, TXT (jeden WIP na linię), JSON
    """
    wip_ids = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            
            # Spróbuj JSON
            if file_path.endswith('.json'):
                data = json.loads(content)
                if isinstance(data, list):
                    wip_ids = [int(x) for x in data]
                elif isinstance(data, dict) and 'wip_ids' in data:
                    wip_ids = [int(x) for x in data['wip_ids']]
            # CSV lub lista oddzielona przecinkami
            elif ',' in content:
                wip_ids = [int(x.strip()) for x in content.split(',') if x.strip()]
            # Jeden WIP na linię
            else:
                wip_ids = [int(line.strip()) for line in content.split('\n') if line.strip()]
    
    except Exception as e:
        print(f"Błąd podczas odczytu pliku: {e}")
        return []
    
    return wip_ids


def parse_wip_ids_from_string(wip_string: str) -> List[int]:
    """Parsuje WIP IDs z ciągu znaków (oddzielone przecinkami lub spacjami)"""
    # Usuń białe znaki i podziel po przecinkach lub spacjach
    wip_string = wip_string.replace(' ', ',')
    return [int(x.strip()) for x in wip_string.split(',') if x.strip()]


def check_genealogy(wip_ids: List[int], environment: str = 'STG'):
    """Sprawdza genealogię dla podanych WIPów"""
    client = ExternalAPIClient(environment)
    
    # Autentykuj się i pobierz UserToken
    if not client.authenticate():
        print("Nie udało się zaautentykować. Sprawdź credentials w .env")
        return
    
    print(f"\n=== Sprawdzanie genealogii dla {len(wip_ids)} WIPów ===\n")
    
    for wip_id in wip_ids:
        print(f"WIP ID: {wip_id}")
        genealogy = client.get_genealogy(wip_id)
        
        if genealogy:
            # Wyświetl podstawowe info
            if 'WipGenealogy' in genealogy:
                items = genealogy['WipGenealogy']
                print(f"  Liczba elementów w genealogii: {len(items)}")
                for item in items[:3]:  # Pokaż pierwsze 3
                    print(f"    - Level {item.get('Level')}: {item.get('SerialNumber')}")
                if len(items) > 3:
                    print(f"    ... i {len(items) - 3} więcej")
        else:
            print("  Nie znaleziono genealogii")
        print()


def process_serial_numbers(serial_numbers: List[str], environment: str = 'STG',
                          mendix_token: str = None, log_file: str = None, 
                          logger: logging.Logger = None, max_workers: int = 10) -> List[Dict]:
    """
    Przetwarza listę numerów seryjnych z wykorzystaniem wielowątkowości
    
    Args:
        serial_numbers: Lista numerów seryjnych
        environment: Środowisko STG/PRD
        mendix_token: Token Mendix (opcjonalny)
        log_file: Ścieżka do pliku logu JSON (opcjonalny)
        logger: Logger aplikacji
        max_workers: Liczba workerów (wątków) - domyślnie 10
        
    Returns:
        Lista wyników dla każdego numeru
    """
    if logger:
        logger.info(f"Rozpoczęcie przetwarzania {len(serial_numbers)} numerów seryjnych w środowisku {environment}")
        logger.info(f"Używam {max_workers} workerów")
    
    # Przygotuj klientów API dla każdego wątku
    ext_client = ExternalAPIClient(environment)
    
    # Autentykuj External API (wspólny token dla wszystkich wątków)
    if not ext_client.authenticate():
        error_msg = "Nie udało się zaautentykować do External API"
        print(f"❌ {error_msg}")
        if logger:
            logger.error(error_msg)
        return []
    
    if logger:
        logger.info("Autentykacja do External API zakończona sukcesem")
    
    # Mendix client (wspólny dla wszystkich wątków)
    mendix_client = MendixAPIClient(environment)
    if mendix_token:
        mendix_client.set_mendix_token(mendix_token)
        if logger:
            logger.info("Ustawiono MendixToken z parametru")
    
    total = len(serial_numbers)
    
    # Thread-safe counter
    counter = {
        'processed': 0,
        'total': total,
        'lock': threading.Lock()
    }
    
    results = []
    
    print(f"\n=== Przetwarzanie {total} numerów seryjnych w środowisku {environment} ===")
    print(f"🔧 Używam {min(max_workers, total)} workerów\n")
    
    # Przetwarzanie wielowątkowe
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Worker") as executor:
        # Utwórz zadania dla każdego numeru
        future_to_sn = {
            executor.submit(
                process_single_serial_number,
                sn,
                environment,
                ext_client,
                mendix_client,
                logger,
                counter
            ): sn for sn in serial_numbers
        }
        
        # Zbieraj wyniki w miarę ukończenia
        for future in as_completed(future_to_sn):
            sn = future_to_sn[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                error_result = {
                    'serial_number': sn,
                    'timestamp': datetime.now().isoformat(),
                    'environment': environment,
                    'thread': threading.current_thread().name,
                    'success': False,
                    'error': f'Wyjątek podczas przetwarzania: {str(e)}',
                    'details': {}
                }
                results.append(error_result)
                if logger:
                    logger.error(f"Wyjątek podczas przetwarzania SN {sn}: {e}")
    
    # Zapisz logi do pliku JSON
    if log_file:
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n📝 Logi JSON zapisane do: {log_file}")
            if logger:
                logger.info(f"Logi JSON zapisane do pliku: {log_file}")
        except Exception as e:
            print(f"\n⚠ Błąd podczas zapisu logów JSON: {e}")
            if logger:
                logger.error(f"Błąd podczas zapisu logów JSON: {e}")
    
    # Podsumowanie
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    
    print(f"\n=== Podsumowanie ===")
    print(f"Przetworzono: {len(results)}")
    print(f"Sukces: {success_count}")
    print(f"Błędy: {fail_count}")
    
    if logger:
        logger.info(f"Podsumowanie: Przetworzono={len(results)}, Sukces={success_count}, Błędy={fail_count}")
    
    return results


def disassemble_wips(parent_child_pairs: List[tuple], environment: str = 'STG', 
                     mendix_token: str = None):
    """
    Odlinkowanie WIPów
    
    Args:
        parent_child_pairs: Lista tupli (parent_wip_id, child_wip_id)
        environment: Środowisko STG/PRD
        mendix_token: Token Mendix (opcjonalny)
    """
    client = MendixAPIClient(environment)
    
    if mendix_token:
        client.set_mendix_token(mendix_token)
    
    print(f"\n=== Odlinkowanie {len(parent_child_pairs)} WIPów w środowisku {environment} ===\n")
    
    results = client.disassemble_multiple_wips(parent_child_pairs)
    
    # Podsumowanie
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    
    print(f"\n=== Podsumowanie ===")
    print(f"Sukces: {success_count}")
    print(f"Błędy: {fail_count}")
    
    if fail_count > 0:
        print("\nWIPy z błędami:")
        for r in results:
            if not r['success']:
                print(f"  Parent {r.get('parent_wip_id')} -> Child {r.get('child_wip_id')}: {r.get('error', 'Unknown error')}")
    
    return results


def main():
    """Główna funkcja aplikacji"""
    # Sprawdź konfigurację
    if not validate_config():
        return
    
    # Pobierz środowisko z .env
    current_env = get_current_environment()
    
    # Setup logger
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    app_log_file = f'unlink_app_{timestamp}.log'
    logger = setup_logger(app_log_file)
    
    logger.info("=" * 60)
    logger.info("Uruchomienie WIP Unlink Application")
    logger.info(f"Środowisko: {current_env}")
    logger.info(f"Plik logu aplikacji: {app_log_file}")
    logger.info("=" * 60)
    
    parser = argparse.ArgumentParser(
        description='WIP Unlink Tool - Odlinkowanie WIPów przez Mendix API',
        epilog=f'Aktualne środowisko z .env: {current_env}'
    )
    
    parser.add_argument(
        '-w', '--wips',
        help='Para parent_wip_id:child_wip_id (np. "4585913:4463232")'
    )
    parser.add_argument(
        '-s', '--serial',
        help='Serial Number - automatycznie znajdzie parent WIP i dzieci do odlinkowania'
    )
    parser.add_argument(
        '-sf', '--serial-file',
        help='Plik z listą numerów seryjnych (jeden na linię)'
    )
    parser.add_argument(
        '-f', '--file',
        help='Plik z parami parent:child WIP IDs (jeden na linię lub JSON)'
    )
    parser.add_argument(
        '-lf', '--log-file',
        help='Plik do zapisu logów w formacie JSON (domyślnie: unlink_log_TIMESTAMP.json)'
    )
    parser.add_argument(
        '-e', '--environment',
        choices=['STG', 'PRD'],
        default=None,
        help=f'Środowisko (domyślnie z .env: {current_env})'
    )
    parser.add_argument(
        '-c', '--check',
        action='store_true',
        help='Tylko sprawdź genealogię bez odlinkowania'
    )
    parser.add_argument(
        '-t', '--token',
        help='MendixToken do autoryzacji'
    )
    
    args = parser.parse_args()
    
    # Użyj środowiska z argumentu lub z .env
    environment = args.environment if args.environment else current_env
    
    logger.info(f"Wybrane środowisko: {environment}")
    logger.info(f"Źródło środowiska: {'argument CLI' if args.environment else '.env'}")
    
    print(f"🌍 Środowisko: {environment}")
    print(f"📁 Źródło: {'.env' if not args.environment else 'argument CLI'}")
    print(f"📋 Log aplikacji: {app_log_file}\n")
    
    # Obsługa pliku z numerami seryjnymi
    if args.serial_file:
        logger.info(f"Tryb: przetwarzanie pliku z numerami seryjnymi: {args.serial_file}")
        print(f"=== Wczytywanie numerów seryjnych z pliku: {args.serial_file} ===\n")
        
        try:
            with open(args.serial_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig usuwa BOM
                serial_numbers = []
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:  # Pomiń puste linie
                        serial_numbers.append(line)
                    else:
                        logger.debug(f"Pominięto pustą linię: {line_num}")
                        print(f"  Pominięto pustą linię: {line_num}")
            
            logger.info(f"Wczytano {len(serial_numbers)} numerów seryjnych z pliku")
            print(f"✓ Wczytano {len(serial_numbers)} numerów seryjnych\n")
            
            # Przygotuj nazwę pliku logu
            if args.log_file:
                log_file = args.log_file
            else:
                os.makedirs('logs', exist_ok=True)
                log_file = f'logs/unlink_results_{timestamp}.json'
            
            logger.info(f"Wyniki JSON zostaną zapisane do: {log_file}")
            
            # Przetwórz wszystkie numery
            if environment == 'PRD':
                logger.info("Środowisko PRD - wykonanie automatyczne bez potwierdzenia")
                print(f"🚀 Środowisko PRD - wykonuję automatycznie bez potwierdzenia\n")
                process_serial_numbers(serial_numbers, environment, args.token, log_file, logger)
            else:
                response = input(f"Czy na pewno chcesz przetworzyć {len(serial_numbers)} numerów w środowisku {environment}? (tak/nie): ")
                logger.info(f"Użytkownik odpowiedział: '{response}'")
                if response.lower() in ['tak', 'yes', 'y', 't']:
                    logger.info("Potwierdzono - rozpoczęcie przetwarzania")
                    process_serial_numbers(serial_numbers, environment, args.token, log_file, logger)
                else:
                    logger.warning("Operacja anulowana przez użytkownika")
                    print("Operacja anulowana")
            logger.info("Zakończenie programu")
            return
            
        except FileNotFoundError:
            error_msg = f"Nie znaleziono pliku {args.serial_file}"
            logger.error(error_msg)
            print(f"❌ Błąd: {error_msg}")
            return
        except Exception as e:
            error_msg = f"Błąd podczas wczytywania pliku: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            return
    
    # Pobierz listę par parent:child WIP IDs
    parent_child_pairs = []
    
    if args.serial:
        # Flow z Serial Number
        print(f"=== Wyszukiwanie WIP po Serial Number: {args.serial} ===\n")
        
        ext_client = ExternalAPIClient(environment)
        if not ext_client.authenticate():
            print("Nie udało się zaautentykować do External API")
            return
        
        # 1. Pobierz WIP ID po serial number
        print("Krok 1: Pobieranie WIP ID...")
        from config import get_site_name
        wip_data = ext_client.get_wip_id_by_serial_number(args.serial, get_site_name())
        if not wip_data or not isinstance(wip_data, list) or len(wip_data) == 0:
            print(f"Nie znaleziono WIP dla serial number: {args.serial}")
            return
        
        parent_wip_id = wip_data[0].get('WipId')
        if not parent_wip_id:
            print(f"Nie znaleziono WipId w odpowiedzi")
            return
        print(f"  ✓ Parent WIP ID: {parent_wip_id}\n")
        
        # 2. Pobierz genealogię
        print("Krok 2: Pobieranie genealogii...")
        genealogy = ext_client.get_genealogy(parent_wip_id)
        if not genealogy or 'WipGenealogy' not in genealogy:
            print("Nie znaleziono genealogii")
            return
        
        items = genealogy['WipGenealogy']
        print(f"  ✓ Znaleziono {len(items)} elementów w genealogii")
        
        # Znajdź dzieci (Level > 0)
        children = [item for item in items if item.get('Level', 0) > 0]
        if not children:
            print("Nie znaleziono dzieci do odlinkowania")
            return
        
        print(f"  ✓ Znaleziono {len(children)} dzieci do odlinkowania:")
        for child in children:
            child_sn = child.get('SerialNumber', 'N/A')
            child_wip_id = child.get('WipId')
            print(f"    - WIP ID: {child_wip_id}, SN: {child_sn}")
            if child_wip_id:
                parent_child_pairs.append((parent_wip_id, child_wip_id))
        print()
        
        # 3. Pobierz operation histories dla parent
        print("Krok 3: Pobieranie operation histories dla parent WIP...")
        histories = ext_client.get_operation_histories(parent_wip_id)
        if histories:
            print(f"  ✓ Pobrano operation histories")
        else:
            print("  ⚠ Brak operation histories (będzie użyty WipProcessStepHistoryId z pierwszego wywołania)")
        print()
        
    elif args.wips:
        # Format: parent:child
        parts = args.wips.split(':')
        if len(parts) == 2:
            parent_child_pairs = [(int(parts[0]), int(parts[1]))]
        else:
            print("Błąd: Format musi być parent_wip_id:child_wip_id (np. '4585913:4463232')")
            return
    elif args.file:
        # Przeczytaj pary z pliku
        try:
            with open(args.file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        parts = line.split(':')
                        if len(parts) == 2:
                            parent_child_pairs.append((int(parts[0]), int(parts[1])))
        except Exception as e:
            print(f"Błąd podczas odczytu pliku: {e}")
            return
    else:
        print("Błąd: Musisz podać Serial Number (-s), plik z SN (-sf), parę WIPów (-w parent:child) lub plik (-f)")
        parser.print_help()
        return
    
    if not parent_child_pairs:
        print("Błąd: Nie znaleziono żadnych par WIP IDs")
        return
    
    print(f"Znaleziono {len(parent_child_pairs)} par WIP IDs:")
    for parent, child in parent_child_pairs:
        print(f"  Parent: {parent} -> Child: {child}")
    
    # Wykonaj akcję
    if args.check:
        # Sprawdź genealogię dla rodziców
        parent_ids = [p for p, c in parent_child_pairs]
        check_genealogy(parent_ids, environment)
    else:
        # Potwierdź przed odlinkowaniem (tylko dla STG)
        if environment == 'PRD':
            print(f"\n🚀 Środowisko PRD - wykonuję automatycznie bez potwierdzenia\n")
            disassemble_wips(parent_child_pairs, environment, args.token)
        else:
            response = input(f"\nCzy na pewno chcesz odlinkować {len(parent_child_pairs)} par WIPów w środowisku {environment}? (tak/nie): ")
            if response.lower() in ['tak', 'yes', 'y', 't']:
                disassemble_wips(parent_child_pairs, environment, args.token)
            else:
                print("Operacja anulowana")


if __name__ == "__main__":
    main()
