# Contributing

Contributions are welcome.

## Development

Use Windows 10/11 and preferably a test VM or non-production machine.

```cmd
python -m pip install psutil pywin32 pyinstaller
```

## Pull Requests

1. Fork the repository.
2. Create a focused feature branch.
3. Test the change on Windows.
4. Run `build_windows.cmd`.
5. Confirm the OfficeGuard service reaches `RUNNING`.
6. Submit a pull request describing what changed, why, and how it was tested.

## Guidelines

- Keep enforcement in the Service/core layer.
- Keep interactive UI out of the Windows Service.
- Avoid broad process substring matching that creates false positives.
- Never log administrator PINs or secrets.
- Preserve administrator recovery and uninstall paths.
- Do not add features intended to defeat Windows recovery or the local-administrator security boundary.
