import winreg

from core.logger import write_log
from core.rules import (
    BLOCKED_BROWSER_URLS,
    BROWSER_POLICY_PATHS,
)
from core.security import (
    load_config,
    save_config,
)


def normalize(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def read_values(key):
    values = {}
    index = 0

    while True:
        try:
            name, value, value_type = (
                winreg.EnumValue(
                    key,
                    index,
                )
            )

            values[str(name)] = {
                "value": value,
                "type": value_type,
            }

            index += 1
        except OSError:
            break

    return values


def next_index(values):
    used = set()

    for name in values.keys():
        try:
            used.add(
                int(name)
            )
        except Exception:
            pass

    index = 1

    while index in used:
        index += 1

    return index


def apply_browser_policies():
    config = load_config()

    owned_map = {}

    for item in config.get(
        "browser_policy_entries",
        [],
    ):
        try:
            identity = (
                item["browser"],
                item["path"],
                str(item["value_name"]),
            )

            owned_map[
                identity
            ] = item
        except Exception:
            continue

    added = 0

    for browser, path in (
        BROWSER_POLICY_PATHS.items()
    ):
        key = winreg.CreateKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            path,
            0,
            winreg.KEY_READ
            | winreg.KEY_WRITE,
        )

        try:
            existing = read_values(
                key
            )

            existing_urls = {
                normalize(
                    item["value"]
                )
                for item in existing.values()
                if item["type"]
                == winreg.REG_SZ
            }

            for url in BLOCKED_BROWSER_URLS:
                if (
                    normalize(url)
                    in existing_urls
                ):
                    continue

                value_name = str(
                    next_index(
                        existing
                    )
                )

                winreg.SetValueEx(
                    key,
                    value_name,
                    0,
                    winreg.REG_SZ,
                    url,
                )

                item = {
                    "browser": browser,
                    "path": path,
                    "value_name": value_name,
                    "url": url,
                }

                owned_map[
                    (
                        browser,
                        path,
                        value_name,
                    )
                ] = item

                existing[
                    value_name
                ] = {
                    "value": url,
                    "type": winreg.REG_SZ,
                }

                existing_urls.add(
                    normalize(url)
                )

                added += 1

        finally:
            winreg.CloseKey(
                key
            )

    config[
        "browser_policy_entries"
    ] = list(
        owned_map.values()
    )

    save_config(
        config
    )

    write_log(
        "BROWSER_POLICY_APPLIED",
        "Chrome/Edge URLBlocklist uygulandı.",
        {
            "added": added,
            "rules": len(
                BLOCKED_BROWSER_URLS
            ),
        },
    )


def remove_browser_policies():
    config = load_config()

    owned = config.get(
        "browser_policy_entries",
        [],
    )

    removed = 0

    for item in owned:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                item["path"],
                0,
                winreg.KEY_READ
                | winreg.KEY_WRITE,
            )
        except Exception:
            continue

        try:
            try:
                value, value_type = (
                    winreg.QueryValueEx(
                        key,
                        str(
                            item["value_name"]
                        ),
                    )
                )
            except OSError:
                continue

            if (
                value_type == winreg.REG_SZ
                and normalize(value)
                == normalize(
                    item["url"]
                )
            ):
                winreg.DeleteValue(
                    key,
                    str(
                        item["value_name"]
                    ),
                )
                removed += 1
        finally:
            winreg.CloseKey(
                key
            )

    config[
        "browser_policy_entries"
    ] = []

    save_config(
        config
    )

    write_log(
        "BROWSER_POLICY_REMOVED",
        "OfficeGuard browser policy kayıtları kaldırıldı.",
        {
            "removed": removed
        },
    )
