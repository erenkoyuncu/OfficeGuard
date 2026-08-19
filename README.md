<p align="center">
  <img src="assets/branding/officeguard-banner.jpg" alt="OfficeGuard — Open-source Windows endpoint application, VPN and browser policy control" width="100%">
</p>

<p align="center">
  <img src="assets/branding/officeguard-app-icon.png" alt="OfficeGuard logo" width="96">
</p>

<h1 align="center">OfficeGuard</h1>

<p align="center">
  Open-source Windows endpoint application, VPN and browser policy control.
</p>

<p align="center">
  <a href="https://github.com/erenkoyuncu/OfficeGuard/actions/workflows/windows-build.yml"><img src="https://github.com/erenkoyuncu/OfficeGuard/actions/workflows/windows-build.yml/badge.svg" alt="Windows Build"></a>
  <a href="https://github.com/erenkoyuncu/OfficeGuard/releases/latest"><img src="https://img.shields.io/github/v/release/erenkoyuncu/OfficeGuard" alt="Latest Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="#installation"><img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue" alt="Windows 10 / 11"></a>
</p>

**OfficeGuard** is an open-source Windows endpoint application-control project for managed office computers.

It runs a Windows Service that monitors blocked applications and VPN clients, applies Chrome / Microsoft Edge URL policies, and shows a local administrator approval screen when a policy violation is detected.

> OfficeGuard is intended for computers you own or administer. It does not attempt to override Windows' local-administrator security boundary.

## Download

The easiest way to try OfficeGuard is the latest pre-built Windows installer:

**[Download the latest OfficeGuard release](https://github.com/erenkoyuncu/OfficeGuard/releases/latest)**

The target PC does **not** need Python installed when using the pre-built setup executable.

## What happens on a violation?

```text
Blocked application starts
        |
        v
OfficeGuardService detects it
        |
        v
Process is terminated
        |
        v
Violation event is published
        |
        v
OfficeGuardUI shows full-screen warning + audible alert
        |
        v
Administrator PIN is required to continue
```

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
- GitHub Actions Windows build verification

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

Runs as a Windows Service and handles:

- process monitoring
- blocked installer detection
- VPN adapter checks
- Chrome / Edge browser policy
- administrator PIN verification
- maintenance state
- local IPC

### OfficeGuardUI

Runs in the interactive Windows session and displays the violation screen. PIN verification is delegated to the Service.

### OfficeGuardAdmin

Provides maintenance mode, resume protection, PIN changes, and the uninstall entry point.

## Installation

Download the latest release and run the setup executable.

1. Launch `OfficeGuardSetup.exe`.
2. Approve the Windows UAC prompt.
3. Create an OfficeGuard administrator PIN/password.
4. Let setup install and start the Windows Service.

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

## Default Rules

Default rules currently include examples for:

- Discord
- Steam
- Epic Games
- Riot / VALORANT / League of Legends
- Battle.net
- Ubisoft Connect
- EA / Origin
- GOG Galaxy
- Proton VPN
- NordVPN
- Surfshark
- Windscribe
- OpenVPN
- WireGuard
- Hamachi
- ExpressVPN
- CyberGhost
- Mullvad
- Private Internet Access
- TunnelBear
- Psiphon

Rules live in:

```text
core/rules.py
```

## Build From Source

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

The build embeds `assets/branding/officeguard.ico` into the Service, UI, Admin tool, Uninstaller, and Setup executable.

### Continuous Integration

Every push and pull request to `main` runs the Windows build workflow in GitHub Actions. The workflow builds the Service, UI, Admin tool, Uninstaller, and final Setup executable, then uploads the Setup as a workflow artifact.

## Branding

Official project assets are kept under:

```text
assets/branding/
```

- `officeguard-logo.png` — full project logo
- `officeguard-banner.jpg` — GitHub / documentation banner
- `officeguard-app-icon.png` — compact application icon
- `officeguard.ico` — Windows executable icon

## Security Model

OfficeGuard assumes employee accounts are standard Windows users.

- `C:\Program Files\OfficeGuard` is read/execute for normal users.
- `SYSTEM` and `Administrators` retain full control.
- Protected configuration is stored in `C:\ProgramData\OfficeGuard\protected`.
- The administrator PIN is stored as a salted PBKDF2-HMAC-SHA256 derived value, not plaintext.

A Windows local administrator ultimately controls the machine. OfficeGuard does not claim otherwise.

## Project Status

OfficeGuard is an experimental open-source endpoint-control project and a practical Windows systems/security learning project.

Potential future work:

- Authenticode code signing
- MSI / enterprise packaging
- AppLocker / WDAC integration
- central policy management
- signed updates
- Windows Event Log integration
- configurable rules from the Admin UI
- automated behavioral tests

## Contributing

Contributions, bug reports, and feature ideas are welcome.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

OfficeGuard is released under the **MIT License**.

See [LICENSE](LICENSE).

## Responsible Use

Deploy OfficeGuard only on Windows devices you own or are authorized to administer. Keep employee accounts as Standard Users; a local Windows Administrator ultimately controls the machine.
