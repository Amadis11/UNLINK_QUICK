# 📘 Instrukcja - WIP Unlink Application

## 📋 Spis treści
- [Opis aplikacji](#opis-aplikacji)
- [Możliwości i funkcjonalności](#możliwości-i-funkcjonalności)
- [Wymagania i instalacja](#wymagania-i-instalacja)
- [Konfiguracja](#konfiguracja)
- [Użycie](#użycie)
- [Przykłady wywołań](#przykłady-wywołań)
- [Struktura projektu](#struktura-projektu)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## 🎯 Opis aplikacji

**WIP Unlink Application** to narzędzie do automatycznego odlinkowania (disassemble) komponentów WIP (Work In Progress) w systemie JEMS przez Mendix API. Aplikacja umożliwia masowe przetwarzanie numerów seryjnych i automatyczne wykonywanie operacji odlinkowania ze wsparciem dla środowisk STG i PRD.

### Główne funkcje:
- ✅ Automatyczne odlinkowanie WIPów przez Mendix API
- 🔍 Sprawdzanie genealogii WIP przed operacją
- 🔄 Wsparcie wielowątkowe - przetwarzanie wielu SN jednocześnie
- 📊 Szczegółowe logowanie i raportowanie wyników
- 🌍 Obsługa środowisk STG i PRD
- 📁 Przetwarzanie z plików (TXT, CSV, JSON) lub z linii poleceń

---

## 🚀 Możliwości i funkcjonalności

### 1. **Tryby pracy**

#### A. Przetwarzanie po numerze seryjnym (`-s` / `--serial`)
Automatyczne pobieranie WIP ID, genealogii i odlinkowanie dzieci dla pojedynczego numeru seryjnego.

#### B. Przetwarzanie z pliku numerów seryjnych (`-sf` / `--serial-file`)
Masowe przetwarzanie wielu numerów seryjnych z pliku TXT. Obsługuje:
- Format: jeden numer seryjny na linię
- Automatyczne usuwanie BOM i whitespace
- Wielowątkowe przetwarzanie (domyślnie 5 wątków)

#### C. Tryb sprawdzania genealogii (`-c` / `--check`)
Sprawdza genealogię WIP bez wykonywania operacji odlinkowania.

#### D. Ręczne podanie par WIP (`-w` / `--wips`)
Bezpośrednie podanie pary parent:child WIP IDs (format: `parent_id:child_id`).

### 2. **Środowiska**

- **STG** (Staging) - środowisko testowe
  - Wymaga potwierdzenia przed wykonaniem operacji
  - Zalecane do testowania przed wdrożeniem na PRD
  
- **PRD** (Production) - środowisko produkcyjne
  - Wykonuje operacje automatycznie bez potwierdzenia
  - Wymaga szczególnej ostrożności

### 3. **Wielowątkowość**

Aplikacja wykorzystuje `ThreadPoolExecutor` do równoległego przetwarzania wielu numerów seryjnych:
- Domyślnie: 5 wątków (`--threads 5`)
- Można dostosować liczbę wątków do potrzeb
- Thread-safe logowanie i liczniki

### 4. **Logowanie**

Wszystkie operacje są logowane w dwóch miejscach:
- **Plik logu**: `logs/unlink_app_YYYYMMDD_HHMMSS.log`
- **Konsola**: wyświetlanie postępu w czasie rzeczywistym
- **Plik wyników JSON**: `logs/unlink_results_YYYYMMDD_HHMMSS.json`

Format logów zawiera:
- Timestamp
- Numer wątku
- Poziom logowania
- Szczegóły operacji

### 5. **Cache tokenów**

Aplikacja cachuje token External API w pliku `.token_cache.json`:
- Token jest ważny przez 8 godzin
- Automatyczne odświeżanie po wygaśnięciu
- Osobny cache dla każdego środowiska (STG/PRD)

---

## 📦 Wymagania i instalacja

### Wymagania systemowe:
- Python 3.7 lub nowszy
- Dostęp do sieci Jabil (VPN jeśli zdalne)
- Tokeny dostępowe: UserToken i MendixToken

### Instalacja:

1. **Sklonuj lub pobierz projekt**
   ```bash
   git clone <repository-url>
   cd UNLINK_QUICK
   ```

2. **Zainstaluj zależności**
   ```bash
   pip install -r requirements.txt
   ```

3. **Utwórz plik `.env`**
   ```bash
   copy .env.example .env  # Windows
   # lub
   cp .env.example .env    # Linux/Mac
   ```

4. **Skonfiguruj plik `.env`** (patrz sekcja Konfiguracja)

---

## ⚙️ Konfiguracja

### Plik `.env`

Utwórz plik `.env` w głównym katalogu projektu z następującymi parametrami:

```env
# Środowisko (STG lub PRD)
ENVIRONMENT=STG

# Site Name
SITE_NAME=Kwidzyn

# External API - Credentials (wspólne dla STG i PRD)
EXTERNAL_API_USERNAME=your_username
EXTERNAL_API_PASSWORD=your_password

# STG Environment URLs
STG_EXTERNAL_API_URL=https://stg-external-api-url.com
STG_MENDIX_API_URL=https://stg-mendix-api-url.com

# PRD Environment URLs
PRD_EXTERNAL_API_URL=https://prd-external-api-url.com
PRD_MENDIX_API_URL=https://prd-mendix-api-url.com

# Mendix Token (opcjonalnie, można podać z linii poleceń)
MENDIX_TOKEN=your_mendix_token_here
```

### Plik `config.py`

Plik `config.py` zawiera dodatkowe konfiguracje:
- **USER_CONTEXT**: dane użytkownika (userId, userName, email, employeeNumber)
- **STATION_CONTEXT**: dane stacji roboczej (routeId, factoryId, stationType)

**Uwaga**: Edytuj te wartości zgodnie z Twoimi danymi przed użyciem aplikacji.

---

## 💻 Użycie

### Podstawowa składnia:

```bash
python main.py [OPTIONS]
```

### Dostępne parametry:

| Parametr | Skrót | Opis | Wymagany |
|----------|-------|------|----------|
| `--serial` | `-s` | Numer seryjny do przetworzenia | Nie* |
| `--serial-file` | `-sf` | Plik z numerami seryjnymi (jeden na linię) | Nie* |
| `--wips` | `-w` | Para WIP IDs (format: parent:child) | Nie* |
| `--file` | `-f` | Plik z parami WIP IDs | Nie* |
| `--environment` | `-e` | Środowisko: STG lub PRD (domyślnie z .env) | Nie |
| `--token` | `-t` | Mendix Token (opcjonalnie, domyślnie z .env) | Nie |
| `--check` | `-c` | Tylko sprawdź genealogię (bez odlinkowania) | Nie |
| `--threads` | - | Liczba wątków do przetwarzania (domyślnie 5) | Nie |
| `--log-file` | - | Nazwa pliku logu (domyślnie auto-generowana) | Nie |

\* *Wymagany jeden z: `-s`, `-sf`, `-w`, `-f`*

---

## 📚 Przykłady wywołań

### 1. Sprawdzenie genealogii (bez odlinkowania)

Sprawdź genealogię dla jednego numeru seryjnego:
```bash
python main.py -s "SN123456789" -c
```

### 2. Odlinkowanie pojedynczego SN

Odlinkuj dzieci dla jednego numeru seryjnego w środowisku STG:
```bash
python main.py -s "SN123456789" -e STG
```

### 3. Odlinkowanie z pliku numerów seryjnych

Odlinkuj wszystkie numery z pliku (wielowątkowo):
```bash
python main.py -sf resources/hmi800.txt -e STG
```

Możesz dostosować liczbę wątków:
```bash
python main.py -sf resources/hmi800.txt -e STG --threads 10
```

### 4. Odlinkowanie konkretnej pary WIP

Odlinkuj konkretną parę parent:child:
```bash
python main.py -w "4585913:4463232" -e STG
```

### 5. Odlinkowanie na środowisku PRD

**UWAGA**: Operacje na PRD są wykonywane automatycznie bez potwierdzenia!
```bash
python main.py -sf resources/production_sns.txt -e PRD
```

### 6. Użycie własnego Mendix Token

Jeśli nie chcesz przechowywać tokenu w `.env`:
```bash
python main.py -s "SN123456789" -e STG -t "YOUR_MENDIX_TOKEN_HERE"
```

### 7. Własna nazwa pliku logu

```bash
python main.py -sf resources/my_list.txt -e STG --log-file logs/custom_log.json
```

---

## 📁 Struktura projektu

```
UNLINK_QUICK/
│
├── main.py                 # Główny plik aplikacji
├── api_client.py           # Klienty API (External i Mendix)
├── config.py               # Konfiguracja aplikacji
├── requirements.txt        # Zależności Python
├── README.md              # README (ang)
├── INSTRUKCJA.md          # Ta instrukcja (pol)
├── DESCRIPTION.md         # Szczegółowy opis technicny
│
├── .env                   # Konfiguracja środowiska (nie w repo)
├── .env.example           # Przykładowa konfiguracja
├── .token_cache.json      # Cache tokenów (nie w repo)
│
├── logs/                  # Folder na logi aplikacji
│   ├── unlink_app_*.log           # Logi aplikacji
│   └── unlink_results_*.json      # Wyniki operacji
│
├── tests/                 # Testy jednostkowe i integracyjne
│   ├── test_auth.py
│   ├── test_disassemble.py
│   ├── test_genealogy.py
│   └── ...
│
└── resources/             # Przykładowe pliki i dane testowe
    ├── hmi800.txt                  # Przykładowa lista SN
    ├── disassemble_request.json    # Przykładowy request
    ├── disassemble_response.json   # Przykładowa odpowiedź
    └── ...
```

---

## 🔧 Rozwiązywanie problemów

### Problem: "Nie udało się zaautentykować do External API"

**Rozwiązanie:**
1. Sprawdź dane logowania w pliku `.env`
2. Upewnij się, że masz dostęp do sieci Jabil (VPN)
3. Sprawdź, czy URL External API jest poprawny
4. Usuń plik `.token_cache.json` i spróbuj ponownie

### Problem: "MendixToken nie został skonfigurowany"

**Rozwiązanie:**
1. Dodaj `MENDIX_TOKEN` w pliku `.env`
2. Lub podaj token z linii poleceń używając parametru `-t`

### Problem: "WIP nie znaleziony dla podanego numeru seryjnego"

**Rozwiązanie:**
1. Sprawdź, czy numer seryjny jest poprawny
2. Sprawdź, czy `SITE_NAME` w `.env` jest poprawny
3. Upewnij się, że WIP istnieje w wybranym środowisku (STG/PRD)

### Problem: Błąd SSL/Certificate

**Rozwiązanie:**
- Aplikacja automatycznie wyłącza weryfikację SSL dla korporacyjnych proxy
- Jeśli problem nadal występuje, sprawdź ustawienia proxy w systemie

### Problem: Zbyt wolne przetwarzanie

**Rozwiązanie:**
- Zwiększ liczbę wątków: `--threads 10`
- Sprawdź połączenie sieciowe
- Może być ograniczenie po stronie API

---

## 📊 Interpretacja wyników

### Plik wyników JSON

Po zakończeniu operacji aplikacja tworzy plik JSON z szczegółowymi wynikami:

```json
{
  "serial_number": "SN123456789",
  "timestamp": "2026-01-22T14:30:00",
  "environment": "STG",
  "thread": "ThreadPoolExecutor-0_0",
  "success": true,
  "error": null,
  "details": {
    "parent_wip_id": 4585913,
    "children_unlinked": [
      {
        "child_wip_id": 4463232,
        "child_serial": "CHILD_SN_001",
        "success": true
      }
    ],
    "total_children": 1,
    "successful_unlinks": 1
  }
}
```

### Kody sukcesu:
- ✅ `"success": true` - Operacja zakończona sukcesem
- ❌ `"success": false` - Operacja zakończona błędem (sprawdź pole `error`)

---

## 🛡️ Bezpieczeństwo

### Ważne zasady:

1. **Nigdy nie commituj pliku `.env` do repozytorium!**
   - Zawiera wrażliwe dane (hasła, tokeny)
   - Dodany do `.gitignore`

2. **Zawsze testuj na STG przed PRD**
   - STG wymaga potwierdzenia
   - PRD wykonuje operacje automatycznie

3. **Przechowuj backupy danych przed operacjami na PRD**

4. **Regularnie rotuj tokeny i hasła**

---

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi w folderze `logs/`
2. Uruchom testy w folderze `tests/`
3. Skontaktuj się z zespołem IT/DevOps

---

## 📝 Changelog

### v2.0 (2026-01-22)
- Dodano tryb przetwarzania z pliku numerów seryjnych
- Implementacja wielowątkowości
- Reorganizacja struktury projektu (logs/, tests/, resources/)
- Dodano cache tokenów
- Ulepszone logowanie

### v1.0 (2026-01-20)
- Pierwsza wersja aplikacji
- Podstawowe funkcje odlinkowania

---

## 📄 Licencja

© 2026 Jabil. Wszystkie prawa zastrzeżone.

Aplikacja do użytku wewnętrznego Jabil.
