"""Bundled pictures and private, persistent copies of user-selected images."""

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import os
import tempfile
import json
import subprocess
import sys

import pygame

from .storage import Store


@dataclass(frozen=True)
class Picture:
    id: str
    title: str
    path: Path


class Gallery:
    def __init__(self, assets: Path, data: Path, store: Store):
        self.assets, self.data, self.store = assets, data, store
        for path in sorted(assets.glob("*.png")):
            title = {"harbor": "Harbor in Bloom", "conservatory": "Alpine Conservatory"}.get(
                path.stem, path.stem.replace("_", " ").title())
            store.register_image("builtin:" + path.stem, title, "builtin")

    def pictures(self) -> list[Picture]:
        pictures = []
        for row in self.store.images():
            key = row["id"].split(":", 1)[1]
            path = self.assets / f"{key}.png" if row["kind"] == "builtin" else (
                self.data / "images" / f"{key}.png")
            if path.is_file():
                pictures.append(Picture(row["id"], row["title"], path))
        return pictures

    def import_image(self, path: Path) -> Picture:
        if path.stat().st_size > 20 * 1024 * 1024:
            raise ValueError("Choose an image smaller than 20 MB.")
        content = path.read_bytes()
        try:
            image = pygame.image.load(BytesIO(content)).convert()
        except pygame.error as error:
            raise ValueError("Cannot read this image. Choose a PNG or JPEG.") from error
        if min(image.get_size()) < 32:
            raise ValueError("The image must be at least 32 pixels on each side.")
        image = square_image(image, min(2048, min(image.get_size())))
        digest = sha256(content).hexdigest()
        directory = self.data / "images"
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"{digest}.png"
        if not destination.exists():
            handle, temporary = tempfile.mkstemp(suffix=".png", dir=directory)
            os.close(handle)
            try:
                pygame.image.save(image, temporary)
                os.replace(temporary, destination)
            finally:
                Path(temporary).unlink(missing_ok=True)
        title = "".join(c for c in path.stem if c.isprintable())[:80] or "My image"
        picture = Picture("upload:" + digest, title, destination)
        self.store.register_image(picture.id, title, "upload")
        return picture


def square_image(image: pygame.Surface, edge: int) -> pygame.Surface:
    crop_edge = min(image.get_size())
    crop = image.subsurface(((image.get_width() - crop_edge) // 2,
                             (image.get_height() - crop_edge) // 2, crop_edge, crop_edge))
    return pygame.transform.smoothscale(crop, (edge, edge))


def choose_image() -> Path | None:
    # Tk and SDL both own NSApplication on macOS; keep their event loops isolated.
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name('file_picker.py'))],
            capture_output=True, text=True, timeout=300, check=True)
        selected = json.loads(result.stdout)
        if selected is not None and not isinstance(selected, str):
            raise ValueError('Invalid image chooser response.')
        return Path(selected) if selected else None
    except (subprocess.SubprocessError, json.JSONDecodeError) as error:
        raise OSError("The image chooser could not finish. Please try again.") from error
