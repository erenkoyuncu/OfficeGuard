import hashlib
import hmac
import json
import secrets
import time

from core.paths import CONFIG_FILE, PROTECTED_DIR


PIN_MIN_LENGTH = 8
PIN_ITERATIONS = 400_000


def _default_config():
    return {
        "version": 1,
        "pin_iterations": PIN_ITERATIONS,
        "pin_salt": None,
        "pin_hash": None,
        "maintenance_until": 0,
        "browser_policy_entries": [],
    }


def load_config():
    if not CONFIG_FILE.exists():
        return _default_config()

    with CONFIG_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    config = _default_config()
    config.update(data)

    return config


def save_config(config):
    PROTECTED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = CONFIG_FILE.with_suffix(
        ".tmp"
    )

    with temp_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            config,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temp_file.replace(
        CONFIG_FILE
    )


def set_pin(new_pin):
    if not isinstance(new_pin, str):
        raise ValueError(
            "PIN string olmalı."
        )

    if len(new_pin) < PIN_MIN_LENGTH:
        raise ValueError(
            f"PIN en az {PIN_MIN_LENGTH} karakter olmalı."
        )

    config = load_config()

    salt = secrets.token_bytes(
        16
    )

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        new_pin.encode("utf-8"),
        salt,
        PIN_ITERATIONS,
    )

    config["pin_iterations"] = (
        PIN_ITERATIONS
    )
    config["pin_salt"] = salt.hex()
    config["pin_hash"] = derived.hex()

    save_config(
        config
    )


def has_pin():
    config = load_config()

    return bool(
        config.get("pin_salt")
        and config.get("pin_hash")
    )


def verify_pin(pin):
    if not isinstance(pin, str):
        return False

    config = load_config()

    try:
        salt = bytes.fromhex(
            config["pin_salt"]
        )

        expected = bytes.fromhex(
            config["pin_hash"]
        )

        iterations = int(
            config["pin_iterations"]
        )
    except Exception:
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        iterations,
    )

    return hmac.compare_digest(
        actual,
        expected,
    )


def set_maintenance_minutes(minutes):
    config = load_config()

    minutes = max(
        0,
        int(minutes),
    )

    if minutes == 0:
        config["maintenance_until"] = 0
    else:
        config["maintenance_until"] = (
            int(time.time())
            + (minutes * 60)
        )

    save_config(
        config
    )

    return config["maintenance_until"]


def clear_maintenance():
    return set_maintenance_minutes(
        0
    )


def maintenance_until():
    config = load_config()

    try:
        return int(
            config.get(
                "maintenance_until",
                0,
            )
        )
    except Exception:
        return 0


def is_maintenance_active():
    return (
        maintenance_until()
        > int(time.time())
    )
