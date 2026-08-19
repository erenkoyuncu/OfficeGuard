# OfficeGuard

**OfficeGuard** is an open-source Windows endpoint application-control project for managed office computers.

It runs a Windows Service that monitors blocked applications and VPN clients, applies Chrome / Microsoft Edge URL policies, and shows a local administrator approval screen when a policy violation is detected.

> OfficeGuard is intended for computers you own or administer. It does not attempt to override Windows' local-administrator security boundary.

## Features

- Windows Service based enforcement
- Application and game-launcher blocking
- VPN client and network-adapter detection
- Chrome `URLBlocklist` policy enforcement
- Microsoft Edge `URLBlocklist` policy enforcement
- Full-screen policy violation screen
- Audible security alerts (custom `alert.wav` is optional; Windows warning sound is used as fallback)
- Administrator PIN verification
- Maintenance mode
- Protected configuration and logs
- Administrator-controlled uninstall
- Standalone Windows setup build

## Architecture

```text
OfficeGuardSetup.exe
        |
        +-- C:\Program Files\OfficeGuard\
            |
            +-- Service\
            |   +-- OfficeGuardService.exe
            |   +-- _internal\
            |
            +-- OfficeGuardUI.exe
            +-- OfficeGuardAdmin.exe
            +-- OfficeGuardUninstall.exe
            +-- alert.wav (optional)
```

### OfficeGuardService

Runs as a Windows Service and handles process monitoring, blocked installer detection, VPN adapter checks, browser policy, administrator PIN verification, maintenance state, and local IPC.

### OfficeGuardUI

Runs in the interactive Windows session and displays the violation screen. PIN verification is delegated to the Service.

### OfficeGuardAdmin

Provides maintenance mode, resume protection, PIN changes, and the uninstall entry point.

## Build

OfficeGuard currently builds on Windows.

Requirements on the **build machine**:

- Windows 10 / 11
- Python 3.13+
- PyInstaller
- pywin32
- psutil

Run:

```cmd
build_windows.cmd
```

The result is:

```text
dist\OfficeGuardSetup.exe
```

Target PCs do not need Python installed.

## Installation

Run `OfficeGuardSetup.exe`, approve UAC, and create an OfficeGuard administrator PIN/password.

Verify the service:

```cmd
sc query OfficeGuard
```

Expected:

```text
STATE : 4  RUNNING
```

## Browser Policy Verification

Chrome:

```text
chrome://policy
```

Edge:

```text
edge://policy
```

Look for `URLBlocklist`.

## Rules

Default rules include Discord, Steam, Epic Games, Riot/VALORANT/League of Legends, Battle.net, Ubisoft Connect, EA/Origin, GOG Galaxy, and common VPN clients.

Rules live in:

```text
core/rules.py
```

## Security Model

OfficeGuard assumes employee accounts are standard Windows users.

- `C:\Program Files\OfficeGuard` is read/execute for normal users.
- `SYSTEM` and `Administrators` retain full control.
- Protected configuration is stored in `C:\ProgramData\OfficeGuard\protected`.
- The administrator PIN is stored as a salted PBKDF2-HMAC-SHA256 derived value, not plaintext.

A Windows local administrator ultimately controls the machine. OfficeGuard does not claim otherwise.

## Project Status

OfficeGuard is an experimental open-source endpoint-control project and a practical Windows systems/security learning project.

Future areas include code signing, MSI packaging, AppLocker/WDAC integration, central policy management, signed updates, Windows Event Log integration, and automated tests.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

## Responsible Use

Deploy OfficeGuard only on Windows devices you own or are authorized to administer. Keep employee accounts as Standard Users; a local Windows Administrator ultimately controls the machine.
