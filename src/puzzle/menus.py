"""Profile, picture selection, and leaderboard screens."""

import pygame

from .formatting import format_duration


class Menus:
    def __init__(self, app):
        self.app = app

    def gallery_capacity(self):
        width, height = self.app.screen.get_size()
        return max(1, (width - 96) // 216) * max(1, (height - 300) // 224)

    def buttons(self):
        app = self.app
        width, height = app.screen.get_size()
        if app.scene == "start":
            buttons = {"start": pygame.Rect(48, 242, 360, 46)}
            for index, player in enumerate(app.players[app.profile_page * 6:][:6]):
                buttons[f"player:{player['id']}"] = pygame.Rect(460, 158 + index * 66, width - 508, 56)
            buttons.update({"profiles_prev": pygame.Rect(460, height - 70, 44, 38),
                            "profiles_next": pygame.Rect(width - 92, height - 70, 44, 38)})
            return buttons
        if app.scene == "setup":
            buttons = {"back": pygame.Rect(48, 35, 92, 40),
                       "import": pygame.Rect(width - 198, 35, 150, 40),
                       "grid_less": pygame.Rect(48, 146, 44, 46),
                       "grid_field": pygame.Rect(102, 146, 84, 46),
                       "grid_more": pygame.Rect(196, 146, 44, 46),
                       "begin": pygame.Rect(width - 218, 142, 170, 48),
                       "leaderboard": pygame.Rect(width - 400, 142, 170, 48),
                       "gallery_prev": pygame.Rect(48, height - 62, 44, 38),
                       "gallery_next": pygame.Rect(width - 92, height - 62, 44, 38)}
            columns = max(1, (width - 96) // 216)
            capacity = self.gallery_capacity()
            for index, picture in enumerate(app.pictures[app.gallery_page * capacity:][:capacity]):
                buttons[f"image:{picture.id}"] = pygame.Rect(
                    48 + (index % columns) * 216, 234 + (index // columns) * 224, 200, 216)
            return buttons
        return {"back_results": pygame.Rect(48, 35, 92, 40),
                "scores_prev": pygame.Rect(48, height - 62, 44, 38),
                "scores_next": pygame.Rect(width - 92, height - 62, 44, 38)}

    def draw(self):
        app = self.app
        app.screen.fill("#f4f6f8")
        buttons = self.buttons()
        width, height = app.screen.get_size()
        if app.scene == "start":
            app.text("Hand-Controlled Puzzle", (48, 35), 32)
            app.text("Player name", (48, 134), 17)
            field = pygame.Rect(48, 170, 360, 52)
            pygame.draw.rect(app.screen, "white", field, border_radius=6)
            pygame.draw.rect(app.screen, "#147d6b", field, 2, border_radius=6)
            name = app.fit_text(app.player_name, 320, 20)
            app.text(name, (62, 185), 20)
            if pygame.time.get_ticks() % 1000 < 500:
                x = 62 + app.fonts[20].size(name)[0]
                pygame.draw.line(app.screen, '#147d6b', (x, 182), (x, 210), 2)
            app._button(buttons["start"], "Continue", True, disabled=not app.player_name.strip())
            preview = pygame.transform.smoothscale(app.source, (240, 240))
            app.screen.blit(preview, (48, 330))
            app.text("Local players", (460, 118), 24)
            if not app.players:
                app.text("No saved players yet", (460, 175), 17, "#606f77")
            for player in app.players[app.profile_page * 6:][:6]:
                rect = buttons[f"player:{player['id']}"]
                app._button(rect, "")
                app.text(app.fit_text(player['name'], rect.width - 140, 20),
                         (rect.x + 12, rect.y + 6), 20)
                app.text(f"{player['solved']} solved  /  {player['visits']} visits",
                         (rect.x + 12, rect.y + 33), 14, "#606f77")
                app.text(player['last_seen'][:10], (rect.right - 105, rect.y + 20), 14, "#606f77")
            self._pages(buttons, "profiles", app.profile_page, len(app.players), 6)
        elif app.scene == "setup":
            app._button(buttons["back"], "Back")
            app.text("Choose a puzzle", (158, 39), 24)
            app._button(buttons["import"], "Upload image")
            app.text(f"{app.player_name}  /  Grid size", (48, 112), 17)
            app._button(buttons["grid_less"], "-", disabled=app.grid_size <= 2)
            app._button(buttons["grid_more"], "+", disabled=app.grid_size >= 32)
            app._button(buttons["grid_field"], app.grid_text,
                         primary=app.editing_grid)
            app.text(f"x {app.grid_size}  /  {app.grid_size ** 2:,} pieces", (254, 160), 17)
            app._button(buttons["leaderboard"], "Leaderboard")
            app._button(buttons["begin"], "Start puzzle", True)
            for picture in app.pictures:
                key = f"image:{picture.id}"
                if key not in buttons:
                    continue
                rect = buttons[key]
                pygame.draw.rect(app.screen, "white", rect, border_radius=6)
                app.screen.blit(app.thumbnails[picture.id], (rect.x + 10, rect.y + 10))
                app.text(app.fit_text(picture.title, 180, 14), (rect.x + 10, rect.y + 195), 14)
                if picture.id == app.picture.id or rect.collidepoint(app.pointer):
                    pygame.draw.rect(app.screen, "#147d6b", rect, 3, border_radius=6)
            self._pages(buttons, "gallery", app.gallery_page, len(app.pictures), self.gallery_capacity())
        else:
            app._button(buttons["back_results"], "Back")
            app.text("Leaderboard", (158, 39), 24)
            app.text(f"{app.fit_text(app.picture.title, 500)}  /  {app.grid_size} x {app.grid_size}",
                     (48, 112), 20)
            best = app.best
            if best:
                app.text(f"Your best: {format_duration(best['elapsed_ms'] / 1000)} / {best['moves']} moves",
                         (48, 149), 17, "#147d6b")
            for label, x in (("Rank", 48), ("Player", 112), ("Time", width - 420),
                             ("Moves", width - 300), ("Completed", width - 190)):
                app.text(label, (x, 202), 14, "#606f77")
            if not app.scores:
                app.text("No completed puzzles yet", (48, 250), 20)
            for index, result in enumerate(app.scores[app.scores_page * 9:][:9]):
                y = 237 + index * 43
                pygame.draw.line(app.screen, "#dce4e8", (48, y + 34), (width - 48, y + 34))
                app.text(str(result['rank']), (48, y), 17)
                app.text(app.fit_text(result['name'], width - 565), (112, y), 17)
                app.text(format_duration(result['elapsed_ms'] / 1000), (width - 420, y), 17)
                app.text(str(result['moves']), (width - 300, y), 17)
                app.text(result['completed_at'][:10], (width - 190, y), 17)
            self._pages(buttons, "scores", app.scores_page, len(app.scores), 9)

    def _pages(self, buttons, prefix, page, total, capacity):
        app = self.app
        pages = max(1, (total + capacity - 1) // capacity)
        app._button(buttons[prefix + "_prev"], "<", disabled=page == 0)
        app._button(buttons[prefix + "_next"], ">", disabled=page >= pages - 1)
        app.text(f"{page + 1} / {pages}",
                 (buttons[prefix + "_prev"].right + 18, buttons[prefix + "_prev"].y + 10), 14)
