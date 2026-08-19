import json
import tkinter as tk
import winsound

from core.ipc import send_request
from core.paths import (
    INSTALL_DIR,
    PENDING_EVENT_FILE,
)


POLL_MS = 600
FALLBACK_BEEP_MS = 2500
ALERT_WAV = INSTALL_DIR / "alert.wav"


def load_pending_event():
    if not PENDING_EVENT_FILE.exists():
        return None

    try:
        with PENDING_EVENT_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(
                file
            )
    except Exception:
        return None


class ViolationWindow:
    def __init__(
        self,
        root,
        event,
        on_closed,
    ):
        self.root = root
        self.event = event
        self.on_closed = on_closed
        self.sound_loop = False

        self.window = tk.Toplevel(
            root
        )

        self.window.title(
            "OfficeGuard"
        )

        self.window.configure(
            bg="#000000"
        )

        self.window.attributes(
            "-fullscreen",
            True,
        )
        self.window.attributes(
            "-topmost",
            True,
        )

        self.window.protocol(
            "WM_DELETE_WINDOW",
            lambda: None,
        )

        self.window.bind_all(
            "<Escape>",
            lambda e: "break",
        )
        self.window.bind_all(
            "<Alt-F4>",
            lambda e: "break",
        )

        self.build()
        self.start_sound()

        self.window.after(
            800,
            self.watch_event,
        )

    def build(self):
        outer = tk.Frame(
            self.window,
            bg="#000000",
        )
        outer.pack(
            fill="both",
            expand=True,
        )

        center = tk.Frame(
            outer,
            bg="#000000",
        )
        center.place(
            relx=0.5,
            rely=0.47,
            anchor="center",
        )

        tk.Label(
            center,
            text="OFFICE GUARD",
            fg="#ffffff",
            bg="#000000",
            font=(
                "Segoe UI",
                38,
                "bold",
            ),
        ).pack(
            pady=(
                0,
                18,
            )
        )

        tk.Label(
            center,
            text=self.event.get(
                "title",
                "YETKİSİZ İŞLEM",
            ),
            fg="#ff4d4d",
            bg="#000000",
            font=(
                "Segoe UI",
                25,
                "bold",
            ),
        ).pack(
            pady=(
                0,
                20,
            )
        )

        tk.Label(
            center,
            text=self.event.get(
                "reason",
                "",
            ),
            fg="#eeeeee",
            bg="#000000",
            font=(
                "Segoe UI",
                15,
            ),
            wraplength=920,
            justify="center",
        ).pack(
            pady=(
                0,
                20,
            )
        )

        tk.Label(
            center,
            text=(
                "İşlem OfficeGuard tarafından durduruldu.\n"
                "Devam etmek için yönetici PIN/parolası gereklidir."
            ),
            fg="#aaaaaa",
            bg="#000000",
            font=(
                "Segoe UI",
                13,
            ),
            justify="center",
        ).pack(
            pady=(
                0,
                28,
            )
        )

        self.pin_entry = tk.Entry(
            center,
            show="●",
            justify="center",
            font=(
                "Segoe UI",
                18,
            ),
            width=30,
            relief="flat",
            bd=0,
        )
        self.pin_entry.pack(
            ipady=10,
            pady=(
                0,
                12,
            )
        )

        self.error_label = tk.Label(
            center,
            text="",
            fg="#ff5555",
            bg="#000000",
            font=(
                "Segoe UI",
                12,
                "bold",
            ),
        )
        self.error_label.pack(
            pady=(
                0,
                15,
            )
        )

        tk.Button(
            center,
            text="YÖNETİCİ ONAYI",
            command=self.unlock,
            font=(
                "Segoe UI",
                13,
                "bold",
            ),
            width=22,
            pady=9,
            relief="flat",
            cursor="hand2",
        ).pack()

        self.pin_entry.bind(
            "<Return>",
            lambda e: self.unlock(),
        )

        self.window.after(
            100,
            self.pin_entry.focus_force,
        )

    def start_sound(self):
        if ALERT_WAV.exists():
            try:
                winsound.PlaySound(
                    str(ALERT_WAV),
                    winsound.SND_FILENAME
                    | winsound.SND_ASYNC
                    | winsound.SND_LOOP,
                )
                self.sound_loop = True
                return
            except Exception:
                pass

        self.fallback_beep()

    def fallback_beep(self):
        if self.sound_loop:
            return

        try:
            winsound.MessageBeep(
                winsound.MB_ICONHAND
            )
        except Exception:
            pass

        if self.window.winfo_exists():
            self.window.after(
                FALLBACK_BEEP_MS,
                self.fallback_beep,
            )

    def stop_sound(self):
        try:
            winsound.PlaySound(
                None,
                winsound.SND_PURGE,
            )
        except Exception:
            pass

    def unlock(self):
        pin = self.pin_entry.get()

        if not pin:
            self.error_label.config(
                text="Yönetici PIN/parolası gerekli."
            )
            return

        self.pin_entry.config(
            state="disabled"
        )

        try:
            result = send_request(
                {
                    "action": "verify_event",
                    "event_id": (
                        self.event.get(
                            "event_id"
                        )
                    ),
                    "pin": pin,
                }
            )
        except Exception:
            result = {
                "ok": False,
                "error": "OfficeGuard Service ile bağlantı kurulamadı.",
            }

        pin = ""

        if result.get(
            "ok"
        ):
            self.close()
            return

        self.pin_entry.config(
            state="normal"
        )
        self.pin_entry.delete(
            0,
            tk.END,
        )
        self.error_label.config(
            text=result.get(
                "error",
                "Hatalı yönetici PIN/parolası.",
            )
        )

    def watch_event(self):
        current = load_pending_event()

        if (
            not current
            or current.get(
                "event_id"
            )
            != self.event.get(
                "event_id"
            )
        ):
            self.close()
            return

        self.window.after(
            800,
            self.watch_event,
        )

    def close(self):
        self.stop_sound()

        try:
            self.window.destroy()
        except Exception:
            pass

        self.on_closed()


class OfficeGuardUiAgent:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.current = None

        self.root.after(
            200,
            self.poll,
        )

    def poll(self):
        if self.current is None:
            event = load_pending_event()

            if event:
                self.current = (
                    ViolationWindow(
                        self.root,
                        event,
                        self.on_closed,
                    )
                )

        self.root.after(
            POLL_MS,
            self.poll,
        )

    def on_closed(self):
        self.current = None

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    OfficeGuardUiAgent().run()
