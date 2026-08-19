import ctypes
import getpass
import subprocess
import sys
import tempfile
import time
import winreg
from pathlib import Path

from core.browser_policy import (
    remove_browser_policies,
)
from core.ipc import send_request
from core.paths import (
    DATA_DIR,
    INSTALL_DIR,
    RUN_REG_PATH,
    RUN_REG_VALUE,
    SERVICE_NAME,
    UNINSTALL_REG_PATH,
)
from core.security import verify_pin


def is_admin():
    try:
        return bool(
            ctypes.windll.shell32.IsUserAnAdmin()
        )
    except Exception:
        return False


def ensure_admin():
    if is_admin():
        return True

    params = " ".join(
        f'"{arg}"'
        for arg in sys.argv
    )

    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        str(INSTALL_DIR),
        1,
    )

    return result > 32


def verify_admin_pin():
    pin = getpass.getpass(
        "OfficeGuard yönetici PIN/parolası: "
    )

    try:
        response = send_request(
            {
                "action": "verify_pin",
                "pin": pin,
            }
        )
        ok = bool(
            response.get("ok")
        )
    except Exception:
        ok = verify_pin(
            pin
        )

    pin = ""

    return ok


def remove_registry_entries():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            RUN_REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )

        try:
            winreg.DeleteValue(
                key,
                RUN_REG_VALUE,
            )
        except FileNotFoundError:
            pass
        finally:
            winreg.CloseKey(
                key
            )
    except OSError:
        pass

    try:
        winreg.DeleteKey(
            winreg.HKEY_LOCAL_MACHINE,
            UNINSTALL_REG_PATH,
        )
    except OSError:
        pass


def stop_and_delete_service():
    subprocess.run(
        [
            "sc.exe",
            "stop",
            SERVICE_NAME,
        ],
        check=False,
    )

    time.sleep(
        2
    )

    subprocess.run(
        [
            "sc.exe",
            "delete",
            SERVICE_NAME,
        ],
        check=False,
    )


def schedule_delete():
    script = Path(
        tempfile.gettempdir()
    ) / "officeguard_remove.cmd"

    content = (
        "@echo off\r\n"
        "ping 127.0.0.1 -n 4 > nul\r\n"
        f'rmdir /s /q "{INSTALL_DIR}"\r\n'
        f'rmdir /s /q "{DATA_DIR}"\r\n'
        'del "%~f0"\r\n'
    )

    script.write_text(
        content,
        encoding="utf-8",
    )

    subprocess.Popen(
        [
            "cmd.exe",
            "/c",
            "start",
            "",
            "/min",
            str(script),
        ],
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS
        ),
    )


def main():
    if not is_admin():
        if ensure_admin():
            return

        print(
            "Yönetici yetkisi alınamadı."
        )
        return

    print()
    print(
        "OFFICE GUARD KALDIRMA"
    )
    print(
        "Windows Administrator + OfficeGuard PIN gereklidir."
    )
    print()

    if not verify_admin_pin():
        print(
            "Hatalı OfficeGuard PIN. Kaldırma iptal edildi."
        )
        input(
            "Çıkmak için Enter..."
        )
        return

    confirm = input(
        "OfficeGuard tamamen kaldırılsın mı? (EVET): "
    ).strip()

    if confirm != "EVET":
        print(
            "Kaldırma iptal edildi."
        )
        return

    try:
        remove_browser_policies()
    except Exception:
        pass

    remove_registry_entries()
    stop_and_delete_service()
    schedule_delete()

    print(
        "OfficeGuard kaldırma işlemi başlatıldı."
    )


if __name__ == "__main__":
    main()
