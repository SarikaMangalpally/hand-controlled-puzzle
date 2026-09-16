"""Main-thread hand input lifecycle, independent of camera implementation."""

from time import monotonic

import pygame

from .camera import CameraSession
from .gestures import Gestures


class HandInput:
    def __init__(self, app, model_path):
        self.app = app
        self.model_path = model_path
        self.session = None
        self.gestures = Gestures()
        self.positions = {}
        self.preview = None
        self.show_preview = True
        self.focused = True
        self.status = ''
        self.generation = 0
        self.last_frame = None

    def reset(self):
        for event in self.gestures.reset():
            self.app.cancel_pointer(event.identity)
        self.positions.clear()
        self.generation += 1

    def start(self):
        if self.session is not None:
            return
        self.app.cancel_inputs()
        try:
            self.session = CameraSession(self.model_path)
        except (OSError, RuntimeError) as error:
            self.app._notify(f'Cannot start camera: {error}')
            return
        self.started = monotonic()
        self.last_frame = None
        self.status = 'Starting camera'

    def stop(self):
        self.reset()
        if self.session is not None:
            self.session.close()
            self.session = None
        self.preview = None
        self.status = ''

    def update(self):
        if self.session is None:
            return
        now = monotonic()
        frame = self.session.poll()
        if frame is not None and frame.error:
            self.stop()
            self.app._notify(frame.error)
            return
        if self.last_frame is None and now - self.started > 30:
            self.stop()
            self.app._notify('Camera timed out. Check camera permission, then try Hands again.')
            return
        timestamp = frame.timestamp if frame else self.last_frame
        if timestamp is not None and now - timestamp > 0.5:
            self.reset()
            self.status = 'Tracking interrupted'
            return
        if frame is None:
            return
        self.last_frame = frame.timestamp
        if frame.preview:
            self.preview = pygame.image.frombytes(frame.preview, (160, 120), 'RGB')
        if not self.focused or self.app.scene != 'puzzle':
            return
        self.status = f'{len(frame.hands)} hands detected'
        generation = self.generation
        width, height = self.app.screen.get_size()
        for event in self.gestures.update(frame.hands, frame.timestamp):
            if generation != self.generation:
                break
            position = (round(event.position[0] * (width - 1)),
                        round(event.position[1] * (height - 1)))
            if event.phase == 'cancel':
                self.app.cancel_pointer(event.identity)
                self.positions.pop(event.identity, None)
            else:
                self.positions[event.identity] = position
                if event.phase == 'down':
                    self.app.pointer_down(event.identity, position)
                elif event.phase == 'up':
                    self.app.pointer_up(event.identity, position)

    def draw_cursors(self):
        for identity, position in self.positions.items():
            color = '#147d6b' if identity == 'Left' else '#bd4057'
            pygame.draw.circle(self.app.screen, 'white', position, 12, 3)
            pygame.draw.circle(self.app.screen, color, position, 9,
                               0 if self.gestures.states[identity].pressed else 2)
            self.app.text(identity[0], (position[0] + 14, position[1] - 10), 14, color)
