from pathlib import Path

APP_NAME = "OfficeGuard"
SERVICE_NAME = "OfficeGuard"
SERVICE_DISPLAY_NAME = "OfficeGuard Endpoint Protection"

INSTALL_DIR = Path(r"C:\Program Files\OfficeGuard")
DATA_DIR = Path(r"C:\ProgramData\OfficeGuard")
PROTECTED_DIR = DATA_DIR / "protected"
PUBLIC_DIR = DATA_DIR / "public"
LOG_DIR = PROTECTED_DIR / "logs"

CONFIG_FILE = PROTECTED_DIR / "config.json"
PENDING_EVENT_FILE = PUBLIC_DIR / "pending_violation.json"
SERVICE_LOG_FILE = LOG_DIR / "service.log"

API_HOST = "127.0.0.1"
API_PORT = 47831

RUN_REG_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
RUN_REG_VALUE = "OfficeGuardUI"

UNINSTALL_REG_PATH = (
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\OfficeGuard"
)
