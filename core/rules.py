BLOCKED_PROCESS_RULES = {
    "discord.exe": "Discord",

    "steam.exe": "Steam",
    "steamservice.exe": "Steam",
    "steamwebhelper.exe": "Steam",

    "epicgameslauncher.exe": "Epic Games",
    "epicwebhelper.exe": "Epic Games",

    "riotclientservices.exe": "Riot Games",
    "riotclientux.exe": "Riot Games",
    "riotclientuxrender.exe": "Riot Games",
    "valorant.exe": "VALORANT",
    "valorant-win64-shipping.exe": "VALORANT",
    "leagueclient.exe": "League of Legends",
    "leagueclientux.exe": "League of Legends",

    "battle.net.exe": "Battle.net",

    "ubisoftconnect.exe": "Ubisoft Connect",
    "upc.exe": "Ubisoft Connect",

    "eadesktop.exe": "EA App",
    "ealauncher.exe": "EA App",
    "eabackgroundservice.exe": "EA App",
    "origin.exe": "EA Origin",

    "galaxyclient.exe": "GOG Galaxy",
    "galaxyclientservice.exe": "GOG Galaxy",

    "protonvpn.exe": "Proton VPN",
    "nordvpn.exe": "NordVPN",
    "nordvpn-service.exe": "NordVPN",
    "surfshark.exe": "Surfshark",
    "surfshark.service.exe": "Surfshark",
    "windscribe.exe": "Windscribe",
    "openvpn.exe": "OpenVPN",
    "openvpn-gui.exe": "OpenVPN",
    "openvpnconnect.exe": "OpenVPN Connect",
    "wireguard.exe": "WireGuard",
    "hamachi-2-ui.exe": "LogMeIn Hamachi",
    "hamachi-2.exe": "LogMeIn Hamachi",
    "expressvpn.exe": "ExpressVPN",
    "expressvpnd.exe": "ExpressVPN",
    "cyberghostvpn.exe": "CyberGhost VPN",
    "mullvad vpn.exe": "Mullvad VPN",
    "mullvad-daemon.exe": "Mullvad VPN",
    "pia-client.exe": "Private Internet Access",
    "pia-service.exe": "Private Internet Access",
    "tunnelbear.exe": "TunnelBear",
    "psiphon3.exe": "Psiphon",
}


BLOCKED_PROCESS_PREFIX_RULES = [
    ("discordsetup", "Discord Installer"),
    ("steamsetup", "Steam Installer"),
    ("epicinstaller", "Epic Games Installer"),
    ("riotclientsetup", "Riot Games Installer"),
    ("battle.net-setup", "Battle.net Installer"),
    ("ubisoftconnectinstaller", "Ubisoft Connect Installer"),
    ("eainstaller", "EA App Installer"),
    ("gog_galaxy", "GOG Galaxy Installer"),

    ("protonvpninstaller", "Proton VPN Installer"),
    ("protonvpnsetup", "Proton VPN Installer"),
    ("nordvpnsetup", "NordVPN Installer"),
    ("nordvpninstaller", "NordVPN Installer"),
    ("surfsharksetup", "Surfshark Installer"),
    ("windscribesetup", "Windscribe Installer"),
    ("openvpn-connect", "OpenVPN Installer"),
    ("openvpn-installer", "OpenVPN Installer"),
    ("wireguard-installer", "WireGuard Installer"),
    ("expressvpnsetup", "ExpressVPN Installer"),
    ("cyberghostvpnsetup", "CyberGhost VPN Installer"),
    ("mullvadvpn", "Mullvad VPN Installer"),
    ("pia-windows", "Private Internet Access Installer"),
    ("tunnelbear-installer", "TunnelBear Installer"),
]


BLOCKED_PATH_MARKERS = [
    (r"\steamapps\common\\", "Steam Oyunu"),
    (r"\riot games\\", "Riot Games"),
    (r"\epic games\\", "Epic Games"),
    (r"\origin games\\", "EA / Origin Oyunu"),
    (r"\ea games\\", "EA Oyunu"),
    (r"\ubisoft game launcher\games\\", "Ubisoft Oyunu"),
    (r"\gog galaxy\games\\", "GOG Oyunu"),
]


BLOCKED_INSTALLED_APP_RULES = [
    ("discord", "Discord"),
    ("steam", "Steam"),
    ("epic games launcher", "Epic Games Launcher"),
    ("riot client", "Riot Client"),
    ("valorant", "VALORANT"),
    ("league of legends", "League of Legends"),
    ("battle.net", "Battle.net"),
    ("ubisoft connect", "Ubisoft Connect"),
    ("ea app", "EA App"),
    ("origin", "EA Origin"),
    ("gog galaxy", "GOG Galaxy"),

    ("proton vpn", "Proton VPN"),
    ("protonvpn", "Proton VPN"),
    ("nordvpn", "NordVPN"),
    ("nord vpn", "NordVPN"),
    ("surfshark", "Surfshark"),
    ("windscribe", "Windscribe"),
    ("openvpn", "OpenVPN"),
    ("wireguard", "WireGuard"),
    ("logmein hamachi", "LogMeIn Hamachi"),
    ("hamachi", "LogMeIn Hamachi"),
    ("expressvpn", "ExpressVPN"),
    ("express vpn", "ExpressVPN"),
    ("cyberghost", "CyberGhost VPN"),
    ("mullvad vpn", "Mullvad VPN"),
    ("private internet access", "Private Internet Access"),
    ("tunnelbear", "TunnelBear"),
    ("psiphon", "Psiphon"),
]


BLOCKED_BROWSER_URLS = [
    "discord.com",
    "discord.gg",
    "discordapp.com",

    "steampowered.com",
    "steamcommunity.com",
    "steamstatic.com",

    "epicgames.com",

    "riotgames.com",
    "playvalorant.com",
    "leagueoflegends.com",

    "battle.net",
    "blizzard.com",
    "ubisoft.com",
    "ea.com",
    "gog.com",

    "protonvpn.com",
    "nordvpn.com",
    "surfshark.com",
    "windscribe.com",
    "openvpn.net",
    "wireguard.com",
    "expressvpn.com",
    "cyberghostvpn.com",
    "mullvad.net",
    "privateinternetaccess.com",
    "tunnelbear.com",
    "psiphon.ca",
]


BROWSER_POLICY_PATHS = {
    "Google Chrome": r"SOFTWARE\Policies\Google\Chrome\URLBlocklist",
    "Microsoft Edge": r"SOFTWARE\Policies\Microsoft\Edge\URLBlocklist",
}


BLOCKED_ADAPTER_RULES = [
    ("protonvpn", "Proton VPN Adapter"),
    ("nordlynx", "NordVPN / NordLynx Adapter"),
    ("nordvpn", "NordVPN Adapter"),
    ("surfshark", "Surfshark Adapter"),
    ("windscribe", "Windscribe Adapter"),
    ("expressvpn", "ExpressVPN Adapter"),
    ("cyberghost", "CyberGhost VPN Adapter"),
    ("mullvad", "Mullvad VPN Adapter"),
    ("hamachi", "LogMeIn Hamachi Adapter"),
    ("tunnelbear", "TunnelBear Adapter"),
]
