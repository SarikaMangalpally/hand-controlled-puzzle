import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import subprocess
import json

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from puzzle.gallery import Gallery, choose_image
from puzzle.storage import Store


class GalleryTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.display.set_mode((1, 1))
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.assets = self.root / 'assets'
        self.assets.mkdir()
        self.store = Store(self.root / 'data' / 'players.db')
        self.gallery = Gallery(self.assets, self.root / 'data', self.store)

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()
        pygame.quit()

    def test_upload_is_copied_cropped_deduplicated_and_reopened(self):
        source = self.root / 'my photo.png'
        surface = pygame.Surface((80, 40))
        surface.fill('red')
        pygame.draw.rect(surface, 'green', (20, 0, 40, 40))
        pygame.image.save(surface, source)
        picture = self.gallery.import_image(source)
        self.assertEqual(picture.id, self.gallery.import_image(source).id)
        source.unlink()
        stored = pygame.image.load(picture.path)
        self.assertEqual(stored.get_size(), (40, 40))
        self.assertEqual(stored.get_at((0, 0))[:3], pygame.Color('green')[:3])
        self.store.close()
        self.store = Store(self.root / 'data' / 'players.db')
        gallery = Gallery(self.assets, self.root / 'data', self.store)
        self.assertEqual([p.id for p in gallery.pictures()], [picture.id])

    def test_invalid_file_does_not_create_gallery_entry(self):
        source = self.root / 'not-an-image.png'
        source.write_bytes(b'not an image')
        with self.assertRaises(ValueError):
            self.gallery.import_image(source)
        self.assertEqual(self.gallery.pictures(), [])

    def test_tiny_image_is_rejected(self):
        source = self.root / 'tiny.png'
        pygame.image.save(pygame.Surface((4, 4)), source)
        with self.assertRaises(ValueError):
            self.gallery.import_image(source)

    def test_file_picker_uses_separate_process_and_handles_cancel_and_failure(self):
        name = str(self.root / 'photo with spaces.png')
        with patch('puzzle.gallery.subprocess.run') as run:
            run.return_value.stdout = json.dumps(name)
            self.assertEqual(choose_image(), Path(name))
            self.assertTrue(run.call_args.args[0][1].endswith('file_picker.py'))
            run.return_value.stdout = 'null'
            self.assertIsNone(choose_image())
            run.side_effect = subprocess.CalledProcessError(1, ['picker'])
            with self.assertRaises(OSError):
                choose_image()


if __name__ == '__main__':
    unittest.main()
