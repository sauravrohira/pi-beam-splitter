import os
import threading
import tempfile
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from logging import getLogger

logger = getLogger(__name__)

_SCOPE = "user-read-currently-playing user-read-playback-state"
_POLL_INTERVAL = 3  # seconds


class SpotifyClient:
    def __init__(self):
        """Authenticate with Spotify and prepare the polling thread."""
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
        """Start the background thread that polls Spotify on a fixed interval."""
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the polling thread to exit cleanly."""
        self._stop.set()

    @property
    def current_track(self):
        """Return the most recently fetched track dict, or None if nothing is playing."""
        with self._lock:
            return self._current_track

    @current_track.setter
    def current_track(self, value):
        with self._lock:
            self._current_track = value

    def _poll_loop(self):
        """Fetch once immediately, then repeat every _POLL_INTERVAL seconds."""
        self._fetch()
        while not self._stop.wait(_POLL_INTERVAL):
            self._fetch()

    def _fetch(self):
        """Query the Spotify playback API and update current_track."""
        try:
            playback = self._sp.current_playback()
            if not playback or not playback.get("is_playing"):
                self.current_track = None
                return

            logger.debug(f"[spotify] playback: {playback}")
            item = playback.get("item")
            if not item or item.get("type") != "track":
                # Podcasts and local files are not supported
                self.current_track = None
                return

            images = item["album"]["images"]
            art_url = images[0]["url"] if images else None  # largest image is first

            track = {
                "id": item["id"],
                "title": item["name"],
                "artist": ", ".join(a["name"] for a in item["artists"]),
                "album": item["album"]["name"],
                "art_url": art_url,
                "progress_ms": playback.get("progress_ms", 0),
                "duration_ms": item.get("duration_ms", 1),
                "volume_percent": playback.get("device", {}).get("volume_percent", 0),
            }
            self.current_track = track
        except Exception as e:
            print(f"[spotify] fetch error: {e}")

    def download_art(self, url: str) -> str | None:
        """Download album art to a fixed temp path and return it, or None on failure.

        Reuses the same file path on every call to avoid accumulating temp files.
        """
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
