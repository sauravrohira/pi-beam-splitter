import os
import py5
from dotenv import load_dotenv

load_dotenv()

_CANVAS_SIZE = int(os.getenv("CANVAS_SIZE", "720"))
_DISPLAY_MODE = os.getenv("DISPLAY_MODE", "local")

_scene = None


def settings():
    if _DISPLAY_MODE == "pi":
        py5.full_screen(py5.P3D)
    else:
        py5.size(_CANVAS_SIZE, _CANVAS_SIZE, py5.P3D)


def setup():
    global _scene
    from scenes.spotify_scene import SpotifyScene

    py5.no_cursor()
    py5.color_mode(py5.RGB, 255)
    py5.text_align(py5.CENTER, py5.CENTER)

    _scene = SpotifyScene()
    _scene.setup()


def draw():
    _scene.draw()


py5.run_sketch()
