import threading
import py5
from utils.spotify_client import SpotifyClient

_ART_SIZE = 300   # px — side length of the spinning album art quad
_ART_DEPTH = 24   # px — thickness of the slab
_SPIN_SPEED = 0.018  # radians per frame


class SpotifyScene:
    def __init__(self):
        self._spotify = SpotifyClient()
        self._album_img = None
        self._cached_track_id = None
        self._loading_art = False
        self._pending_art_path = None
        self._angle = 0.0

    def setup(self):
        self._spotify.start_polling()

    def draw(self):
        # Resolve pending art (py5.load_image must be called on the draw thread)
        if not self._loading_art and self._pending_art_path is not None:
            self._album_img = py5.load_image(self._pending_art_path)
            self._pending_art_path = None

        py5.background(0)

        track = self._spotify.current_track
        self._maybe_reload_art(track)

        w, h = py5.width, py5.height

        if self._album_img:
            self._draw_spinning_art(w, h)
        else:
            self._draw_idle(w, h)

        if track:
            self._draw_track_info(track, w, h)

        self._angle += _SPIN_SPEED

    # ------------------------------------------------------------------
    # Art loading
    # ------------------------------------------------------------------

    def _maybe_reload_art(self, track):
        if self._loading_art:
            return
        if track is None:
            if self._cached_track_id is not None:
                self._album_img = None
                self._cached_track_id = None
            return
        if track["id"] == self._cached_track_id:
            return

        self._loading_art = True
        self._cached_track_id = track["id"]
        url = track.get("art_url")
        threading.Thread(target=self._load_art_bg, args=(url,), daemon=True).start()

    def _load_art_bg(self, url):
        path = self._spotify.download_art(url) if url else None
        self._pending_art_path = path
        self._loading_art = False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _draw_spinning_art(self, w, h):
        art_center_y = h * 0.42

        py5.push_matrix()
        py5.translate(w / 2, art_center_y, 0)
        py5.rotate_y(self._angle)

        s = _ART_SIZE / 2
        d = _ART_DEPTH / 2
        img = self._album_img
        iw, ih = img.width, img.height

        py5.ambient_light(60, 60, 80)
        py5.directional_light(200, 200, 220, 0, 0.3, -1)
        py5.no_stroke()

        # Front face
        py5.begin_shape(py5.QUADS)
        py5.texture(img)
        py5.vertex(-s, -s,  d, 0,  0)
        py5.vertex( s, -s,  d, iw, 0)
        py5.vertex( s,  s,  d, iw, ih)
        py5.vertex(-s,  s,  d, 0,  ih)
        py5.end_shape()

        # Back face (horizontally mirrored so it reads correctly from behind)
        py5.begin_shape(py5.QUADS)
        py5.texture(img)
        py5.vertex( s, -s, -d, 0,  0)
        py5.vertex(-s, -s, -d, iw, 0)
        py5.vertex(-s,  s, -d, iw, ih)
        py5.vertex( s,  s, -d, 0,  ih)
        py5.end_shape()

        # Thin edges
        py5.fill(20, 20, 25)
        _quad((-s, -s,  d), (-s, -s, -d), (-s,  s, -d), (-s,  s,  d))  # left
        _quad(( s, -s, -d), ( s, -s,  d), ( s,  s,  d), ( s,  s, -d))  # right
        _quad((-s, -s, -d), ( s, -s, -d), ( s, -s,  d), (-s, -s,  d))  # top
        _quad((-s,  s,  d), ( s,  s,  d), ( s,  s, -d), (-s,  s, -d))  # bottom

        py5.pop_matrix()

    def _draw_track_info(self, track, w, h):
        text_y = h * 0.42 + _ART_SIZE / 2 + 28

        py5.hint(py5.DISABLE_DEPTH_TEST)
        py5.no_lights()

        py5.text_align(py5.CENTER, py5.TOP)
        py5.text_size(22)
        py5.fill(255)
        py5.text(track["title"], w / 2, text_y)

        py5.text_size(16)
        py5.fill(160, 160, 180)
        py5.text(track["artist"], w / 2, text_y + 30)

        # Progress bar
        bar_w = _ART_SIZE
        bar_x = w / 2 - bar_w / 2
        bar_y = text_y + 62
        progress = track["progress_ms"] / max(track["duration_ms"], 1)

        py5.no_stroke()
        py5.fill(50, 50, 60)
        py5.rect(bar_x, bar_y, bar_w, 3, 2)
        py5.fill(180, 180, 220)
        py5.rect(bar_x, bar_y, bar_w * progress, 3, 2)

        py5.hint(py5.ENABLE_DEPTH_TEST)

    def _draw_idle(self, w, h):
        py5.hint(py5.DISABLE_DEPTH_TEST)
        py5.no_lights()
        py5.text_align(py5.CENTER, py5.CENTER)
        py5.text_size(18)
        py5.fill(80, 80, 100)
        py5.text("nothing playing", w / 2, h / 2)
        py5.hint(py5.ENABLE_DEPTH_TEST)


def _quad(a, b, c, d):
    py5.begin_shape(py5.QUADS)
    py5.vertex(*a)
    py5.vertex(*b)
    py5.vertex(*c)
    py5.vertex(*d)
    py5.end_shape()
