import os
import threading
import time
import tempfile
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

_SCOPE = "user-read-currently-playing user-read-playback-state"
_POLL_INTERVAL = 5  # seconds


class SpotifyClient:
    def __init__(self):
        self._lock = threading.Lock()
        self._current_track = None
        self._stop = threading.Event()
        self._thread = None

        self._sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.environ["SPOTIFY_CLIENT_ID"],
                client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
                redirect_uri=os.environ["SPOTIFY_REDIRECT_URI"],
                scope=_SCOPE,
                open_browser=True,
            )
        )

    def start_polling(self):
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    @property
    def current_track(self):
        with self._lock:
            return self._current_track

    @current_track.setter
    def current_track(self, value):
        with self._lock:
            self._current_track = value

    def _poll_loop(self):
        # Run once immediately, then on interval
        self._fetch()
        while not self._stop.wait(_POLL_INTERVAL):
            self._fetch()

    def _fetch(self):
        try:
            playback = self._sp.current_playback()
            if not playback or not playback.get("is_playing"):
                self.current_track = None
                return

            item = playback.get("item")
            if not item or item.get("type") != "track":
                self.current_track = None
                return

            images = item["album"]["images"]
            # Prefer the largest image (first in list)
            art_url = images[0]["url"] if images else None

            track = {
                "id": item["id"],
                "title": item["name"],
                "artist": ", ".join(a["name"] for a in item["artists"]),
                "album": item["album"]["name"],
                "art_url": art_url,
                "progress_ms": playback.get("progress_ms", 0),
                "duration_ms": item.get("duration_ms", 1),
            }
            self.current_track = track
        except Exception as e:
            print(f"[spotify] fetch error: {e}")

    def download_art(self, url: str) -> str | None:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            suffix = ".jpg" if "jpeg" in resp.headers.get("content-type", "") else ".png"
            path = os.path.join(tempfile.gettempdir(), f"pi_beam_art{suffix}")
            with open(path, "wb") as f:
                f.write(resp.content)
            return path
        except Exception as e:
            print(f"[spotify] art download error: {e}")
            return None
