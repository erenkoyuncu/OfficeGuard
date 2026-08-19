import json
import os
import time
import uuid
import winreg

import psutil

from core.logger import write_log
from core.paths import (
    PENDING_EVENT_FILE,
    PUBLIC_DIR,
)
from core.rules import (
    BLOCKED_ADAPTER_RULES,
    BLOCKED_INSTALLED_APP_RULES,
    BLOCKED_PATH_MARKERS,
    BLOCKED_PROCESS_PREFIX_RULES,
    BLOCKED_PROCESS_RULES,
)


def normalize(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def normalize_path(value):
    return normalize(
        value
    ).replace(
        "/",
        "\\",
    )


def match_process(name, exe):
    process_name = normalize(
        name
    )

    if (
        not process_name
        and exe
    ):
        process_name = normalize(
            os.path.basename(exe)
        )

    if (
        process_name
        in BLOCKED_PROCESS_RULES
    ):
        return {
            "matched": True,
            "type": "exact",
            "rule": process_name,
            "label": (
                BLOCKED_PROCESS_RULES[
                    process_name
                ]
            ),
        }

    for prefix, label in (
        BLOCKED_PROCESS_PREFIX_RULES
    ):
        if process_name.startswith(
            normalize(prefix)
        ):
            return {
                "matched": True,
                "type": "prefix",
                "rule": prefix,
                "label": label,
            }

    exe_path = normalize_path(
        exe
    )

    for marker, label in (
        BLOCKED_PATH_MARKERS
    ):
        if (
            normalize_path(marker)
            in exe_path
        ):
            return {
                "matched": True,
                "type": "path",
                "rule": marker,
                "label": label,
            }

    return {
        "matched": False
    }


def terminate_process_tree(process):
    try:
        children = process.children(
            recursive=True
        )
    except Exception:
        children = []

    for child in reversed(
        children
    ):
        try:
            child.terminate()
        except Exception:
            pass

    try:
        process.terminate()
    except psutil.NoSuchProcess:
        return True
    except Exception:
        pass

    _, alive = psutil.wait_procs(
        children + [process],
        timeout=1.5,
    )

    for item in alive:
        try:
            item.kill()
        except Exception:
            pass

    return True


def match_installed(display_name):
    app = normalize(
        display_name
    )

    for blocked, label in (
        BLOCKED_INSTALLED_APP_RULES
    ):
        blocked = normalize(
            blocked
        )

        if (
            app == blocked
            or app.startswith(
                blocked + " "
            )
            or app.startswith(
                blocked + "-"
            )
        ):
            return {
                "matched": True,
                "rule": blocked,
                "label": label,
            }

    return {
        "matched": False
    }


def read_uninstall_key(
    hive,
    path,
):
    programs = set()

    try:
        root = winreg.OpenKey(
            hive,
            path,
        )
    except OSError:
        return programs

    try:
        index = 0

        while True:
            try:
                sub_name = winreg.EnumKey(
                    root,
                    index,
                )
                index += 1
            except OSError:
                break

            try:
                sub = winreg.OpenKey(
                    root,
                    sub_name,
                )
            except OSError:
                continue

            try:
                try:
                    display_name, _ = (
                        winreg.QueryValueEx(
                            sub,
                            "DisplayName",
                        )
                    )

                    if display_name:
                        programs.add(
                            str(
                                display_name
                            ).strip()
                        )
                except OSError:
                    pass
            finally:
                winreg.CloseKey(
                    sub
                )
    finally:
        winreg.CloseKey(
            root
        )

    return programs


def read_installed_programs():
    programs = set()

    for path in [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]:
        programs.update(
            read_uninstall_key(
                winreg.HKEY_LOCAL_MACHINE,
                path,
            )
        )

    try:
        users = winreg.OpenKey(
            winreg.HKEY_USERS,
            "",
        )
    except OSError:
        return programs

    try:
        index = 0

        while True:
            try:
                sid = winreg.EnumKey(
                    users,
                    index,
                )
                index += 1
            except OSError:
                break

            if (
                sid.endswith(
                    "_Classes"
                )
                or not sid.startswith(
                    "S-1-5-"
                )
            ):
                continue

            programs.update(
                read_uninstall_key(
                    winreg.HKEY_USERS,
                    sid
                    + r"\Software\Microsoft\Windows\CurrentVersion\Uninstall",
                )
            )
    finally:
        winreg.CloseKey(
            users
        )

    return programs


def get_blocked_installs():
    blocked = {}

    for program in read_installed_programs():
        match = match_installed(
            program
        )

        if match["matched"]:
            blocked[
                program
            ] = match

    return blocked


def get_blocked_adapters():
    matches = []

    try:
        adapters = (
            psutil.net_if_addrs()
        )
    except Exception:
        return matches

    for name in adapters.keys():
        normalized = normalize(
            name
        )

        for keyword, label in (
            BLOCKED_ADAPTER_RULES
        ):
            if (
                normalize(keyword)
                in normalized
            ):
                matches.append(
                    {
                        "interface": name,
                        "rule": keyword,
                        "label": label,
                    }
                )

    return matches


def publish_violation(
    title,
    reason,
    details=None,
):
    PUBLIC_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if PENDING_EVENT_FILE.exists():
        return None

    event = {
        "event_id": str(
            uuid.uuid4()
        ),
        "created_at": int(
            time.time()
        ),
        "title": title,
        "reason": reason,
        "details": details or {},
    }

    temp = PENDING_EVENT_FILE.with_suffix(
        ".tmp"
    )

    with temp.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            event,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temp.replace(
        PENDING_EVENT_FILE
    )

    return event


def clear_pending_event(event_id):
    if not PENDING_EVENT_FILE.exists():
        return True

    try:
        with PENDING_EVENT_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            event = json.load(
                file
            )

        if (
            event.get("event_id")
            != event_id
        ):
            return False
    except Exception:
        return False

    try:
        PENDING_EVENT_FILE.unlink()
    except FileNotFoundError:
        pass

    return True


class MonitorEngine:
    def __init__(self):
        self.handled_pids = set()
        self.known_blocked_installs = set()
        self.known_blocked_adapters = set()
        self.last_violation = {}

    def initialize_baselines(self):
        self.known_blocked_installs = set(
            get_blocked_installs().keys()
        )

        self.known_blocked_adapters = {
            item["interface"]
            for item in get_blocked_adapters()
        }

        write_log(
            "BASELINE_INITIALIZED",
            "OfficeGuard başlangıç baseline'ı oluşturuldu.",
            {
                "blocked_installs": sorted(
                    self.known_blocked_installs
                ),
                "blocked_adapters": sorted(
                    self.known_blocked_adapters
                ),
            },
        )

    def cooldown(
        self,
        key,
        seconds=8,
    ):
        now = time.monotonic()

        previous = self.last_violation.get(
            key
        )

        self.last_violation[
            key
        ] = now

        return (
            previous is not None
            and now - previous < seconds
        )

    def scan_processes(self):
        current_pids = set()
        violations = []

        for process in psutil.process_iter(
            attrs=[
                "pid",
                "name",
                "exe",
            ]
        ):
            try:
                info = process.info

                pid = info.get(
                    "pid"
                )

                if pid is None:
                    continue

                current_pids.add(
                    pid
                )

                if pid in self.handled_pids:
                    continue

                match = match_process(
                    info.get("name"),
                    info.get("exe"),
                )

                if not match.get(
                    "matched"
                ):
                    continue

                self.handled_pids.add(
                    pid
                )

                violations.append(
                    {
                        "process": process,
                        "pid": pid,
                        "name": info.get("name"),
                        "exe": info.get("exe"),
                        "label": match["label"],
                        "rule": match["rule"],
                        "match_type": match["type"],
                    }
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

        self.handled_pids = (
            self.handled_pids.intersection(
                current_pids
            )
        )

        if not violations:
            return

        labels = set()
        names = set()

        for item in violations:
            labels.add(
                item["label"]
            )

            names.add(
                item["name"]
                or "UNKNOWN"
            )

            terminate_process_tree(
                item["process"]
            )

            write_log(
                "PROCESS_BLOCKED",
                "Yasaklı process sonlandırıldı.",
                {
                    key: value
                    for key, value in item.items()
                    if key != "process"
                },
            )

        labels = sorted(
            labels
        )

        key = (
            "process:"
            + "|".join(labels)
        )

        if self.cooldown(
            key
        ):
            return

        publish_violation(
            "YETKİSİZ UYGULAMA ÇALIŞTIRILDI",
            (
                "Yasaklı uygulama çalıştırma girişimi tespit edildi: "
                + ", ".join(labels)
            ),
            {
                "applications": labels,
                "processes": sorted(
                    names
                ),
            },
        )

    def scan_installed_apps(self):
        blocked = get_blocked_installs()

        current = set(
            blocked.keys()
        )

        new_items = (
            current
            - self.known_blocked_installs
        )

        self.known_blocked_installs = (
            current
        )

        if not new_items:
            return

        labels = sorted(
            {
                blocked[name]["label"]
                for name in new_items
            }
        )

        write_log(
            "BLOCKED_INSTALL",
            "Yeni yasaklı uygulama kurulumu tespit edildi.",
            {
                "programs": sorted(
                    new_items
                ),
                "labels": labels,
            },
        )

        publish_violation(
            "YETKİSİZ UYGULAMA KURULUMU",
            (
                "Yeni yasaklı uygulama kurulumu tespit edildi: "
                + ", ".join(labels)
            ),
            {
                "programs": sorted(
                    new_items
                )
            },
        )

    def scan_adapters(self):
        matches = get_blocked_adapters()

        current = {
            item["interface"]
            for item in matches
        }

        new_names = (
            current
            - self.known_blocked_adapters
        )

        self.known_blocked_adapters = (
            current
        )

        if not new_names:
            return

        new_matches = [
            item
            for item in matches
            if item["interface"]
            in new_names
        ]

        labels = sorted(
            {
                item["label"]
                for item in new_matches
            }
        )

        write_log(
            "BLOCKED_ADAPTER",
            "Yeni yasaklı VPN adapter tespit edildi.",
            {
                "matches": new_matches
            },
        )

        publish_violation(
            "YETKİSİZ VPN / AĞ ARAYÜZÜ",
            (
                "Yasaklı VPN/network adapter tespit edildi: "
                + ", ".join(labels)
            ),
            {
                "matches": new_matches
            },
        )
