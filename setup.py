import ctypes
import getpass
import os
import shutil
import subprocess
import sys
import time
import winreg
from pathlib import Path

from core.paths import (
    DATA_DIR,
    INSTALL_DIR,
    LOG_DIR,
    PROTECTED_DIR,
    PUBLIC_DIR,
    RUN_REG_PATH,
    RUN_REG_VALUE,
    SERVICE_NAME,
    UNINSTALL_REG_PATH,
)
from core.security import (
    PIN_MIN_LENGTH,
    has_pin,
    set_pin,
)


def resource_root():
    if hasattr(
        sys,
        "_MEIPASS",
    ):
        return Path(
            sys._MEIPASS
        )

    return Path(
        __file__
    ).resolve().parent


PAYLOAD_DIR = (
    resource_root()
    / "payload"
)


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

    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        None,
        str(
            resource_root()
        ),
        1,
    )

    return result > 32


def run(
    command,
    check=True,
    capture=False,
):
    print(
        ">",
        subprocess.list2cmdline(
            [
                str(item)
                for item in command
            ]
        ),
    )

    return subprocess.run(
        command,
        check=check,
        capture_output=capture,
        text=capture,
    )


def setup_dirs():
    for path in [
        INSTALL_DIR,
        DATA_DIR,
        PROTECTED_DIR,
        PUBLIC_DIR,
        LOG_DIR,
    ]:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )


def copy_payload():
    if not PAYLOAD_DIR.exists():
        raise RuntimeError(
            f"Setup payload bulunamadı: {PAYLOAD_DIR}"
        )

    if INSTALL_DIR.exists():
        for item in INSTALL_DIR.iterdir():
            if item.is_dir():
                shutil.rmtree(
                    item,
                    ignore_errors=False,
                )
            else:
                item.unlink()

    for item in PAYLOAD_DIR.iterdir():
        target = (
            INSTALL_DIR
            / item.name
        )

        if item.is_dir():
            shutil.copytree(
                item,
                target,
            )
        else:
            shutil.copy2(
                item,
                target,
            )


def create_pin():
    if has_pin():
        return

    while True:
        pin = getpass.getpass(
            f"OfficeGuard yönetici PIN/parolası "
            f"(en az {PIN_MIN_LENGTH} karakter): "
        )

        confirm = getpass.getpass(
            "Tekrar gir: "
        )

        if pin != confirm:
            print(
                "PIN değerleri eşleşmiyor."
            )
            continue

        try:
            set_pin(
                pin
            )
        except Exception as exc:
            print(
                exc
            )
            continue

        pin = ""
        confirm = ""
        break


def service_exe():
    return (
        INSTALL_DIR
        / "Service"
        / "OfficeGuardService.exe"
    )


def register_service():
    exe = service_exe()

    if not exe.exists():
        raise RuntimeError(
            f"Service EXE bulunamadı: {exe}"
        )

    result = run(
        [
            str(exe),
            "--startup",
            "auto",
            "install",
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "OfficeGuard Windows Service kaydı oluşturulamadı."
        )

    run(
        [
            "sc.exe",
            "failure",
            SERVICE_NAME,
            "reset=",
            "86400",
            "actions=",
            "restart/5000/restart/10000/restart/30000",
        ],
        check=True,
    )

    run(
        [
            "sc.exe",
            "failureflag",
            SERVICE_NAME,
            "1",
        ],
        check=True,
    )


def register_ui_agent():
    ui_exe = (
        INSTALL_DIR
        / "OfficeGuardUI.exe"
    )

    key = winreg.CreateKeyEx(
        winreg.HKEY_LOCAL_MACHINE,
        RUN_REG_PATH,
        0,
        winreg.KEY_SET_VALUE,
    )

    try:
        winreg.SetValueEx(
            key,
            RUN_REG_VALUE,
            0,
            winreg.REG_SZ,
            f'"{ui_exe}"',
        )
    finally:
        winreg.CloseKey(
            key
        )


def register_uninstall():
    uninstaller = (
        INSTALL_DIR
        / "OfficeGuardUninstall.exe"
    )

    key = winreg.CreateKeyEx(
        winreg.HKEY_LOCAL_MACHINE,
        UNINSTALL_REG_PATH,
        0,
        winreg.KEY_SET_VALUE,
    )

    try:
        values = {
            "DisplayName": "OfficeGuard",
            "DisplayVersion": "1.0.0",
            "Publisher": "OfficeGuard",
            "InstallLocation": str(
                INSTALL_DIR
            ),
            "UninstallString": (
                f'"{uninstaller}"'
            ),
            "DisplayIcon": (
                str(
                    INSTALL_DIR
                    / "OfficeGuardAdmin.exe"
                )
            ),
        }

        for name, value in values.items():
            winreg.SetValueEx(
                key,
                name,
                0,
                winreg.REG_SZ,
                value,
            )

        winreg.SetValueEx(
            key,
            "NoModify",
            0,
            winreg.REG_DWORD,
            1,
        )

    finally:
        winreg.CloseKey(
            key
        )


def apply_acl():
    run(
        [
            "icacls",
            str(INSTALL_DIR),
            "/inheritance:r",
            "/grant:r",
            "*S-1-5-18:(OI)(CI)F",
            "*S-1-5-32-544:(OI)(CI)F",
            "*S-1-5-32-545:(OI)(CI)RX",
            "/C",
        ],
        check=True,
    )

    run(
        [
            "icacls",
            str(PROTECTED_DIR),
            "/inheritance:r",
            "/grant:r",
            "*S-1-5-18:(OI)(CI)F",
            "*S-1-5-32-544:(OI)(CI)F",
            "/C",
        ],
        check=True,
    )

    run(
        [
            "icacls",
            str(PUBLIC_DIR),
            "/inheritance:r",
            "/grant:r",
            "*S-1-5-18:(OI)(CI)F",
            "*S-1-5-32-544:(OI)(CI)F",
            "*S-1-5-32-545:(OI)(CI)RX",
            "/C",
        ],
        check=True,
    )


def query_service():
    result = subprocess.run(
        [
            "sc.exe",
            "query",
            SERVICE_NAME,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    output = (
        (result.stdout or "")
        + (result.stderr or "")
    )

    return result.returncode, output


def start_and_wait_service(
    timeout_seconds=30,
):
    run(
        [
            "sc.exe",
            "start",
            SERVICE_NAME,
        ],
        check=False,
    )

    deadline = (
        time.monotonic()
        + timeout_seconds
    )

    last_output = ""

    while (
        time.monotonic()
        < deadline
    ):
        code, output = query_service()
        last_output = output

        upper = output.upper()

        if (
            code == 0
            and "STATE" in upper
            and "RUNNING" in upper
        ):
            return True

        if (
            "STOPPED" in upper
            and "WIN32_EXIT_CODE" in upper
        ):
            break

        time.sleep(
            0.75
        )

    raise RuntimeError(
        "OfficeGuard Service RUNNING durumuna geçmedi.\n"
        + last_output
    )


def main():
    if not ensure_admin():
        print(
            "Yönetici yetkisi alınamadı."
        )
        return

    print()
    print("=" * 68)
    print("OFFICEGUARD 1.0.0 SETUP")
    print("=" * 68)
    print()

    try:
        setup_dirs()
        create_pin()
        copy_payload()
        register_service()
        register_ui_agent()
        register_uninstall()
        apply_acl()
        start_and_wait_service(
            timeout_seconds=30
        )

    except Exception as exc:
        print()
        print("=" * 68)
        print("OFFICEGUARD KURULUMU BAŞARISIZ")
        print("=" * 68)
        print(
            str(exc)
        )
        print()
        input(
            "Çıkmak için Enter..."
        )
        raise

    print()
    print("=" * 68)
    print("OFFICEGUARD KURULUMU BAŞARILI")
    print("=" * 68)
    print(
        f"Program : {INSTALL_DIR}"
    )
    print(
        f"Data    : {DATA_DIR}"
    )
    print()
    print(
        "Hedef bilgisayarda Python kurulumu gerekmiyor."
    )
    print()
    input(
        "Çıkmak için Enter..."
    )


if __name__ == "__main__":
    main()
