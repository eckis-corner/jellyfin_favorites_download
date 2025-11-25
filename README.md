# 📥 Jellyfin Favorites Downloader

Ein praktisches und angenehm unkompliziertes Python-Skript, mit dem du deine Lieblingsfilme und -serien aus Jellyfin ganz automatisch herunterladen kannst.
Alles, was du als **Favorit** markierst – egal ob Filme, einzelne Folgen, ganze Staffeln oder komplette Serien – landet sauber sortiert in deinem lokalen Medienordner.

Das Skript kümmert sich dabei um alles Wichtige:
Es erstellt die richtige Ordnerstruktur für Serien, zeigt dir beim Herunterladen einen Fortschrittsbalken, kann dir vorher ausrechnen, wie viel du runterladen würdest, und hat sogar einen Dry-Run-Modus, falls du erst mal testen willst, ohne etwas anzufassen.

Wenn du möchtest, kannst du sogar deinen Jellyfin-Login direkt hinterlegen, damit das Skript komplett ohne Rückfragen durchläuft.

Kurz gesagt:
Ein kleines Helferlein, das dir jede Menge Klickerei abnimmt und deine Jellyfin-Favoriten automatisch sauber auf deine Festplatte bringt.

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


