import os
import threading
import py5
from utils.spotify_client import SpotifyClient

# Pixel footprint of the beam splitter cube on the screen, and the margin inside it.
# All content is scaled and centered to fit within the usable area.
_CUBE_PX     = int(os.getenv("CUBE_SIZE_PX", "460"))
_CUBE_MARGIN = int(os.getenv("CUBE_MARGIN",  "10"))
_USABLE      = _CUBE_PX - 2 * _CUBE_MARGIN

# Art fills 68% of usable height — the remaining 32% accommodates track info below.
# (art + info) / art ≈ 1.47, so 1/1.47 ≈ 0.68 ensures both fit within _USABLE.
_ART_SIZE  = int(_USABLE * 0.68)
_ART_DEPTH = max(4, int(_ART_SIZE * 0.08))  # depth scales proportionally
_UI_SCALE  = _ART_SIZE / 300                 # scale factor relative to 300px reference design
_SPIN_SPEED = 0.018  # radians per frame

# Vertical offset of the art center above h/2 so the whole layout is centered in the cube.
# Content spans: _ART_SIZE above+below art, plus ~93px of info below.
# Content midpoint sits 46.5px below the art center → shift art up by that amount.
_ART_Y_OFFSET = int(46 * _UI_SCALE)


class SpotifyScene:
    def __init__(self):
        """Set up Spotify client and initialise all rendering state."""
        self._spotify = SpotifyClient()
        self._album_img = None
        self._cached_track_id = None
        self._loading_art = False
        self._pending_art_path = None
        self._idle_art = py5.load_image("assets/spotify_idle.png")
        self._angle = 0.0

    def setup(self):
        """Start the Spotify polling thread. Called once after the sketch is ready."""
        self._spotify.start_polling()

    def draw(self):
        """Main draw loop — called every frame by py5."""
        # py5.load_image must run on the draw thread, so art downloaded in the
        # background is staged via _pending_art_path and resolved here.
        if not self._loading_art and self._pending_art_path is not None:
            self._album_img = py5.load_image(self._pending_art_path)
            self._pending_art_path = None

        py5.background(0)

        track = self._spotify.current_track
        self._maybe_reload_art(track)

        w, h = py5.width, py5.height

        self._draw_idle_line(w, h)
        if self._album_img:
            volume = track["volume_percent"] if track else 0
            self._draw_animated_music_curve(w, h, volume)
            self._draw_spinning_art(self._album_img, w, h)
        else:
            self._draw_spinning_art(self._idle_art, w, h)

        if track:
            self._draw_track_info(track, w, h)

        self._angle += _SPIN_SPEED

    # ------------------------------------------------------------------
    # Art loading
    # ------------------------------------------------------------------

    def _maybe_reload_art(self, track):
        """Kick off a background download when the track changes."""
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
        """Download art on a background thread and stage it for the draw thread."""
        path = self._spotify.download_art(url) if url else None
        self._pending_art_path = path
        self._loading_art = False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _art_center_y(self, h):
        """Return the y coordinate of the art center, offset so the full layout is vertically centered in the cube."""
        return h / 2 - _ART_Y_OFFSET

    def _draw_spinning_art(self, img, w, h):
        """Render the album art as a rotating 3D slab with lit edges."""
        cy = self._art_center_y(h)

        py5.push_matrix()
        py5.translate(w / 2, cy, 0)
        py5.rotate_y(self._angle)

        s = _ART_SIZE / 2
        d = _ART_DEPTH / 2
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

        # Back face — UVs are mirrored horizontally so the art reads correctly from behind
        py5.begin_shape(py5.QUADS)
        py5.texture(img)
        py5.vertex( s, -s, -d, 0,  0)
        py5.vertex(-s, -s, -d, iw, 0)
        py5.vertex(-s,  s, -d, iw, ih)
        py5.vertex( s,  s, -d, 0,  ih)
        py5.end_shape()

        # Thin dark edges give the slab a physical feel
        py5.fill(20, 20, 25)
        _quad((-s, -s,  d), (-s, -s, -d), (-s,  s, -d), (-s,  s,  d))  # left
        _quad(( s, -s, -d), ( s, -s,  d), ( s,  s,  d), ( s,  s, -d))  # right
        _quad((-s, -s, -d), ( s, -s, -d), ( s, -s,  d), (-s, -s,  d))  # top
        _quad((-s,  s,  d), ( s,  s,  d), ( s,  s, -d), (-s,  s, -d))  # bottom

        py5.pop_matrix()

    def _draw_track_info(self, track, w, h):
        """Render title, artist, and playback progress bar below the art."""
        cy = self._art_center_y(h)
        text_y = cy + _ART_SIZE / 2 + int(28 * _UI_SCALE)

        py5.hint(py5.DISABLE_DEPTH_TEST)
        py5.no_lights()

        py5.text_align(py5.CENTER, py5.TOP)
        py5.text_size(int(22 * _UI_SCALE))
        py5.fill(255)
        py5.text(track["title"], w / 2, text_y)

        py5.text_size(int(16 * _UI_SCALE))
        py5.fill(160, 160, 180)
        py5.text(track["artist"], w / 2, text_y + int(30 * _UI_SCALE))

        bar_w = _ART_SIZE
        bar_x = w / 2 - bar_w / 2
        bar_y = text_y + int(62 * _UI_SCALE)
        progress = track["progress_ms"] / max(track["duration_ms"], 1)

        py5.no_stroke()
        py5.fill(50, 50, 60)
        py5.rect(bar_x, bar_y, bar_w, 3, 2)
        py5.fill(180, 180, 220)
        py5.rect(bar_x, bar_y, bar_w * progress, 3, 2)

        py5.hint(py5.ENABLE_DEPTH_TEST)

    def _draw_idle_line(self, w, h):
        """Draw a static baseline at the vertical center of the art area."""
        cy = self._art_center_y(h)
        x0 = w / 2 - _ART_SIZE / 2
        x1 = w / 2 + _ART_SIZE / 2

        py5.hint(py5.DISABLE_DEPTH_TEST)
        py5.no_lights()
        py5.no_fill()
        py5.stroke(80, 80, 100)
        py5.stroke_weight(1.5)
        py5.line(x0, cy, x1, cy)
        py5.stroke_weight(1)
        py5.hint(py5.ENABLE_DEPTH_TEST)

    def _draw_animated_music_curve(self, w, h, volume_percent):
        """Draw two animated waveforms behind the art, scaled by playback volume.

        Both curves share the same composite waveform but are phase-shifted by
        half a cycle so they mirror each other as they animate.
        """
        cy = self._art_center_y(h)
        x0 = w / 2 - _ART_SIZE / 2
        steps = 120
        max_amp = _ART_SIZE * 0.25 * (volume_percent / 100)
        t = self._angle

        curves = [
            ((120, 80,  220), 0.0),
            ((80,  180, 200), py5.TWO_PI / 2),
        ]

        py5.hint(py5.DISABLE_DEPTH_TEST)
        py5.no_lights()
        py5.no_fill()
        py5.stroke_weight(2)

        for (r, g, b), phase in curves:
            py5.stroke(r, g, b)
            py5.begin_shape()
            for i in range(steps + 1):
                x_frac = i / steps
                x = x0 + x_frac * _ART_SIZE
                # Layered sine waves at different frequencies for an organic shape
                y = cy + max_amp * (
                    py5.sin(x_frac * py5.TWO_PI * 3 + t * 2.0 + phase) * 0.5
                    + py5.sin(x_frac * py5.TWO_PI * 7 - t * 3.1 + phase) * 0.3
                    + py5.sin(x_frac * py5.TWO_PI * 13 + t * 1.7 + phase) * 0.2
                )
                py5.vertex(x, y)
            py5.end_shape()

        py5.stroke_weight(1)
        py5.hint(py5.ENABLE_DEPTH_TEST)


def _quad(a, b, c, d):
    """Draw a single quad from four (x, y, z) vertex tuples."""
    py5.begin_shape(py5.QUADS)
    py5.vertex(*a)
    py5.vertex(*b)
    py5.vertex(*c)
    py5.vertex(*d)
    py5.end_shape()
