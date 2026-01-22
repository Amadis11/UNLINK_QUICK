# WIP Unlink Application

Aplikacja do automatycznego odlinkowania WIP (Work In Progress) przez Mendix API w systemie JEMS.

> 📖 **[Polski opis i instrukcja - INSTRUKCJA.md](INSTRUKCJA.md)**

## ✨ Features

- 🔗 Unlink WIPs via Mendix API endpoint `/api/assembleall/{wipId}/disassemble`
- 📊 Check WIP genealogy before unlinking
- 🔄 Support for STG and PRD environments
- 🧵 Multi-threaded processing for batch operations
- 📝 Process serial numbers from files (TXT, CSV, JSON) or command line
- 📁 Organized structure with logs, tests, and resources
- ✅ Confirmation before executing operations
- 💾 Token caching for External API (8-hour validity)

## 📦 Requirements

- Python 3.7+
- Access to Jabil JEMS API (STG or PRD)
- Required tokens: UserToken and MendixToken
- Network access (VPN if remote)

## 🚀 Quick Start

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd UNLINK_QUICK
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file**
   ```bash
   copy .env.example .env  # Windows
   # or
   cp .env.example .env    # Linux/Mac
   ```

4. **Configure `.env` with your credentials**
   ```env
   ENVIRONMENT=STG
   SITE_NAME=Kwidzyn
   EXTERNAL_API_USERNAME=your_username
   EXTERNAL_API_PASSWORD=your_password
   MENDIX_TOKEN=your_mendix_token
   # ... see .env.example for full configuration
   ```

## 💻 Usage

### Basic Commands

**Check genealogy (without unlinking):**
```bash
python main.py -s "SN123456789" -c
```

**Unlink single serial number:**
```bash
python main.py -s "SN123456789" -e STG
```

**Unlink from file (multi-threaded):**
```bash
python main.py -sf resources/hmi800.txt -e STG
```

**Specify number of threads:**
```bash
python main.py -sf resources/hmi800.txt -e STG --threads 10
```

**Production environment (auto-execution):**
```bash
python main.py -sf resources/production.txt -e PRD
```

### Command-Line Parameters

| Parameter | Short | Description | Required |
|-----------|-------|-------------|----------|
| `--serial` | `-s` | Single serial number to process | No* |
| `--serial-file` | `-sf` | File with serial numbers (one per line) | No* |
| `--wips` | `-w` | WIP pair (format: parent:child) | No* |
| `--file` | `-f` | File with WIP pairs | No* |
| `--environment` | `-e` | Environment: STG or PRD (default from .env) | No |
| `--token` | `-t` | Mendix Token (optional, default from .env) | No |
| `--check` | `-c` | Check genealogy only (no unlinking) | No |
| `--threads` | - | Number of threads (default: 5) | No |
| `--log-file` | - | Log file name (default: auto-generated) | No |

\* *One of: `-s`, `-sf`, `-w`, `-f` is required*

## 📁 Project Structure

```
UNLINK_QUICK/
│
├── main.py                 # Main CLI application
├── api_client.py           # API clients (External & Mendix)
├── config.py               # Environment and context configuration
├── requirements.txt        # Python dependencies
├── README.md              # This file (English)
├── INSTRUKCJA.md          # Full instruction (Polish)
├── DESCRIPTION.md         # Technical description
│
├── .env                   # Environment configuration (not in repo)
├── .env.example           # Example configuration
├── .token_cache.json      # Token cache (not in repo)
│
├── logs/                  # Application logs
│   ├── unlink_app_*.log           # Application logs
│   └── unlink_results_*.json      # Operation results
│
├── tests/                 # Unit and integration tests
│   ├── test_auth.py
│   ├── test_disassemble.py
│   ├── test_genealogy.py
│   └── ...
│
└── resources/             # Example files and test data
    ├── hmi800.txt                  # Example serial number list
    ├── disassemble_request.json    # Example request
    ├── disassemble_response.json   # Example response
    └── ...
```


## 🔧 Configuration Details

The application uses environment-based configuration via `.env` file:

### Required Environment Variables:
- `ENVIRONMENT` - Default environment (STG/PRD)
- `SITE_NAME` - Site name (e.g., Kwidzyn)
- `EXTERNAL_API_USERNAME` - External API username
- `EXTERNAL_API_PASSWORD` - External API password
- `MENDIX_TOKEN` - Mendix authentication token
- `STG_EXTERNAL_API_URL` - STG External API URL
- `STG_MENDIX_API_URL` - STG Mendix API URL
- `PRD_EXTERNAL_API_URL` - PRD External API URL
- `PRD_MENDIX_API_URL` - PRD Mendix API URL

### Additional Configuration:
Edit [config.py](config.py) to set:
- `USER_CONTEXT` - User data (userId, userName, email, employeeNumber)
- `STATION_CONTEXT` - Station data (routeId, factoryId, stationType)

## 🌟 Features in Detail

### Multi-threaded Processing
- Uses `ThreadPoolExecutor` for parallel processing
- Default: 5 threads (configurable via `--threads`)
- Thread-safe logging and counters
- Progress tracking per thread

### Token Caching
- External API tokens are cached in `.token_cache.json`
- Tokens valid for 8 hours
- Automatic refresh on expiration
- Separate cache per environment

### Comprehensive Logging
- Console output with progress indicators
- File logging with timestamps and thread info
- JSON results file with detailed operation data
- All logs saved to `logs/` directory

## 📊 Output Files

### Log File Format
```
2026-01-22 14:30:00 - [ThreadPoolExecutor-0_0] - INFO - Processing SN: SN123456789
```

### Results JSON Format
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
    "children_unlinked": [...],
    "total_children": 1,
    "successful_unlinks": 1
  }
}
```


## 🛡️ Security

⚠️ **WARNING:** Never commit sensitive data to the repository!

Best practices:
- ✅ `.env` file is in `.gitignore`
- ✅ Use environment variables for sensitive data
- ✅ Keep credentials secure and rotate regularly
- ✅ Always test on STG before PRD
- ✅ PRD executes automatically without confirmation

## 🐛 Troubleshooting

### "Cannot authenticate to External API"
- Check credentials in `.env`
- Verify network access (VPN if remote)
- Ensure API URLs are correct
- Delete `.token_cache.json` and retry

### "MendixToken not configured"
- Add `MENDIX_TOKEN` to `.env`
- Or provide via `-t` parameter

### "WIP not found for serial number"
- Verify serial number is correct
- Check `SITE_NAME` in `.env`
- Ensure WIP exists in selected environment

### SSL/Certificate errors
- Application automatically disables SSL verification for corporate proxies
- Check system proxy settings if issues persist

## 📝 Example Session

```bash
# 1. Check genealogy before unlinking
python main.py -s "SN123456789" -c -e STG

# 2. If OK, unlink the WIP
python main.py -s "SN123456789" -e STG

# 3. Confirm operation
Do you want to process 1 serial numbers in environment STG? (tak/nie): tak

[1/1] [ThreadPoolExecutor-0_0] Processing SN: SN123456789
  ✓ Success - Parent WIP: 4585913, Children unlinked: 1

=== Summary ===
Success: 1
Errors: 0

Results saved to: logs/unlink_results_20260122_143000.json
```

## 🧪 Testing

Run tests from the `tests/` directory:
```bash
# Run all tests
cd tests
python test_auth.py
python test_genealogy.py
python test_disassemble.py
# ... etc
```

## 📚 Documentation

- **[INSTRUKCJA.md](INSTRUKCJA.md)** - Full Polish instruction with detailed examples
- **[DESCRIPTION.md](DESCRIPTION.md)** - Technical description and API documentation
- **[config.py](config.py)** - Configuration reference

## 👤 Author

Amadeusz Kusz (2969118)

## 📄 License

© 2026 Jabil. All rights reserved.

Internal use only.
