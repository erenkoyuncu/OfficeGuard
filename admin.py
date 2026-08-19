import ctypes
import sys
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

from core.ipc import send_request
from core.paths import INSTALL_DIR


def format_until(timestamp):
    if not timestamp:
        return "-"

    return time.strftime(
        "%d.%m.%Y %H:%M:%S",
        time.localtime(timestamp),
    )


class AdminApp:
    def __init__(self):
        self.root = tk.Tk()

        self.root.title(
            "OfficeGuard Administration"
        )
        self.root.geometry(
            "520x430"
        )
        self.root.resizable(
            False,
            False,
        )

        self.status_var = tk.StringVar(
            value="Servis durumu kontrol ediliyor..."
        )

        self.build()

        self.root.after(
            250,
            self.refresh_status,
        )

    def build(self):
        frame = tk.Frame(
            self.root,
            padx=28,
            pady=24,
        )
        frame.pack(
            fill="both",
            expand=True,
        )

        tk.Label(
            frame,
            text="OFFICE GUARD",
            font=(
                "Segoe UI",
                24,
                "bold",
            ),
        ).pack(
            pady=(
                0,
                8,
            )
        )

        tk.Label(
            frame,
            textvariable=self.status_var,
            font=(
                "Segoe UI",
                11,
            ),
            wraplength=450,
            justify="center",
        ).pack(
            pady=(
                0,
                24,
            )
        )

        buttons = [
            (
                "15 Dakika Bakım Modu",
                lambda: self.maintenance(
                    15
                ),
            ),
            (
                "30 Dakika Bakım Modu",
                lambda: self.maintenance(
                    30
                ),
            ),
            (
                "Koruma Moduna Dön",
                self.resume,
            ),
            (
                "Yönetici PIN Değiştir",
                self.change_pin,
            ),
            (
                "OfficeGuard'ı Kaldır",
                self.launch_uninstall,
            ),
        ]

        for text, command in buttons:
            tk.Button(
                frame,
                text=text,
                command=command,
                font=(
                    "Segoe UI",
                    11,
                    "bold",
                ),
                width=30,
                pady=7,
            ).pack(
                pady=5
            )

    def ask_pin(self):
        return simpledialog.askstring(
            "OfficeGuard Yönetici Doğrulaması",
            "Yönetici PIN/parolası:",
            show="*",
            parent=self.root,
        )

    def refresh_status(self):
        try:
            response = send_request(
                {
                    "action": "ping"
                },
                timeout=2,
            )

            if response.get(
                "ok"
            ):
                if response.get(
                    "maintenance"
                ):
                    self.status_var.set(
                        "BAKIM MODU AKTİF\nBitiş: "
                        + format_until(
                            response.get(
                                "maintenance_until"
                            )
                        )
                    )
                else:
                    self.status_var.set(
                        "KORUMA AKTİF • OfficeGuard Service çalışıyor"
                    )
            else:
                self.status_var.set(
                    "OfficeGuard Service yanıt vermiyor."
                )
        except Exception:
            self.status_var.set(
                "OfficeGuard Service'e bağlanılamadı."
            )

        self.root.after(
            2500,
            self.refresh_status,
        )

    def maintenance(self, minutes):
        pin = self.ask_pin()

        if pin is None:
            return

        try:
            result = send_request(
                {
                    "action": "maintenance",
                    "pin": pin,
                    "minutes": minutes,
                }
            )
        except Exception as exc:
            messagebox.showerror(
                "OfficeGuard",
                str(exc),
            )
            return

        pin = ""

        if result.get(
            "ok"
        ):
            messagebox.showinfo(
                "OfficeGuard",
                f"Bakım modu {minutes} dakika açıldı.",
            )
        else:
            messagebox.showerror(
                "OfficeGuard",
                result.get(
                    "error",
                    "İşlem başarısız.",
                ),
            )

    def resume(self):
        pin = self.ask_pin()

        if pin is None:
            return

        try:
            result = send_request(
                {
                    "action": "resume",
                    "pin": pin,
                }
            )
        except Exception as exc:
            messagebox.showerror(
                "OfficeGuard",
                str(exc),
            )
            return

        pin = ""

        if result.get(
            "ok"
        ):
            messagebox.showinfo(
                "OfficeGuard",
                "Koruma modu yeniden aktif.",
            )
        else:
            messagebox.showerror(
                "OfficeGuard",
                result.get(
                    "error",
                    "İşlem başarısız.",
                ),
            )

    def change_pin(self):
        current = self.ask_pin()

        if current is None:
            return

        new_pin = simpledialog.askstring(
            "Yeni Yönetici PIN",
            "Yeni PIN/parola (en az 8 karakter):",
            show="*",
            parent=self.root,
        )

        if not new_pin:
            return

        confirm = simpledialog.askstring(
            "Yeni Yönetici PIN",
            "Yeni PIN/parolayı tekrar gir:",
            show="*",
            parent=self.root,
        )

        if new_pin != confirm:
            messagebox.showerror(
                "OfficeGuard",
                "Yeni PIN değerleri eşleşmiyor.",
            )
            return

        try:
            result = send_request(
                {
                    "action": "change_pin",
                    "pin": current,
                    "new_pin": new_pin,
                }
            )
        except Exception as exc:
            messagebox.showerror(
                "OfficeGuard",
                str(exc),
            )
            return

        current = ""
        new_pin = ""
        confirm = ""

        if result.get(
            "ok"
        ):
            messagebox.showinfo(
                "OfficeGuard",
                "Yönetici PIN/parolası değiştirildi.",
            )
        else:
            messagebox.showerror(
                "OfficeGuard",
                result.get(
                    "error",
                    "PIN değiştirilemedi.",
                ),
            )

    def launch_uninstall(self):
        uninstaller = (
            INSTALL_DIR
            / "OfficeGuardUninstall.exe"
        )

        if not uninstaller.exists():
            messagebox.showerror(
                "OfficeGuard",
                "OfficeGuardUninstall.exe bulunamadı.",
            )
            return

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            str(uninstaller),
            None,
            str(
                INSTALL_DIR
            ),
            1,
        )

        if result <= 32:
            messagebox.showerror(
                "OfficeGuard",
                "Yönetici yetkisi alınamadı.",
            )

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AdminApp().run()
