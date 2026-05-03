# Pi Beam Splitter

A Raspberry Pi display that shows your currently playing Spotify track as a spinning 3D album art slab, rendered in real time using [py5](https://py5coding.org) (Python + Processing).

Designed for a 720×720 touchscreen mounted in a custom enclosure. The `stl_files/` directory contains printable parts for the enclosure.

## What it does

- Polls the Spotify API every 5 seconds for the currently playing track
- Renders the album art as a rotating 3D slab with lit edges
- Displays the track title, artist, and a live progress bar below the art
- Shows a quiet idle screen when nothing is playing
- Runs fullscreen on a Pi or in a window for local development

## Requirements

- Python 3.11
- Java JDK (JPype1, which py5 depends on, requires JNI headers — see [Java setup](#java-setup))
- A Spotify app with a Client ID and Secret ([create one here](https://developer.spotify.com/dashboard))

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd pi-beam-splitter
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Java setup

JPype1 (required by py5) needs a JDK with JNI headers. On macOS with [Temurin](https://adoptium.net):

```bash
# Install via Homebrew
brew install --cask temurin

# Set JAVA_HOME (add to ~/.zshrc to persist)
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-26.jdk/Contents/Home
```

On Raspberry Pi:

```bash
sudo apt install default-jdk
```

### 3. Install dependencies

```bash
JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-26.jdk/Contents/Home \
  pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your Spotify credentials:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

Create your Spotify app at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and add `http://localhost:8888/callback` as a Redirect URI.

Set `DISPLAY_MODE=pi` when running on the Pi for fullscreen output; leave it as `local` for windowed development.

### 5. Run

```bash
python main.py
```

On first run, Spotipy will open a browser to authorize the app. After that, the token is cached and subsequent runs start without a prompt.

## Project structure

```
main.py               # Entry point — py5 sketch setup and draw loop
scenes/
  spotify_scene.py    # 3D rendering: spinning art, track info, progress bar
utils/
  spotify_client.py   # Spotify polling thread and album art downloader
stl_files/            # 3D-printable enclosure parts
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DISPLAY_MODE` | `local` | `local` for windowed, `pi` for fullscreen |
| `CANVAS_SIZE` | `720` | Window size in pixels (square) |
| `SPOTIFY_CLIENT_ID` | — | Spotify app client ID |
| `SPOTIFY_CLIENT_SECRET` | — | Spotify app client secret |
| `SPOTIFY_REDIRECT_URI` | — | Must match the URI in your Spotify app settings |