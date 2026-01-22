# WIP Unlink Application

Aplikacja do odlinkowania WIP (Work In Progress) przez Mendix API w systemie JEMS.

## Funkcjonalności

- 🔗 Odlinkowanie WIPów przez Mendix API endpoint `/api/assembleall/{wipId}/disassemble`
- 📊 Sprawdzanie genealogii WIP przed odlinkowaniem
- 🔄 Wsparcie dla środowisk STG i PRD
- 📝 Odczyt listy WIPów z pliku (TXT, CSV, JSON) lub z linii poleceń
- ✅ Potwierdzenie przed wykonaniem operacji

## Wymagania

- Python 3.7+
- Dostęp do Jabil JEMS API (STG lub PRD)
- Wymagane tokeny: UserToken i MendixToken

## Instalacja

1. Sklonuj lub pobierz projekt
2. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```

## Konfiguracja

Edytuj [config.py](config.py) aby ustawić:
- Dane logowania do API
- User Context (userId, userName, userLogin, email, employeeNumber)
- Station Context (routeId, factoryId, stationType, etc.)

## Użycie

### Podstawowe komendy

**Sprawdzenie genealogii (bez odlinkowania):**
```bash
python main.py -w "2521879,2521880,2521881" -c
```

**Odlinkowanie WIPów z listy:**
```bash
python main.py -w "2521879,2521880,2521881" -e STG
```

**Odlinkowanie WIPów z pliku:**
```bash
python main.py -f wip_list.txt -e STG
```

**Z tokenem Mendix:**
```bash
python main.py -w "2521879" -e PRD -t "YOUR_MENDIX_TOKEN"
```

### Parametry

- `-w, --wips` - Lista WIP IDs oddzielona przecinkami
- `-f, --file` - Plik z listą WIP IDs (txt, csv, json)
- `-e, --environment` - Środowisko: STG lub PRD (domyślnie: STG)
- `-c, --check` - Tylko sprawdź genealogię bez odlinkowania
- `-t, --token` - MendixToken do autoryzacji

### Formaty plików wejściowych

**TXT (jeden WIP na linię):**
```
2521879
2521880
2521881
```

**CSV (oddzielone przecinkami):**
```
2521879,2521880,2521881
```

**JSON:**
```json
{
  "wip_ids": [2521879, 2521880, 2521881]
}
```
lub
```json
[2521879, 2521880, 2521881]
```

## Struktura projektu

```
.
├── main.py              # Główna aplikacja CLI
├── api_client.py        # Klienty API (Mendix i External)
├── config.py            # Konfiguracja środowisk i kontekstów
├── requirements.txt     # Zależności Python
├── genealogy.json       # Przykładowa odpowiedź API genealogii
└── README.md           # Ten plik
```

## API Endpoints

### Mendix API
- **Base URL (STG):** https://kwi2-stg.jemsms.corp.jabil.org/mendix
- **Base URL (PRD):** https://kwi-prd.jemsms.corp.jabil.org/mendix
- **Disassemble:** `POST /mendix-api/api/assembleall/{wipId}/disassemble`

### External API
- **Base URL (STG):** https://kwi2-stg.jemsms.corp.jabil.org/api-external-api
- **Base URL (PRD):** https://kwi-prd.jemsms.corp.jabil.org/api-external-api
- **Genealogy:** `GET /genealogy/{wipId}`

## Bezpieczeństwo

⚠️ **UWAGA:** Plik [config.py](config.py) zawiera dane logowania. Nie commituj tego pliku do repozytorium publicznego!

Zalecane:
- Dodaj `config.py` do `.gitignore`
- Użyj zmiennych środowiskowych dla wrażliwych danych
- Przechowuj credentials w bezpiecznym miejscu

## Przykład użycia

```bash
# 1. Sprawdź genealogię przed odlinkowaniem
python main.py -w "2521879" -c -e STG

# 2. Jeśli wszystko OK, odlinkuj
python main.py -w "2521879" -e STG

# 3. Potwierdź operację
Czy na pewno chcesz odlinkować 1 WIPów w środowisku STG? (tak/nie): tak

=== Odlinkowanie 1 WIPów w środowisku STG ===

Odlinkowywanie WIP 2521879...
  ✓ Sukces

=== Podsumowanie ===
Sukces: 1
Błędy: 0
```

## Development

Dodatkowe narzędzia pomocnicze:
- `ExternalAPIClient` - do pobierania danych z External API
- `MendixAPIClient` - do wykonywania operacji przez Mendix API

## Troubleshooting

**Problem:** `Python was not found`
- **Rozwiązanie:** Zainstaluj Python 3.7+ z [python.org](https://python.org)

**Problem:** Błąd autoryzacji
- **Rozwiązanie:** Sprawdź credentials w [config.py](config.py) i upewnij się, że tokeny są aktualne

**Problem:** Nie można znaleźć genealogii
- **Rozwiązanie:** Sprawdź czy WIP ID jest poprawny i czy endpoint API jest dostępny

## Autor

Amadeusz Kusz (2969118)
