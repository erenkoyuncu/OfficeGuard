import sys
import json
import socketserver
import threading
import time

import servicemanager
import win32event
import win32service
import win32serviceutil

from core.browser_policy import (
    apply_browser_policies,
    remove_browser_policies,
)
from core.logger import write_log
from core.monitor import (
    MonitorEngine,
    clear_pending_event,
)
from core.paths import (
    API_HOST,
    API_PORT,
    LOG_DIR,
    PROTECTED_DIR,
    PUBLIC_DIR,
    SERVICE_DISPLAY_NAME,
    SERVICE_NAME,
)
from core.security import (
    clear_maintenance,
    is_maintenance_active,
    maintenance_until,
    set_maintenance_minutes,
    set_pin,
    verify_pin,
)


class PinLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.failed = 0
        self.block_until = 0.0

    def can_try(self):
        with self.lock:
            return (
                time.monotonic()
                >= self.block_until
            )

    def success(self):
        with self.lock:
            self.failed = 0
            self.block_until = 0.0

    def failure(self):
        with self.lock:
            self.failed += 1

            if self.failed >= 5:
                self.block_until = (
                    time.monotonic()
                    + 30
                )
                self.failed = 0


PIN_LIMITER = PinLimiter()


def verify_rate_limited(pin):
    if not PIN_LIMITER.can_try():
        return (
            False,
            "Çok fazla hatalı deneme. Kısa süre sonra tekrar deneyin.",
        )

    if verify_pin(
        pin
    ):
        PIN_LIMITER.success()
        return True, None

    PIN_LIMITER.failure()

    return (
        False,
        "Hatalı yönetici PIN/parolası.",
    )


class ApiHandler(
    socketserver.StreamRequestHandler
):
    def send_json(self, payload):
        self.wfile.write(
            (
                json.dumps(
                    payload,
                    ensure_ascii=False,
                )
                + "\n"
            ).encode(
                "utf-8"
            )
        )

    def handle(self):
        try:
            raw = self.rfile.readline(
                16_384
            )

            if not raw:
                return

            request = json.loads(
                raw.decode(
                    "utf-8"
                )
            )
        except Exception:
            self.send_json(
                {
                    "ok": False,
                    "error": "Geçersiz istek.",
                }
            )
            return

        action = request.get(
            "action"
        )

        if action == "ping":
            self.send_json(
                {
                    "ok": True,
                    "service": SERVICE_NAME,
                    "maintenance": (
                        is_maintenance_active()
                    ),
                    "maintenance_until": (
                        maintenance_until()
                    ),
                }
            )
            return

        if action == "verify_event":
            ok, error = verify_rate_limited(
                request.get(
                    "pin",
                    "",
                )
            )

            if not ok:
                write_log(
                    "BAD_PIN",
                    "İhlal ekranında hatalı PIN denemesi.",
                )

                self.send_json(
                    {
                        "ok": False,
                        "error": error,
                    }
                )
                return

            event_id = request.get(
                "event_id"
            )

            if not clear_pending_event(
                event_id
            ):
                self.send_json(
                    {
                        "ok": False,
                        "error": "İhlal olayı değişti veya bulunamadı.",
                    }
                )
                return

            write_log(
                "VIOLATION_UNLOCKED",
                "İhlal ekranı yönetici PIN'i ile onaylandı.",
                {
                    "event_id": event_id
                },
            )

            self.send_json(
                {
                    "ok": True
                }
            )
            return

        if action in {
            "maintenance",
            "resume",
            "change_pin",
            "verify_pin",
        }:
            ok, error = verify_rate_limited(
                request.get(
                    "pin",
                    "",
                )
            )

            if not ok:
                self.send_json(
                    {
                        "ok": False,
                        "error": error,
                    }
                )
                return

            if action == "verify_pin":
                self.send_json(
                    {
                        "ok": True
                    }
                )
                return

            if action == "maintenance":
                minutes = int(
                    request.get(
                        "minutes",
                        15,
                    )
                )

                until = set_maintenance_minutes(
                    minutes
                )

                write_log(
                    "MAINTENANCE_ENABLED",
                    "Bakım modu açıldı.",
                    {
                        "minutes": minutes,
                        "until": until,
                    },
                )

                self.send_json(
                    {
                        "ok": True,
                        "maintenance_until": until,
                    }
                )
                return

            if action == "resume":
                clear_maintenance()

                write_log(
                    "MAINTENANCE_DISABLED",
                    "Bakım modu kapatıldı.",
                )

                self.send_json(
                    {
                        "ok": True
                    }
                )
                return

            if action == "change_pin":
                try:
                    set_pin(
                        request.get(
                            "new_pin",
                            "",
                        )
                    )
                except Exception as exc:
                    self.send_json(
                        {
                            "ok": False,
                            "error": str(exc),
                        }
                    )
                    return

                write_log(
                    "PIN_CHANGED",
                    "OfficeGuard yönetici PIN'i değiştirildi.",
                )

                self.send_json(
                    {
                        "ok": True
                    }
                )
                return

        self.send_json(
            {
                "ok": False,
                "error": "Bilinmeyen action.",
            }
        )


class LocalApiServer(
    socketserver.ThreadingTCPServer
):
    allow_reuse_address = True
    daemon_threads = True


class OfficeGuardService(
    win32serviceutil.ServiceFramework
):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = (
        SERVICE_DISPLAY_NAME
    )
    _svc_description_ = (
        "OfficeGuard application, VPN and browser access enforcement service."
    )

    def __init__(self, args):
        super().__init__(
            args
        )

        self.stop_event = (
            win32event.CreateEvent(
                None,
                0,
                0,
                None,
            )
        )

        self.running = True
        self.api_server = None

    def SvcStop(self):
        self.ReportServiceStatus(
            win32service.SERVICE_STOP_PENDING
        )

        self.running = False

        win32event.SetEvent(
            self.stop_event
        )

        if self.api_server:
            try:
                self.api_server.shutdown()
            except Exception:
                pass

    def start_api(self):
        self.api_server = LocalApiServer(
            (
                API_HOST,
                API_PORT,
            ),
            ApiHandler,
        )

        thread = threading.Thread(
            target=self.api_server.serve_forever,
            name="OfficeGuardLocalApi",
            daemon=True,
        )

        thread.start()

    def SvcDoRun(self):
        servicemanager.LogInfoMsg(
            "OfficeGuard service starting."
        )

        PROTECTED_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )
        PUBLIC_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )
        LOG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        write_log(
            "SERVICE_START",
            "OfficeGuard Windows Service başladı.",
        )

        self.start_api()

        monitor = MonitorEngine()
        monitor.initialize_baselines()

        browser_enabled = False
        last_registry = 0.0
        last_adapter = 0.0

        if is_maintenance_active():
            try:
                remove_browser_policies()
            except Exception as exc:
                write_log(
                    "BROWSER_POLICY_ERROR",
                    "Başlangıç bakım modunda browser policy kaldırılamadı.",
                    {
                        "error": str(exc)
                    },
                )
        else:
            try:
                apply_browser_policies()
                browser_enabled = True
            except Exception as exc:
                write_log(
                    "BROWSER_POLICY_ERROR",
                    "Başlangıçta browser policy uygulanamadı.",
                    {
                        "error": str(exc)
                    },
                )

        while self.running:
            if is_maintenance_active():
                if browser_enabled:
                    try:
                        remove_browser_policies()
                    except Exception as exc:
                        write_log(
                            "BROWSER_POLICY_ERROR",
                            "Bakım modunda browser policy kaldırılamadı.",
                            {
                                "error": str(exc)
                            },
                        )

                    browser_enabled = False

            else:
                if not browser_enabled:
                    try:
                        apply_browser_policies()
                        browser_enabled = True
                    except Exception as exc:
                        write_log(
                            "BROWSER_POLICY_ERROR",
                            "Browser policy uygulanamadı.",
                            {
                                "error": str(exc)
                            },
                        )

                try:
                    monitor.scan_processes()
                except Exception as exc:
                    write_log(
                        "PROCESS_SCAN_ERROR",
                        "Process taraması hata verdi.",
                        {
                            "error": str(exc)
                        },
                    )

                now = time.monotonic()

                if (
                    now - last_registry
                    >= 10
                ):
                    last_registry = now

                    try:
                        monitor.scan_installed_apps()
                    except Exception as exc:
                        write_log(
                            "INSTALL_SCAN_ERROR",
                            "Installed apps taraması hata verdi.",
                            {
                                "error": str(exc)
                            },
                        )

                if (
                    now - last_adapter
                    >= 5
                ):
                    last_adapter = now

                    try:
                        monitor.scan_adapters()
                    except Exception as exc:
                        write_log(
                            "ADAPTER_SCAN_ERROR",
                            "Network adapter taraması hata verdi.",
                            {
                                "error": str(exc)
                            },
                        )

            result = (
                win32event.WaitForSingleObject(
                    self.stop_event,
                    750,
                )
            )

            if (
                result
                == win32event.WAIT_OBJECT_0
            ):
                break

        if self.api_server:
            try:
                self.api_server.server_close()
            except Exception:
                pass

        write_log(
            "SERVICE_STOP",
            "OfficeGuard Windows Service durdu.",
        )


def main():
    if (
        getattr(sys, "frozen", False)
        and len(sys.argv) == 1
    ):
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(
            OfficeGuardService
        )
        servicemanager.StartServiceCtrlDispatcher()
        return

    win32serviceutil.HandleCommandLine(
        OfficeGuardService
    )


if __name__ == "__main__":
    main()
