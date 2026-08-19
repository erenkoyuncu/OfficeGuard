import json
import socket

from core.paths import (
    API_HOST,
    API_PORT,
)


def send_request(payload, timeout=5):
    raw = (
        json.dumps(
            payload,
            ensure_ascii=False,
        )
        + "\n"
    ).encode(
        "utf-8"
    )

    with socket.create_connection(
        (
            API_HOST,
            API_PORT,
        ),
        timeout=timeout,
    ) as sock:
        sock.settimeout(
            timeout
        )
        sock.sendall(
            raw
        )

        chunks = []

        while True:
            chunk = sock.recv(
                4096
            )

            if not chunk:
                break

            chunks.append(
                chunk
            )

            if b"\n" in chunk:
                break

    data = b"".join(
        chunks
    ).split(
        b"\n",
        1,
    )[0]

    return json.loads(
        data.decode(
            "utf-8"
        )
    )
