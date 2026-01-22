#!/usr/bin/env python3
"""
WIP Unlink Application
Aplikacja do odlinkowania WIP przez Mendix API
"""

import argparse
import json
import os
from typing import List
from api_client import MendixAPIClient, ExternalAPIClient
from config import DEFAULT_ENVIRONMENT, get_current_environment, validate_config


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
        '-f', '--file',
        help='Plik z parami parent:child WIP IDs (jeden na linię lub JSON)'
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
    
    print(f"🌍 Środowisko: {environment}")
    print(f"📁 Źródło: {'.env' if not args.environment else 'argument CLI'}\n")
    
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
        print("Błąd: Musisz podać Serial Number (-s), parę WIPów (-w parent:child) lub plik (-f)")
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
