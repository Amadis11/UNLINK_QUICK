# Opis działania aplikacji WIP Unlink

## Proces odlinkowania WIP krok po kroku

### INPUT: Serial Number rodzica (np. "367499998250320140017728737910445")

---

## KROK 1: Autentykacja do External API

**Endpoint:** `GET /api/user/adsignin`

**Metoda:** Basic Authentication (username/password z .env)

**Proces:**
1. Aplikacja sprawdza cache w `.token_cache.json`
2. Jeśli token jest ważny (<8h) - używa go z cache
3. Jeśli nie ma lub wygasł - wykonuje request do `/api/user/adsignin`
4. Otrzymuje `UserToken=BQAAAA...` jako plain text
5. Wyciąga wartość po znaku `=` i ustawia jako ciastko `UserToken`
6. Zapisuje token do `.token_cache.json` z timestampem
7. Token ważny przez 8 godzin dla danego środowiska (STG/PRD osobno)

**Przykład odpowiedzi:**
```
UserToken=BQAAAAdDb29raWVzAQAAAAdDb29raWVzCXVzZXJs...
```

---

## KROK 2: Pobranie WIP ID po Serial Number

**Endpoint:** `GET /api/Wips/GetWipIdBySerialNumber`

**Parametry:**
- `SiteName` (obowiązkowy) - z .env, np. "Kwidzyn"
- `SerialNumber` (obowiązkowy) - podany przez użytkownika
- `CustomerName` (opcjonalny)
- `MaterialName` (opcjonalny)

**Headers:**
- Cookie: `UserToken` (z kroku 1)

**Przykład requestu:**
```
GET /api/Wips/GetWipIdBySerialNumber?SiteName=Kwidzyn&SerialNumber=367499998250320140017728737910445
Cookie: UserToken=BQAAAA...
```

**Przykład odpowiedzi:**
```json
[
  {
    "WipId": 4585908,
    "SerialNumber": "367499998250320140017728737910445",
    "Panel": null,
    "CustomerName": "BOSCH",
    "MaterialName": "8737910445",
    "IsAssembled": false
  }
]
```

**Output:** `WipId = 4585908`

---

## KROK 3: Pobranie genealogii WIP (opcjonalne - do weryfikacji)

**Endpoint:** `GET /api/Wips/{wipId}/genealogy`

**Parametry:**
- `wipId` - z kroku 2

**Headers:**
- Cookie: `UserToken`

**Przykład requestu:**
```
GET /api/Wips/4585908/genealogy
Cookie: UserToken=BQAAAA...
```

**Przykład odpowiedzi:**
```json
{
  "WipGenealogy": [
    {
      "Level": 0,
      "ItemId": 1,
      "ParentItemId": 0,
      "WipId": 4585908,
      "SerialNumber": "367499998250320140017728737910445",
      "MaterialName": "8737910445",
      "PhoenixMaterialType": "WIP"
    },
    {
      "Level": 1,
      "ItemId": 2,
      "ParentItemId": 1,
      "WipId": 4463218,
      "SerialNumber": "367499998250320140017728737910445PCB",
      "MaterialName": "8737910447",
      "PhoenixMaterialType": "WIP"
    }
  ]
}
```

**Output:** Lista zlinkowanych części w hierarchii (Level 0 = rodzic, Level 1+ = dzieci)

---

## KROK 4: Pobranie Operation Histories

**Endpoint:** `GET /api/Wips/{wipId}`

**Parametry:**
- `wipId` - z kroku 2

**Headers:**
- Cookie: `UserToken`

**Przykład requestu:**
```
GET /api/Wips/4585908
Cookie: UserToken=BQAAAA...
```

**Przykład odpowiedzi:**
```json
{
  "Wips": [
    {
      "WipId": 4585908,
      "SerialNumber": "367499998250320140017728737910445",
      "OperationHistories": [
        {
          "WipProcessStepHistoryId": 30138941,
          "RouteStepName": "LINK LOACAL",
          "StationType": "Assemble",
          "EndDateTime": "2025-06-17T11:13:27.6291197+00:00",
          "AssembledItems": [
            {
              "MaterialId": 299,
              "Material": "8737910447",
              "EntityId": 4463218,
              "Identifier": "367499998250320140017728737910445PCB",
              "EventType": "Assemble"
            }
          ]
        },
        {
          "WipProcessStepHistoryId": 30153562,
          "RouteStepName": "AOI_BB",
          "AssembledItems": []
        }
      ]
    }
  ]
}
```

**Proces wyszukiwania:**
1. Przeszukaj `OperationHistories` od najnowszej do najstarszej
2. Znajdź pierwszą operację gdzie `AssembledItems` nie jest puste
3. Wyciągnij `WipProcessStepHistoryId` z tej operacji

**Output:** `WipProcessStepHistoryId = 30138941` (z operacji Assembly)

---

## KROK 5: Pierwsze wywołanie Disassemble (GET wipAssembleHistoryId)

**Endpoint:** `POST /mendix-api/api/assembleall/{wipId}/disassemble`

**Parametry URL:**
- `wipId` - z kroku 2

**Headers:**
- `Content-Type: application/json`
- `UserContext: {"userId":3006,"userName":"Amadeusz Kusz",...}` (z .env)
- `StationContext: {"routeId":2257,"routeName":"GOLDEN TEST SAMPLE PCB",...}` (z config)

**Body:**
```json
{
  "wipId": 4585908,
  "wipAssembleHistoryId": 0,
  "wipProcessStepHistoryId": 30138941
}
```

**Przykład requestu:**
```
POST /mendix-api/api/assembleall/4585908/disassemble
Content-Type: application/json
UserContext: {"userId":3006,...}
StationContext: {"routeId":2257,...}

{
  "wipId": 4585908,
  "wipAssembleHistoryId": 0,
  "wipProcessStepHistoryId": 30138941
}
```

**Przykład odpowiedzi (200 OK):**
```json
{
  "wipId": 4585908,
  "serialNumber": "367499998250320140017728737910445",
  "material": "8737910445",
  "itemsAssembled": [
    {
      "wipAssembleHistoryId": 45643425,
      "materialID": 299,
      "material": "8737910447",
      "childWipId": 4463218,
      "serialNumberSubAssembly": "367499998250320140017728737910445PCB",
      "mustBeRemoved": true
    }
  ],
  "hasItemsThatMustBeRemoved": true
}
```

**Proces:**
1. API sprawdza co jest zlinkowane
2. Zwraca listę `itemsAssembled` z `wipAssembleHistoryId`
3. Wyciągamy `wipAssembleHistoryId` z pierwszego elementu

**Output:** `wipAssembleHistoryId = 45643425`

---

## KROK 6: Drugie wywołanie Disassemble (faktyczne odlinkowanie)

**Endpoint:** `POST /mendix-api/api/assembleall/{wipId}/disassemble`

**Parametry URL:**
- `wipId` - z kroku 2

**Headers:**
- `Content-Type: application/json`
- `UserContext: {...}` (j.w.)
- `StationContext: {...}` (j.w.)

**Body:**
```json
{
  "wipId": 4585908,
  "wipAssembleHistoryId": 45643425,
  "wipProcessStepHistoryId": 30138941
}
```

**Przykład requestu:**
```
POST /mendix-api/api/assembleall/4585908/disassemble
Content-Type: application/json
UserContext: {"userId":3006,...}
StationContext: {"routeId":2257,...}

{
  "wipId": 4585908,
  "wipAssembleHistoryId": 45643425,
  "wipProcessStepHistoryId": 30138941
}
```

**Przykład odpowiedzi (200 OK):**
```json
{
  "success": true,
  "message": "WIP successfully disassembled"
}
```

**To wywołanie faktycznie wykonuje odlinkowanie w bazie!**

---

## Podsumowanie danych przepływających przez system

### INPUT od użytkownika:
- Serial Number rodzica: `"367499998250320140017728737910445"`
- Środowisko: `STG` lub `PRD` (z .env)

### Dane pośrednie:
1. **UserToken** (8h cache): `"UserToken=BQAAAA..."`
2. **WipId** rodzica: `4585908`
3. **WipProcessStepHistoryId** (z Assembly operation): `30138941`
4. **wipAssembleHistoryId** (z pierwszego disassemble): `45643425`

### OUTPUT - REQUEST do faktycznego disassemble:
```json
{
  "wipId": 4585908,
  "wipAssembleHistoryId": 45643425,
  "wipProcessStepHistoryId": 30138941
}
```

### Rezultat:
Dziecko (WIP `4463218`, SN: `"367499998250320140017728737910445PCB"`) zostaje odlinkowane od rodzica.

---

## Środowiska i konfiguracja

### Z pliku .env:
- `ENVIRONMENT` - STG/PRD
- `SITE_NAME` - Kwidzyn
- `STG_EXTERNAL_API_URL` - https://kwi2-stg.jemsms.corp.jabil.org/api-external-api
- `STG_MENDIX_API_URL` - https://kwi2-stg.jemsms.corp.jabil.org/mendix
- `EXTERNAL_API_USERNAME` - JABIL\SVCKWI_JEMSMSAPISTG
- `EXTERNAL_API_PASSWORD` - (hasło)
- `USER_ID`, `USER_NAME`, `USER_LOGIN`, `USER_EMAIL`, `EMPLOYEE_NUMBER`

### Z pliku .token_cache.json (automatyczny):
```json
{
  "STG": {
    "token": "UserToken=BQAAAA...",
    "timestamp": "2026-01-22T09:00:00",
    "expires_at": "2026-01-22T17:00:00"
  },
  "PRD": {
    "token": "UserToken=...",
    "timestamp": "...",
    "expires_at": "..."
  }
}
```

---

## Bezpieczeństwo

### SSL Certificate Verification
- **Wyłączona** (`verify=False`) dla obu API
- Powód: Korporacyjne proxy/certyfikaty Jabil
- Ostrzeżenia SSL są wyciszone (`urllib3.disable_warnings`)

### Tokeny
- UserToken cache'owany lokalnie w `.token_cache.json` (gitignore'd)
- Ważność: 8 godzin
- Osobne tokeny dla STG i PRD
- Automatyczne odnowienie po wygaśnięciu

### Credentials
- Przechowywane tylko w `.env` (gitignore'd)
- Nie hardcoded w kodzie
- `.env.example` bez wrażliwych danych

---

## Error Handling

### Możliwe błędy:

1. **Autentykacja failed** → Sprawdź credentials w .env
2. **Serial Number nie znaleziony** → WIP nie istnieje w danym środowisku
3. **Brak operation histories z Assembly** → WIP nie był linkowany lub już odlinkowany
4. **Brak itemsAssembled w pierwszym disassemble** → Nic nie jest zlinkowane
5. **Drugi disassemble failed** → Błędne ID lub brak uprawnień

### Logi:
Aplikacja wyświetla szczegółowe logi na każdym etapie:
```
✓ Używam cache'owanego tokenu (ważny jeszcze 8h)
✓ WIP ID: 4585908
✓ Znaleziono operację Assembly: RouteStep='LINK LOACAL', WipProcessStepHistoryId=30138941
  Krok 1: Pobieranie wipAssembleHistoryId...
  ✓ Znaleziono wipAssembleHistoryId: 45643425
  Krok 2: Disassemble z wipAssembleHistoryId=45643425, wipProcessStepHistoryId=30138941
✓ Sukces
```
