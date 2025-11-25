# 📥 Jellyfin Favorites Downloader

Ein vielseitiges und robustes Python-Skript, das es ermöglicht, alle in Jellyfin als **Favoriten** markierten Filme, Episoden, Staffeln oder kompletten Serien automatisch herunterzuladen.
Das Skript nutzt die Jellyfin-API, analysiert intelligent die markierten Inhalte und legt sie anschließend in einer klar strukturierten Medienbibliothek ab – inklusive automatisch erzeugter Ordner für Serien, Staffeln und korrekt benannten Episoden.

Dank integrierter Funktionen wie einer Download-Fortschrittsanzeige, einer vollständigen Volumen- und Aufgabenanalyse, einem DRY-RUN-Modus zur Vorschau aller Aktionen, sowie der Option für einen automatischen Login per hinterlegtem Benutzername und Passwort, eignet sich das Skript sowohl für einfache Anwender als auch für fortgeschrittene Automatisierungs-Workflows.

Es bietet eine zuverlässige, flexible und komfortable Möglichkeit, die eigenen Lieblingsinhalte aus Jellyfin lokal zu sichern oder zu archivieren – vollständig automatisiert und ohne manuelle Eingriffe.

## ✨ Funktionen

### 🎬 Unterstützte Favoriten-Arten

-   **Filme**
-   **Einzelne Episoden**
-   **Komplette Staffeln** (alle Episoden)
-   **Komplette Serien** (alle Staffel und all Episoden)

### 📁 Automatische Ordnerstruktur

Downloads werden lokal strukturiert abgelegt:

    Filme/
        Filmname (Jahr).mkv

    Serien/
        Serienname/
            Staffel 1/
                S01E01 - Episodentitel.mkv
                S01E02 - Episodentitel.mkv

### 🧠 Intelligente Erkennung

-   Bereits vorhandene Dateien werden **übersprungen**
-   Doppelte Einträge werden **dedupliziert**
-   Staffel- und Serienfavoriten werden vollständig **auf Episoden
    heruntergebrochen**

### 🔍 Analyse vor dem Download

-   Anzahl der geplanten Downloads
-   Anzahl bereits vorhandener Dateien
-   Geschätztes Downloadvolumen in MB (falls verfügbar)

### 🧪 DRY-RUN Modus

Zeigt an, was heruntergeladen würde -- ohne etwas zu laden:

``` bash
python3 jellyfin_favorites_download.py --dry-run
```

### 📊 Fortschrittsbalken pro Datei

Jeder Download zeigt: - heruntergeladene MB - Prozentwert - Gesamtgröße
(falls bekannt)

### 🔐 Optionaler Auto-Login

Benutzername/Passwort können im Skript hinterlegt werden.

### 🔈 Quiet & Verbose Modes

-   **Quiet:** minimale Ausgabe\
-   **Verbose:** zusätzliche Debug-Informationen

## 📦 Voraussetzungen

-   Python **3.9 oder neuer**
-   Das Python-Paket `requests`:

``` bash
pip3 install requests
```

## ⚙️ Konfiguration

``` python
JELLYFIN_URL = "https://dein-jellyfin-server.de"

TARGET_MOVIES_DIR = Path("/Pfad/zu/Filme")
TARGET_SERIES_DIR = Path("/Pfad/zu/Serien")

JELLYFIN_USERNAME = "dein_benutzer"
JELLYFIN_PASSWORD = "dein_passwort"
```

## 🏁 Verwendung

### Standardausführung

``` bash
python3 jellyfin_favorites_download.py
```

### Nur anzeigen, was passieren würde

``` bash
python3 jellyfin_favorites_download.py --dry-run
```

### Quiet-Modus

``` bash
python3 jellyfin_favorites_download.py --quiet
```

### Verbose-Modus

``` bash
python3 jellyfin_favorites_download.py --verbose
```

## 🛠️ Ablauf & Funktionsweise

1.  **Authentifizierung**\
2.  **Favoritenabfrage**\
3.  **Auflösen der Favoriten**\
4.  **Vorbereitung**\
5.  **Download**

## 🔐 Sicherheitshinweis

``` bash
chmod 600 jellyfin_favorites_download.py
```

## 💡 Erweiterungsmöglichkeiten --> Version 2.0

-   JDownloader-Integration\
-   Filter: `--only-movies`, `--only-series`\
-   Limitierung: `--max-downloads`\
-   Cronjobs\
-   Passwort aus .env statt im Code\
-   Fortschrittbalken-Design


