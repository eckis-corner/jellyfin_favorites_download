#!/usr/bin/env python3

# WARNUNGEN UNTERDRÜCKEN (z.B. urllib3/OpenSSL)
import warnings
# Warnung von urllib3 (LibreSSL/OpenSSL) unterdrücken – MUSS vor "import requests" kommen!
warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL",
)
warnings.filterwarnings("ignore", module="urllib3")

import requests
from pathlib import Path
import shutil
import getpass
import sys
from typing import Optional, List, Dict, Any
import argparse


# ==========================
# KONFIGURATION
# ==========================

JELLYFIN_URL = "https://YOUR_JELLYFIN_SERVER_URL"  # z.B. https://jellyfin.meinserver.de

TARGET_MOVIES_DIR = Path("/Users/daniel/Work/Filme")
TARGET_SERIES_DIR = Path("/Users/daniel/Work/Serien")

# Optional: feste Zugangsdaten (leer lassen => Eingabeabfrage)
JELLYFIN_USERNAME = ""  # oder "" lassen für Eingabe
JELLYFIN_PASSWORD = ""  # oder "" lassen für Eingabe


# ==========================
# GLOBALE VARIABLEN
# ==========================

ACCESS_TOKEN: Optional[str] = None
USER_ID: Optional[str] = None

DRY_RUN = False
VERBOSE = False
QUIET = False


# ==========================
# LOGGING / AUSGABE
# ==========================

def log_banner():
    if QUIET:
        return
    print(r"""
========================================
  Jellyfin Favorites Downloader
========================================
""")

def log_info(msg: str):
    if QUIET:
        return
    print(msg)

def log_debug(msg: str):
    if VERBOSE and not QUIET:
        print("[DEBUG] " + msg)

def log_warn(msg: str):
    if not QUIET:
        print("[WARN] " + msg)

def log_error(msg: str):
    # Fehler immer anzeigen
    print("[ERROR] " + msg)


# ==========================
# HELFERFUNKTIONEN
# ==========================

def clean_name(name: str) -> str:
    """Unzulässige Zeichen aus Dateinamen entfernen."""
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, "_")
    return name.strip()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_headers() -> Dict[str, str]:
    return {"X-Emby-Token": ACCESS_TOKEN}  # type: ignore[arg-type]


def authenticate() -> None:
    """Mit Benutzername+Passwort bei Jellyfin anmelden und AccessToken + UserId holen."""
    global ACCESS_TOKEN, USER_ID

    log_info(f"Verbinde zu {JELLYFIN_URL} …")

    if JELLYFIN_USERNAME:
        username = JELLYFIN_USERNAME
        log_info(f"Jellyfin Benutzername (aus Konfiguration): {username}")
    else:
        username = input("Jellyfin Benutzername: ")

    if JELLYFIN_PASSWORD:
        password = JELLYFIN_PASSWORD
        log_info("Jellyfin Passwort: (aus Konfiguration)")
    else:
        password = getpass.getpass("Jellyfin Passwort: ")

    url = f"{JELLYFIN_URL}/Users/AuthenticateByName"
    headers = {
        "Content-Type": "application/json",
        "X-Emby-Authorization": (
            'MediaBrowser Client="FavDownloader", '
            'Device="ExternalScript", '
            'DeviceId="favdownloader-1", '
            'Version="1.0.0"'
        ),
    }
    payload = {"Username": username, "Pw": password}

    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        log_error(f"Login fehlgeschlagen: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    data = resp.json()

    ACCESS_TOKEN = data["AccessToken"]
    USER_ID = data["User"]["Id"]
    log_info(f"Anmeldung erfolgreich. User-ID: {USER_ID}")
    if DRY_RUN:
        log_info("[INFO] DRY-RUN aktiv – es werden keine Dateien heruntergeladen.\n")


def get_favorites() -> List[Dict[str, Any]]:
    """
    Holt alle Favoriten des Users:
    - Movie
    - Series
    - Season
    - Episode
    inkl. MediaSources, um Größe auslesen zu können.
    """
    url = f"{JELLYFIN_URL}/Users/{USER_ID}/Items"
    params = {
        "Filters": "IsFavorite",
        "IncludeItemTypes": "Movie,Series,Season,Episode",
        "Recursive": "true",
        "Fields": "Container,SeriesName,ParentIndexNumber,IndexNumber,MediaSources"
    }
    resp = requests.get(url, headers=get_headers(), params=params)
    resp.raise_for_status()
    return resp.json().get("Items", [])


def get_episodes_for_series(series_id: str) -> List[Dict[str, Any]]:
    url = f"{JELLYFIN_URL}/Users/{USER_ID}/Items"
    params = {
        "ParentId": series_id,
        "IncludeItemTypes": "Episode",
        "Recursive": "true",
        "Fields": "Container,SeriesName,ParentIndexNumber,IndexNumber,MediaSources"
    }
    resp = requests.get(url, headers=get_headers(), params=params)
    resp.raise_for_status()
    return resp.json().get("Items", [])


def get_episodes_for_season(season_id: str) -> List[Dict[str, Any]]:
    url = f"{JELLYFIN_URL}/Users/{USER_ID}/Items"
    params = {
        "ParentId": season_id,
        "IncludeItemTypes": "Episode",
        "Recursive": "true",
        "Fields": "Container,SeriesName,ParentIndexNumber,IndexNumber,MediaSources"
    }
    resp = requests.get(url, headers=get_headers(), params=params)
    resp.raise_for_status()
    return resp.json().get("Items", [])


def build_file_extension(item: Dict[str, Any]) -> str:
    """Dateiendung aus 'Container' ableiten (mkv, mp4, etc.)."""
    container = (item.get("Container") or "").strip().lower()
    if not container:
        return ".mkv"
    if not container.startswith("."):
        return "." + container
    return container


def get_item_size_bytes(item: Dict[str, Any]) -> Optional[int]:
    """
    Versucht, die Dateigröße aus MediaSources[0].Size zu bekommen.
    Gibt None zurück, wenn unbekannt.
    """
    media_sources = item.get("MediaSources") or []
    if not media_sources:
        return None
    size = media_sources[0].get("Size")
    if size is None:
        return None
    try:
        return int(size)
    except (TypeError, ValueError):
        return None


# ==========================
# DOWNLOAD-LOGIK MIT PROGRESS-BALKEN
# ==========================

def download_item_file(item_id: str, dest: Path, size_bytes: Optional[int]) -> None:
    """Lädt ein Item über /Items/{id}/Download herunter – mit Fortschrittsanzeige."""
    if dest.exists():
        log_debug(f"Datei existiert bereits, wird übersprungen: {dest}")
        log_info(f"[SKIP] existiert schon: {dest}")
        return

    url = f"{JELLYFIN_URL}/Items/{item_id}/Download"
    resp = requests.get(url, headers=get_headers(), stream=True)
    resp.raise_for_status()

    # Content-Length als Fallback, falls Größe nicht aus MediaSources bekannt
    if size_bytes is None:
        cl = resp.headers.get("Content-Length")
        if cl is not None:
            try:
                size_bytes = int(cl)
            except ValueError:
                size_bytes = None

    ensure_dir(dest.parent)
    tmp = dest.with_suffix(dest.suffix + ".part")

    downloaded = 0
    chunk_size = 1024 * 1024  # 1 MB

    if size_bytes:
        total_mb = size_bytes / (1024 * 1024)
        log_info(f"{dest.name} – ca. {total_mb:.1f} MB")
    else:
        log_info(f"{dest.name} – Größe unbekannt")

    if DRY_RUN:
        log_info("    [DRY-RUN] Download wird nicht ausgeführt.\n")
        return

    with open(tmp, "wb") as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if not chunk:
                continue
            f.write(chunk)
            downloaded += len(chunk)

            if not QUIET:
                if size_bytes:
                    done_mb = downloaded / (1024 * 1024)
                    total_mb = size_bytes / (1024 * 1024)
                    percent = downloaded * 100.0 / size_bytes
                    print(
                        "\r    Fortschritt: %6.1f/%6.1f MB (%5.1f%%)" %
                        (done_mb, total_mb, percent),
                        end="",
                        flush=True,
                    )
                else:
                    done_mb = downloaded / (1024 * 1024)
                    print(
                        "\r    Fortschritt: %6.1f MB" % done_mb,
                        end="",
                        flush=True,
                    )

    if not QUIET:
        print()  # Zeilenumbruch nach dem Balken
    tmp.replace(dest)
    log_info(f"    Fertig: {dest}\n")


# ==========================
# AUFBAU DER DOWNLOAD-TASKS
# ==========================

def build_movie_dest(item: Dict[str, Any]) -> Path:
    title = clean_name(item.get("Name", "Movie-%s" % item["Id"]))
    ext = build_file_extension(item)
    filename = "%s%s" % (title, ext)
    return TARGET_MOVIES_DIR / filename


def build_episode_dest(item: Dict[str, Any]) -> Path:
    series_name = clean_name(item.get("SeriesName", "Unbekannte Serie"))
    season = item.get("ParentIndexNumber", 0) or 0
    episode = item.get("IndexNumber", 0) or 0
    title = clean_name(item.get("Name", "Episode %s" % episode))
    ext = build_file_extension(item)

    season_folder = "Staffel %d" % season
    filename = "S%02dE%02d - %s%s" % (season, episode, title, ext)
    return TARGET_SERIES_DIR / series_name / season_folder / filename


def collect_download_tasks(favorites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Erzeugt eine Liste von Download-Tasks:
    Jeder Task: {item_id, item_type, label, title, dest, size_bytes, will_download}
    Serien und Staffeln werden auf Episoden aufgeklappt.
    Episoden werden nach item_id dedupliziert.
    """
    tasks: List[Dict[str, Any]] = []
    seen_ids = set()

    def add_task_for_item(item: Dict[str, Any], item_type_label: str) -> None:
        item_id = item["Id"]
        if item_id in seen_ids:
            log_debug(f"Doppelte Episode/Film (Id={item_id}) – übersprungen")
            return
        seen_ids.add(item_id)

        if item["Type"] == "Movie":
            dest = build_movie_dest(item)
        else:  # Episode
            dest = build_episode_dest(item)

        size_bytes = get_item_size_bytes(item)
        will_download = not dest.exists()
        title = item.get("Name", item_id)

        tasks.append({
            "item_id": item_id,
            "item_type": item["Type"],
            "label": item_type_label,
            "title": title,
            "dest": dest,
            "size_bytes": size_bytes,
            "will_download": will_download,
        })

    for fav in favorites:
        t = fav.get("Type")
        name = fav.get("Name")
        log_info("%s: %s" % (t, name))

        if t == "Movie":
            add_task_for_item(fav, "Film-Favorit")
        elif t == "Episode":
            add_task_for_item(fav, "Episoden-Favorit")
        elif t == "Series":
            episodes = get_episodes_for_series(fav["Id"])
            log_info("    -> Serie '%s': %d Episoden" % (name, len(episodes)))
            for ep in episodes:
                add_task_for_item(ep, "Serie-Favorit '%s'" % name)
        elif t == "Season":
            episodes = get_episodes_for_season(fav["Id"])
            log_info("    -> Staffel '%s': %d Episoden" % (name, len(episodes)))
            for ep in episodes:
                add_task_for_item(ep, "Staffel-Favorit '%s'" % name)
        else:
            log_warn("Typ nicht unterstützt: %s" % t)

    return tasks


def print_download_summary(tasks: List[Dict[str, Any]]) -> None:
    """Gibt eine Zusammenfassung aus, wieviel heruntergeladen werden soll."""
    to_download = [t for t in tasks if t["will_download"]]
    already_there = [t for t in tasks if not t["will_download"]]

    total_known_bytes = sum(
        t["size_bytes"] for t in to_download if t["size_bytes"] is not None
    )
    unknown_count = sum(
        1 for t in to_download if t["size_bytes"] is None
    )

    total_mb = total_known_bytes / (1024 * 1024) if total_known_bytes else 0.0

    log_info("\n========== Zusammenfassung ==========")
    log_info("Geplante Dateien insgesamt: %d" % len(tasks))
    log_info("  Davon neu zu laden:       %d" % len(to_download))
    log_info("  Bereits vorhanden:        %d" % len(already_there))

    if total_known_bytes:
        log_info("\nGeschätztes Download-Volumen (bekannte Größen): %.1f MB" % total_mb)
    else:
        log_info("\nGeschätztes Download-Volumen: unbekannt (keine Größeninformationen)")

    if unknown_count:
        log_warn("%d Datei(en) ohne bekannte Größe (nicht in MB-Schätzung enthalten)." % unknown_count)

    log_info("=====================================\n")


# ==========================
# ARGUMENTE PARSEN
# ==========================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Jellyfin-Favoriten herunterladen (Filme & Serien)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, was geladen würde – keine Downloads ausführen.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mehr Details und Debug-Informationen ausgeben.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Nur das Nötigste ausgeben (keine Banner, wenig Text).",
    )
    return parser.parse_args()


# ==========================
# MAIN
# ==========================

def main() -> None:
    global DRY_RUN, VERBOSE, QUIET

    args = parse_args()
    DRY_RUN = args.dry_run
    VERBOSE = args.verbose
    QUIET = args.quiet

    log_banner()

    ensure_dir(TARGET_MOVIES_DIR)
    ensure_dir(TARGET_SERIES_DIR)

    authenticate()

    favorites = get_favorites()
    log_info("[INFO] Favoriten insgesamt: %d\n" % len(favorites))

    tasks = collect_download_tasks(favorites)
    print_download_summary(tasks)

    if DRY_RUN:
        log_info("[DRY-RUN] Folgende Dateien würden heruntergeladen werden:\n")
        for t in tasks:
            if not t["will_download"]:
                continue
            size_mb = t["size_bytes"] / (1024 * 1024) if t["size_bytes"] else None
            size_str = "%.1f MB" % size_mb if size_mb else "Größe unbekannt"
            log_info("  - %s '%s'" % (t["item_type"], t["title"]))
            log_info("    -> %s" % t["dest"])
            log_info("    -> %s\n" % size_str)
        return

    # echter Download
    for t in tasks:
        if not t["will_download"]:
            log_info("[SKIP] existiert schon: %s" % t["dest"])
            continue
        download_item_file(t["item_id"], t["dest"], t["size_bytes"])


if __name__ == "__main__":
    main()

# end of file