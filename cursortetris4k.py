    import pygame
    import sys
    import random
    import numpy as np

    # ================================================
    # AC'S TETRIS - GAME BOY EDITION (Python 3.14 Compatible)
    # 60 FPS • Authentic Game Boy speed • EXACT ORIGINAL KOROBEINIKI 
    # EVERYTHING IN ONE FILE • NO EXTERNAL FILES (files = OFF)
    # ================================================

    # Initialize pygame and mixer for the synthesized music
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    # Screen Dimensions
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    BLOCK_SIZE = 24
    COLS = 10
    ROWS = 20
    PLAYFIELD_X = 240
    PLAYFIELD_Y = 60

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("AC'S TETRIS • Game Boy Edition")
    clock = pygame.time.Clock()

    # Game Boy authentic colors (Greyscale/Green palette)
    COLORS = {
        0: (15, 56, 15),
        1: (0, 240, 240),   # I (Cyan mapped to GB colors in drawing, but these are logical base colors)
        2: (240, 240, 0),   # O (Yellow)
        3: (160, 0, 240),   # T (Purple)
        4: (0, 240, 0),     # S (Green)
        5: (240, 0, 0),     # Z (Red)
        6: (0, 0, 240),     # J (Blue)
        7: (240, 160, 0)    # L (Orange)
    }

    # Tetromino shapes (exact rotations)
    PIECES = [
        [[1,1,1,1]], [[1],[1],[1],[1]],                                          # I
        [[2,2],[2,2]],                                                           # O
        [[0,3,0],[3,3,3]], [[3,0],[3,3],[3,0]], [[3,3,3],[0,3,0]], [[0,3],[3,3],[0,3]],  # T
        [[0,4,4],[4,4,0]], [[4,0],[4,4],[0,4]],                                  # S
        [[5,5,0],[0,5,5]], [[0,5],[5,5],[5,0]],                                  # Z
        [[6,0,0],[6,6,6]], [[6,6],[6,0],[6,0]], [[6,6,6],[0,0,6]], [[0,6],[0,6],[6,6]],  # J
        [[0,0,7],[7,7,7]], [[7,0],[7,0],[7,7]], [[7,7,7],[7,0,0]], [[7,7],[0,7],[0,7]]   # L
    ]

    # Game Boy level drop speeds (frames per drop at 60 FPS)
    GB_SPEED = [48, 43, 38, 33, 28, 23, 18, 13, 8, 6, 5, 4, 3, 2, 1]

    # KOROBEINIKI — traditional Russian folk song ("Коробейники"),
    # the Tetris Type-A theme. Transcribed in E minor, procedurally synthesized.
    # Note values at 60 FPS: eighth = 12, quarter = 24, dotted-q = 36, half = 48
    # Pitches: A4=440, B4=494, C5=523, D5=587, E5=659, F5=698, G5=784, A5=880
    _E = 12
    _Q = 24
    _DQ = 36
    _H = 48
    MUSIC = [
        # --- A section (first half) ---
        (659, _Q),  (494, _E),  (523, _E),  (587, _Q),  (523, _E),  (494, _E),
        (440, _Q),  (440, _E),  (523, _E),  (659, _Q),  (587, _E),  (523, _E),
        (494, _DQ), (523, _E),  (587, _Q),  (659, _Q),
        (523, _Q),  (440, _Q),  (440, _H),
        # --- B section (second half) ---
        (587, _Q),  (698, _E),  (880, _Q),  (784, _E),  (698, _E),
        (659, _DQ), (523, _E),  (659, _Q),  (587, _E),  (523, _E),
        (494, _Q),  (494, _E),  (523, _E),  (587, _Q),  (659, _Q),
        (523, _Q),  (440, _Q),  (440, _H),
        # --- repeat A section one more time so the loop feels like the Game Boy ---
        (659, _Q),  (494, _E),  (523, _E),  (587, _Q),  (523, _E),  (494, _E),
        (440, _Q),  (440, _E),  (523, _E),  (659, _Q),  (587, _E),  (523, _E),
        (494, _DQ), (523, _E),  (587, _Q),  (659, _Q),
        (523, _Q),  (440, _Q),  (440, _H),
    ]

    class Tetris:
        def __init__(self):
            self.font_big = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 28)
            self.font_tiny = pygame.font.Font(None, 22)
            self.state = "menu"
            self.music_index = 0
            self.music_timer = 0
            self._note_cache = {}
            pygame.mixer.set_num_channels(8)

            # Main-menu model
            self.menu_screen = "main"   # main | howto | sound | credits | about
            self.menu_items = [
                "PLAY GAME",
                "HOW TO PLAY",
                "SOUND OPTIONS",
                "CREDITS",
                "ABOUT",
                "EXIT",
            ]
            self.menu_index = 0
            self.sound_items = ["MUSIC", "SFX", "VOLUME"]
            self.sound_index = 0
            self.music_enabled = True
            self.sfx_enabled = True
            self.master_volume = 0.6
            self.tick = 0

            self.reset_game()

        def reset_game(self):
            self.board = [[0] * COLS for _ in range(ROWS)]
            self.score = 0
            self.lines_cleared = 0
            self.level = 0
            # Fix: drop interval is exactly the frames from GB_SPEED
            self.drop_interval = GB_SPEED[0] 
            self.drop_counter = 0
            self.next_piece_idx = random.randint(0, len(PIECES)-1)
            self.spawn_piece()

        def spawn_piece(self):
            idx = self.next_piece_idx
            self.current_piece = [row[:] for row in PIECES[idx]]
            self.piece_x = COLS // 2 - len(self.current_piece[0]) // 2
            self.piece_y = 0
            self.next_piece_idx = random.randint(0, len(PIECES)-1)
            if self.collides():
                self.state = "gameover"

        def collides(self):
            for y, row in enumerate(self.current_piece):
                for x, cell in enumerate(row):
                    if cell == 0: continue
                    nx = self.piece_x + x
                    ny = self.piece_y + y
                    if nx < 0 or nx >= COLS or ny >= ROWS: return True
                    if ny >= 0 and self.board[ny][nx] != 0: return True
            return False

        def rotate(self):
            original = self.current_piece
            self.current_piece = [list(reversed(col)) for col in zip(*original)]
            if self.collides():
                self.current_piece = original

        def lock_piece(self):
            for y, row in enumerate(self.current_piece):
                for x, cell in enumerate(row):
                    if cell:
                        ny = self.piece_y + y
                        if ny >= 0:
                            self.board[ny][self.piece_x + x] = cell
            self.clear_lines()
            self.spawn_piece()

        def clear_lines(self):
            new_board = [row for row in self.board if 0 in row]
            cleared = ROWS - len(new_board)
            if cleared:
                self.board = [[0]*COLS for _ in range(cleared)] + new_board
                points = [0, 40, 100, 300, 1200]
                self.score += points[cleared] * (self.level + 1)
                self.lines_cleared += cleared
                self.level = self.lines_cleared // 10
                idx = min(self.level, len(GB_SPEED)-1)
                self.drop_interval = GB_SPEED[idx]

        def _build_note(self, freq, frames):
            """Game Boy-style square-wave 'duh' with a short attack/release so it
            sounds like a distinct note instead of a click or continuous tone."""
            sr = 44100
            note_frames = max(1, frames - 1)
            n = max(1, int(sr * note_frames / 60.0))
            t = np.arange(n, dtype=np.float32) / sr
            wave = np.where(np.sin(2 * np.pi * freq * t) >= 0.0, 1.0, -1.0) * 0.22
            env = np.ones(n, dtype=np.float32)
            a = min(n, int(sr * 0.008))
            r = min(n, int(sr * 0.030))
            if a:
                env[:a] = np.linspace(0.0, 1.0, a, dtype=np.float32)
            if r:
                env[-r:] = np.linspace(1.0, 0.0, r, dtype=np.float32)
            audio = (wave * env * 32767.0).astype(np.int16)
            stereo = np.column_stack((audio, audio))
            return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))

        def play_note(self, freq, frames):
            if not self.music_enabled:
                return
            key = (freq, frames)
            snd = self._note_cache.get(key)
            if snd is None:
                snd = self._build_note(freq, frames)
                self._note_cache[key] = snd
            snd.set_volume(max(0.0, min(1.0, self.master_volume)))
            ch = pygame.mixer.find_channel(True)
            if ch is not None:
                ch.play(snd)
            else:
                snd.play()

        def update_music(self):
            if self.state != "playing":
                return
            if self.music_timer <= 0:
                freq, dur = MUSIC[self.music_index]
                self.play_note(freq, dur)
                self.music_timer = dur
                self.music_index = (self.music_index + 1) % len(MUSIC)
            else:
                self.music_timer -= 1

        # ---------------- Main Menu: input ----------------

        def _handle_menu_key(self, key):
            screen_name = self.menu_screen

            if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                if screen_name != "main":
                    self.menu_screen = "main"
                    self.menu_index = 0
                return

            if screen_name == "main":
                if key == pygame.K_UP:
                    self.menu_index = (self.menu_index - 1) % len(self.menu_items)
                elif key == pygame.K_DOWN:
                    self.menu_index = (self.menu_index + 1) % len(self.menu_items)
                elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self._activate_main_menu_item()
                return

            if screen_name == "sound":
                if key == pygame.K_UP:
                    self.sound_index = (self.sound_index - 1) % len(self.sound_items)
                elif key == pygame.K_DOWN:
                    self.sound_index = (self.sound_index + 1) % len(self.sound_items)
                elif key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self._adjust_sound_option(+1 if key == pygame.K_RIGHT else -1)
                elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    sel = self.sound_items[self.sound_index]
                    if sel == "MUSIC":
                        self.music_enabled = not self.music_enabled
                        if not self.music_enabled:
                            pygame.mixer.stop()
                    elif sel == "SFX":
                        self.sfx_enabled = not self.sfx_enabled
                    else:
                        self.menu_screen = "main"
                        self.menu_index = 0
                return

            # howto | credits | about
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.menu_screen = "main"
                self.menu_index = 0

        def _activate_main_menu_item(self):
            item = self.menu_items[self.menu_index]
            if item == "PLAY GAME":
                self.reset_game()
                self.state = "playing"
                self.music_index = 0
                self.music_timer = 0
                self.menu_screen = "main"
                self.menu_index = 0
                pygame.mixer.stop()
            elif item == "HOW TO PLAY":
                self.menu_screen = "howto"
            elif item == "SOUND OPTIONS":
                self.menu_screen = "sound"
                self.sound_index = 0
            elif item == "CREDITS":
                self.menu_screen = "credits"
            elif item == "ABOUT":
                self.menu_screen = "about"
            elif item == "EXIT":
                pygame.quit()
                sys.exit()

        def _adjust_sound_option(self, direction):
            sel = self.sound_items[self.sound_index]
            if sel == "MUSIC":
                self.music_enabled = not self.music_enabled
                if not self.music_enabled:
                    pygame.mixer.stop()
            elif sel == "SFX":
                self.sfx_enabled = not self.sfx_enabled
            elif sel == "VOLUME":
                self.master_volume = max(0.0, min(1.0, self.master_volume + 0.05 * direction))

        # ---------------- Main Menu: render ----------------

        def _draw_menu_background(self):
            screen.fill((15, 56, 15))
            # faint procedural falling tetromino silhouettes
            cols = SCREEN_WIDTH // BLOCK_SIZE + 2
            for i in range(cols):
                seed = (i * 73) % len(PIECES)
                piece = PIECES[seed]
                px = i * BLOCK_SIZE
                py = ((self.tick // 2 + i * 37) % (SCREEN_HEIGHT + 120)) - 80
                for y, row in enumerate(piece):
                    for x, cell in enumerate(row):
                        if cell:
                            pygame.draw.rect(
                                screen,
                                (30, 80, 30),
                                (px + x * BLOCK_SIZE // 2,
                                py + y * BLOCK_SIZE // 2,
                                BLOCK_SIZE // 2 - 1,
                                BLOCK_SIZE // 2 - 1),
                            )

        def _draw_title(self):
            t1 = self.font_big.render("AC'S TETRIS", True, (139, 172, 15))
            t2 = self.font_small.render("PY PORT", True, (200, 230, 120))
            sub = self.font_tiny.render("files = off", True, (120, 160, 120))
            screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, 70))
            screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, 120))
            screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 152))

        def _draw_footer(self, hint):
            f = self.font_tiny.render(hint, True, (120, 160, 120))
            screen.blit(f, (SCREEN_WIDTH // 2 - f.get_width() // 2, SCREEN_HEIGHT - 32))

        def _draw_main_menu(self):
            start_y = 210
            spacing = 36
            for i, item in enumerate(self.menu_items):
                selected = (i == self.menu_index)
                color = (255, 255, 100) if selected else (139, 172, 15)
                label = f"> {item}" if selected else f"  {item}"
                surf = self.font_small.render(label, True, color)
                screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2,
                                start_y + i * spacing))
            self._draw_footer("[UP/DOWN] move   [ENTER] select   [ESC] back")

        def _draw_howto(self):
            header = self.font_big.render("HOW TO PLAY", True, (255, 255, 100))
            screen.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, 180))
            lines = [
                "LEFT / RIGHT  -  move piece",
                "UP            -  rotate",
                "DOWN          -  soft drop (+1 pt)",
                "SPACE         -  hard drop (+10 pts)",
                "P             -  pause / resume",
                "ESC           -  return to menu",
            ]
            y = 250
            for ln in lines:
                s = self.font_small.render(ln, True, (139, 172, 15))
                screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, y))
                y += 32
            self._draw_footer("[ENTER] or [ESC] back")

        def _draw_sound_options(self):
            header = self.font_big.render("SOUND OPTIONS", True, (255, 255, 100))
            screen.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, 170))
            rows = []
            rows.append(("MUSIC",  "ON" if self.music_enabled else "OFF"))
            rows.append(("SFX",    "ON" if self.sfx_enabled else "OFF"))
            bars_total = 20
            filled = int(round(self.master_volume * bars_total))
            bar = "[" + ("#" * filled) + ("-" * (bars_total - filled)) + "]"
            rows.append(("VOLUME", f"{bar} {int(round(self.master_volume * 100)):3d}%"))

            y = 250
            for i, (label, value) in enumerate(rows):
                selected = (i == self.sound_index)
                color = (255, 255, 100) if selected else (139, 172, 15)
                arrow_l = "<" if selected else " "
                arrow_r = ">" if selected else " "
                text = f"{label:<7}: {arrow_l} {value} {arrow_r}"
                s = self.font_small.render(text, True, color)
                screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, y))
                y += 40
            self._draw_footer("[UP/DOWN] item   [LEFT/RIGHT] change   [ESC] back")

        def _draw_credits(self):
            header = self.font_big.render("CREDITS", True, (255, 255, 100))
            screen.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, 180))
            lines = [
                "AC'S TETRIS PY PORT",
                "",
                "Engine  :  Python 3.14 + Pygame-CE",
                "Music   :  Korobeiniki (Russian folk)",
                "Synth   :  NumPy square-wave, in-memory",
                "Policy  :  files = off",
            ]
            y = 260
            for ln in lines:
                if ln:
                    s = self.font_small.render(ln, True, (139, 172, 15))
                    screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, y))
                y += 30
            self._draw_footer("[ENTER] or [ESC] back")

        def _draw_about(self):
            header = self.font_big.render("ABOUT", True, (255, 255, 100))
            screen.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, 170))
            paragraph = (
                "AC's Tetris PY Port is a single-file Game Boy-flavored "
                "Tetris clone written for Python 3.14 and Pygame-CE. "
                "Every graphic is drawn with shapes and every note of the "
                "Korobeiniki theme is synthesized on the fly with NumPy. "
                "No external assets, no saves, no config files. "
                "files = off."
            )
            # naive word wrap at ~46 chars
            words = paragraph.split()
            lines, cur = [], ""
            for w in words:
                if len(cur) + len(w) + 1 > 46:
                    lines.append(cur.strip())
                    cur = w + " "
                else:
                    cur += w + " "
            if cur.strip():
                lines.append(cur.strip())
            y = 240
            for ln in lines:
                s = self.font_small.render(ln, True, (139, 172, 15))
                screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, y))
                y += 30
            self._draw_footer("[ENTER] or [ESC] back")

        def _draw_menu(self):
            self._draw_menu_background()
            self._draw_title()
            if self.menu_screen == "main":
                self._draw_main_menu()
            elif self.menu_screen == "howto":
                self._draw_howto()
            elif self.menu_screen == "sound":
                self._draw_sound_options()
            elif self.menu_screen == "credits":
                self._draw_credits()
            elif self.menu_screen == "about":
                self._draw_about()

        def draw(self):
            if self.state == "menu":
                self._draw_menu()
                pygame.display.flip()
                return

            screen.fill((15, 56, 15))

            # Draw the Playfield background and border
            pygame.draw.rect(screen, (139, 172, 15),
                            (PLAYFIELD_X-16, PLAYFIELD_Y-16, COLS*BLOCK_SIZE+32, ROWS*BLOCK_SIZE+32), border_radius=4)
            pygame.draw.rect(screen, (48, 98, 48),
                            (PLAYFIELD_X-8, PLAYFIELD_Y-8, COLS*BLOCK_SIZE+16, ROWS*BLOCK_SIZE+16))

            # Draw locked blocks
            for y in range(ROWS):
                for x in range(COLS):
                    if self.board[y][x]:
                        color = COLORS[self.board[y][x]]
                        rect = pygame.Rect(PLAYFIELD_X + x*BLOCK_SIZE, PLAYFIELD_Y + y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                        pygame.draw.rect(screen, color, rect)
                        pygame.draw.rect(screen, (255,255,255,50), rect.inflate(-6,-6))

            # Draw active dropping piece
            if self.current_piece and self.state in ["playing", "paused"]:
                for y, row in enumerate(self.current_piece):
                    for x, cell in enumerate(row):
                        if cell:
                            color = COLORS[cell]
                            rect = pygame.Rect(PLAYFIELD_X + (self.piece_x + x)*BLOCK_SIZE,
                                            PLAYFIELD_Y + (self.piece_y + y)*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                            pygame.draw.rect(screen, color, rect)
                            pygame.draw.rect(screen, (255,255,255,50), rect.inflate(-6,-6))

            # Draw Next piece preview
            next_p = PIECES[self.next_piece_idx]
            nx, ny = 580, 120
            pygame.draw.rect(screen, (48, 98, 48), (nx-10, ny-10, 140, 140))
            for y, row in enumerate(next_p):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(screen, COLORS[cell],
                                        (nx + x*BLOCK_SIZE//2, ny + y*BLOCK_SIZE//2, BLOCK_SIZE//2, BLOCK_SIZE//2))

            # Draw UI text
            title = self.font_small.render("AC'S TETRIS", True, (139, 172, 15))
            screen.blit(title, (45, 45))
            screen.blit(self.font_small.render(f"SCORE {self.score:06d}", True, (139, 172, 15)), (45, 180))
            screen.blit(self.font_small.render(f"LEVEL {self.level:02d}", True, (139, 172, 15)), (45, 260))
            screen.blit(self.font_small.render(f"LINES {self.lines_cleared:03d}", True, (139, 172, 15)), (45, 340))

            if self.state == "gameover":
                t = self.font_big.render("GAME OVER", True, (255, 50, 50))
                screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 200))
                s = self.font_small.render(f"FINAL SCORE {self.score:06d}", True, (139, 172, 15))
                screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 280))
                r = self.font_small.render("PRESS SPACE TO RESTART", True, (255, 255, 100))
                screen.blit(r, (SCREEN_WIDTH//2 - r.get_width()//2, 340))

            if self.state == "paused":
                t = self.font_big.render("PAUSED", True, (255, 255, 100))
                screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 250))

            pygame.display.flip()

        def run(self):
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    if event.type == pygame.KEYDOWN:
                        if self.state == "menu":
                            self._handle_menu_key(event.key)

                        elif self.state in ["playing", "paused"]:
                            if event.key == pygame.K_ESCAPE:
                                self.state = "menu"
                                self.menu_screen = "main"
                                self.menu_index = 0
                                pygame.mixer.stop()
                                continue
                            if event.key == pygame.K_p:
                                if self.state == "paused":
                                    self.state = "playing"
                                    pygame.mixer.unpause()
                                else:
                                    self.state = "paused"
                                    pygame.mixer.pause()
                                continue
                            
                            if self.state == "playing":
                                if event.key == pygame.K_LEFT:
                                    self.piece_x -= 1
                                    if self.collides(): self.piece_x += 1
                                elif event.key == pygame.K_RIGHT:
                                    self.piece_x += 1
                                    if self.collides(): self.piece_x -= 1
                                elif event.key == pygame.K_DOWN:
                                    self.piece_y += 1
                                    if self.collides():
                                        self.piece_y -= 1
                                        self.lock_piece()
                                    else:
                                        self.score += 1
                                elif event.key == pygame.K_UP:
                                    self.rotate()
                                elif event.key == pygame.K_SPACE:
                                    while not self.collides():
                                        self.piece_y += 1
                                    self.piece_y -= 1
                                    self.lock_piece()
                                    self.score += 10

                        elif self.state == "gameover" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.state = "menu"
                            self.menu_screen = "main"
                            self.menu_index = 0
                            pygame.mixer.stop()

                self.tick += 1

                # Game Logic tick
                if self.state == "playing":
                    self.drop_counter += 1
                    if self.drop_counter >= self.drop_interval:
                        self.piece_y += 1
                        if self.collides():
                            self.piece_y -= 1
                            self.lock_piece()
                        self.drop_counter = 0

                    # Tick custom synth audio
                    self.update_music()

                self.draw()
                clock.tick(60)

    if __name__ == "__main__":
        print("AC'S TETRIS - Game Boy Edition starting...")
        print("60 FPS - Russian folk song KOROBEINIKI (synthesized in-memory) - files = OFF")
        Tetris().run()
