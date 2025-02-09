import pygame
import random
import sys
import os
import math
import json
import glob
import tkinter as tk
from tkinter import filedialog

pygame.init()
pygame.mixer.set_num_channels(32)
pygame.mixer.init()

# -------------------------- Global Music Playlist Variables --------------------------
MUSIC_END_EVENT = pygame.USEREVENT + 1
custom_music_playlist = []  # Sorted list of music files (alphabetical order)
current_track_index = 0

# -------------------------- Helper Functions --------------------------
def load_sound(file_path):
    """Attempt to load a sound file; if missing, print a warning and return None."""
    if os.path.exists(file_path):
        try:
            return pygame.mixer.Sound(file_path)
        except Exception as e:
            print(f"Error loading sound {file_path}: {e}")
            return None
    else:
        print(f"Sound file not found: {file_path}")
        return None

def get_music_files(directory):
    """Recursively search the given directory for files with allowed music extensions.
    Returns a sorted list (alphabetically)."""
    allowed_ext = ('.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a')
    music_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(allowed_ext):
                music_files.append(os.path.join(root, file))
    return sorted(music_files)

def update_custom_music_playlist(settings):
    global custom_music_playlist, current_track_index
    music_dir = settings.get('music_directory', "")
    if music_dir and os.path.isdir(music_dir):
        custom_music_playlist = get_music_files(music_dir)
        current_track_index = 0
    else:
        custom_music_playlist = []

# -------------------------- Constants --------------------------
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 930
BLOCK_SIZE = 30
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE
SUBWINDOW_WIDTH = 369
DOUBLE_CLICK_TIME = 300

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
COLORS = [
    (0, 255, 255), (255, 165, 0), (0, 0, 255),
    (255, 0, 0), (0, 255, 0), (255, 255, 0), (128, 0, 128)
]

# -------------------------- Audio Files --------------------------
AUDIO_FOLDER = "Audio"  # Must be in the same folder as this script
BACKGROUND_MUSIC_PATH = os.path.join(AUDIO_FOLDER, "Background.ogg")
LINE_CLEAR_SOUND_PATH = os.path.join(AUDIO_FOLDER, "Lineclear.ogg")
MULTIPLE_LINE_CLEAR_SOUND_PATH = os.path.join(AUDIO_FOLDER, "MultipleLineclear.ogg")
GAME_OVER_SOUND_PATH = os.path.join(AUDIO_FOLDER, "GAMEOVER.ogg")
HEARTBEAT_SOUND_PATH = os.path.join(AUDIO_FOLDER, "heartbeat_grid_almost_full.ogg")

line_clear_sound = load_sound(LINE_CLEAR_SOUND_PATH)
multiple_line_clear_sound = load_sound(MULTIPLE_LINE_CLEAR_SOUND_PATH)
game_over_sound = load_sound(GAME_OVER_SOUND_PATH)
heartbeat_sound = load_sound(HEARTBEAT_SOUND_PATH)
heartbeat_playing = False

# -------------------------- Tetromino Shapes --------------------------
SHAPES = [
    [[1, 1, 1], [0, 1, 0]],
    [[1, 1], [1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 1, 1, 1]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [1, 1, 1]]
]

# -------------------------- Fonts --------------------------
TETRIS_FONT_PATH = "assets/tetris-blocks.TTF"
try:
    tetris_font_large = pygame.font.Font(TETRIS_FONT_PATH, 40)
    tetris_font_medium = pygame.font.Font(TETRIS_FONT_PATH, 27)
    tetris_font_small = pygame.font.Font(TETRIS_FONT_PATH, 18)
except FileNotFoundError:
    print(f"Font file not found: {TETRIS_FONT_PATH}")
    sys.exit()

screen = pygame.display.set_mode((SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("TetraFusion 1.8.2")
clock = pygame.time.Clock()

subwindow_visible = True
last_click_time = 0

# Global variables for in-game buttons and sound bar (subwindow coordinates)
restart_button_rect = None
menu_button_rect = None
skip_button_rect = None  # Only if custom music is enabled
sound_bar_rect = None
game_command = None  # "restart" or "menu" when a button is clicked

# -------------------------- Settings System --------------------------
def load_settings(filename="settings.json"):
    default_settings = {
        'controls': {
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'down': pygame.K_DOWN,
            'rotate': pygame.K_UP,
            'pause': pygame.K_p,
            'hard_drop': pygame.K_SPACE
        },
        'difficulty': 'normal',
        'flame_trails': True,
        'grid_color': [200, 200, 200],
        'grid_opacity': 128,    # 0 = black grid lines, 192 = full grid color
        'grid_lines': True,     # Toggle grid lines on/off
        'ghost_piece': True,    # Toggle ghost (drop shadow) effect on/off
        'music_enabled': True,
        'use_custom_music': False,
        'music_directory': ""
    }
    try:
        with open(filename, "r") as file:
            saved_settings = json.load(file)
            if 'controls' in saved_settings:
                for key, value in default_settings['controls'].items():
                    if key in saved_settings['controls']:
                        val = saved_settings['controls'][key]
                        if isinstance(val, str):
                            saved_settings['controls'][key] = getattr(pygame, f'K_{val.lower()}', default_settings['controls'][key])
                        elif isinstance(val, int):
                            saved_settings['controls'][key] = val
                    else:
                        saved_settings['controls'][key] = default_settings['controls'][key]
            else:
                saved_settings['controls'] = default_settings['controls']
            for key, default_value in default_settings.items():
                if key not in saved_settings:
                    saved_settings[key] = default_value
            return saved_settings
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return default_settings

def save_settings(settings, filename="settings.json"):
    controls_dict = {control: pygame.key.name(key).upper() for control, key in settings['controls'].items()}
    settings_to_save = {
        'controls': controls_dict,
        'difficulty': settings['difficulty'],
        'flame_trails': settings['flame_trails'],
        'grid_color': settings['grid_color'],
        'grid_opacity': settings['grid_opacity'],
        'grid_lines': settings.get('grid_lines', True),
        'ghost_piece': settings.get('ghost_piece', True),
        'music_enabled': settings.get('music_enabled', True),
        'use_custom_music': settings.get('use_custom_music', False),
        'music_directory': settings.get('music_directory', "")
    }
    try:
        with open(filename, "w") as file:
            json.dump(settings_to_save, file, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

# -------------------------- Particle Effects --------------------------
class DustParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = random.uniform(math.pi, math.pi*2)
        self.speed = random.uniform(1.0, 3.0)
        self.age = 0
        self.max_age = random.randint(20, 40)
        self.size = random.randint(8, 15)
        self.color = (random.randint(100, 150), random.randint(50, 100), 0)
        self.alpha = 255

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.speed *= 0.92
        self.age += 1
        self.alpha = max(0, 255 - (self.age / self.max_age) * 255)
        self.size = max(2, self.size * 0.95)

    def draw(self, screen):
        if self.age >= self.max_age:
            return
        surface = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(surface, (*self.color, int(self.alpha)), (int(self.size), int(self.size)), int(self.size))
        screen.blit(surface, (int(self.x - self.size), int(self.y - self.size)))

class TrailParticle:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        if direction == "left":
            self.angle = random.uniform(math.pi/2, 3*math.pi/2)
        elif direction == "right":
            self.angle = random.uniform(-math.pi/2, math.pi/2)
        elif direction == "down":
            self.angle = random.uniform(math.pi/2 - math.pi/8, math.pi/2 + math.pi/8)
        else:
            self.angle = random.uniform(-math.pi, math.pi)
        self.speed = random.uniform(1.5, 3.0)
        self.age = 0
        self.max_age = random.randint(40, 60)
        self.size = random.randint(12, 20)
        self.colors = [
            (255, 240, 150),
            (255, 180, 80),
            (255, 90, 40)
        ]
        self.turbulence = random.uniform(0.5, 1.5)
        self.gravity = -0.1
        self.drift_x = random.uniform(-0.5, 0.5)
        self.drift_y = random.uniform(-0.5, 0.5)

    def update(self, wind_force=(0,0), screen=None):
        self.x += math.cos(self.angle) * self.speed + self.drift_x + wind_force[0]
        self.y += math.sin(self.angle) * self.speed + self.drift_y + wind_force[1]
        if screen:
            self.x = max(self.size, min(screen.get_width()-self.size, self.x))
            self.y = max(self.size, min(screen.get_height()-self.size, self.y))
        self.speed *= 0.92
        self.drift_x *= 0.7
        self.drift_y *= 0.7
        self.y += self.gravity
        self.age += 1
        self.size = max(5, self.size * 0.95)

    def draw(self, screen):
        if self.age >= self.max_age:
            return
        if not (0 <= self.x <= screen.get_width() and 0 <= self.y <= screen.get_height()):
            return
        color_progress = self.age / self.max_age
        if color_progress < 0.33:
            color = self.colors[0]
        elif color_progress < 0.66:
            color = self.colors[1]
        else:
            color = self.colors[2]
        alpha = int(255 * (1 - color_progress**1.5))
        radius = int(self.size)
        blended_color = (color[0], color[1], color[2], alpha)
        particle_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, blended_color, (radius, radius), radius)
        screen.blit(particle_surface, (int(self.x - radius), int(self.y - radius)))

class Explosion:
    def __init__(self, x, y, color, particle_count=30, max_speed=8, duration=45):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []
        self.lifetime = duration
        for _ in range(particle_count):
            self.particles.append([
                x + random.uniform(-15,15),
                y + random.uniform(-15,15),
                random.uniform(-max_speed, max_speed),
                random.uniform(-max_speed, max_speed),
                random.uniform(0.1, 0.3),
                random.randint(200,255)
            ])

    def update(self):
        self.lifetime -= 1
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[4]
            p[5] = max(0, p[5]-4)

    def draw(self, surface, offset=(0,0)):
        for p in self.particles:
            if p[5] > 0:
                size = 4 + int(p[5]/50)
                pygame.draw.circle(surface, (*self.color, p[5]),
                                   (int(p[0]+offset[0]), int(p[1]+offset[1])), size)

# -------------------------- Tetromino Bag --------------------------
class TetrominoBag:
    def __init__(self, shapes):
        self.shapes = shapes
        self.bag = []
        self.refill_bag()

    def refill_bag(self):
        self.bag = self.shapes[:]
        random.shuffle(self.bag)

    def get_next_tetromino(self):
        if not self.bag:
            self.refill_bag()
        return self.bag.pop()

# -------------------------- Drawing Functions --------------------------
def draw_3d_block(screen, color, x, y, block_size):
    top_color = tuple(min(255, c+40) for c in color)
    side_color = tuple(max(0, c-40) for c in color)
    front_color = color
    front_rect = pygame.Rect(x+5, y+5, block_size-10, block_size-10)
    top_polygon = [(x, y), (x+block_size, y), (x+block_size-5, y+5), (x+5, y+5)]
    pygame.draw.polygon(screen, top_color, top_polygon)
    left_polygon = [(x,y), (x+5, y+5), (x+5, y+block_size+5), (x, y+block_size)]
    pygame.draw.polygon(screen, side_color, left_polygon)
    right_polygon = [(x+block_size, y), (x+block_size-5, y+5), (x+block_size-5, y+block_size+5), (x+block_size, y+block_size)]
    pygame.draw.polygon(screen, side_color, right_polygon)
    pygame.draw.rect(screen, front_color, front_rect)
    outline_color = (0, 0, 0)
    pygame.draw.rect(screen, outline_color, front_rect, 2)
    pygame.draw.polygon(screen, outline_color, top_polygon, 2)
    pygame.draw.polygon(screen, outline_color, left_polygon, 2)
    pygame.draw.polygon(screen, outline_color, right_polygon, 2)

def draw_3d_grid(grid_surface, grid_color, grid_opacity):
    if not settings.get('grid_lines', True):
        grid_surface.fill((0,0,0,0))
        return
    grid_surface.fill((0, 0, 0, 0))
    factor = grid_opacity / 192.0
    line_color = tuple(int(grid_color[i]*factor) for i in range(3))
    for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
        pygame.draw.line(grid_surface, line_color, (x,0), (x,SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
        pygame.draw.line(grid_surface, line_color, (0,y), (SCREEN_WIDTH,y), 1)

def load_high_score(filename="high_score.txt"):
    try:
        if os.path.exists(filename):
            with open(filename, "r") as file:
                content = file.read().strip()
                if content:
                    parts = content.split(maxsplit=1)
                    return int(parts[0]), parts[1] if len(parts)>1 else "---"
        return 0, "---"
    except Exception as e:
        print(f"Error loading high score: {e}")
        return 0, "---"

def save_high_score(high_score, high_score_name, filename="high_score.txt"):
    try:
        with open(filename, "w") as file:
            file.write(f"{high_score} {high_score_name}")
    except Exception as e:
        print(f"Error saving high score: {e}")

high_score, high_score_name = load_high_score()

def create_grid():
    return [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def is_danger_zone_active(grid):
    for y in range(4):
        if any(grid[y]):
            return True
    return False

def valid_position(tetromino, offset, grid):
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = offset[0] + cx
                y = offset[1] + cy
                if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT or (y>=0 and grid[y][x]):
                    return False
    return True

def rotate_tetromino_with_kick(tetromino, offset, grid):
    rotated = [list(row) for row in zip(*tetromino[::-1])]
    kicks = [(0,0), (-1,0), (1,0), (0,-1), (-2,0), (2,0)]
    for dx, dy in kicks:
        new_offset = [offset[0]+dx, offset[1]+dy]
        if valid_position(rotated, new_offset, grid):
            return rotated, new_offset
    return tetromino, offset

def clear_lines(grid):
    full_lines = [y for y in range(GRID_HEIGHT) if all(grid[y])]
    if full_lines:
        if len(full_lines)==4 and multiple_line_clear_sound:
            multiple_line_clear_sound.play()
        elif line_clear_sound:
            line_clear_sound.play()
    for y in full_lines:
        del grid[y]
        grid.insert(0, [0 for _ in range(GRID_WIDTH)])
    return grid, len(full_lines)

def update_score(score, lines_cleared):
    return score + lines_cleared * 100

def check_game_over(grid):
    return any(cell != 0 for cell in grid[0])

def draw_subwindow(score, next_tetromino, level, pieces_dropped, lines_cleared_total, is_tetris=False, tetris_last_flash=0, tetris_flash_time=2000):
    global restart_button_rect, menu_button_rect, skip_button_rect, sound_bar_rect
    subwindow = pygame.Surface((SUBWINDOW_WIDTH, SCREEN_HEIGHT))
    subwindow.fill(BLACK)
    # Game info:
    score_text = tetris_font_small.render(f"Score: {score}", True, WHITE)
    high_score_text = tetris_font_small.render(f"High Score: {high_score} ({high_score_name})", True, WHITE)
    level_text = tetris_font_small.render(f"Level: {level}", True, WHITE)
    pieces_text = tetris_font_small.render(f"Pieces Dropped: {pieces_dropped}", True, WHITE)
    lines_text = tetris_font_small.render(f"Lines Cleared: {lines_cleared_total}", True, WHITE)
    subwindow.blit(score_text, (10, 10))
    subwindow.blit(high_score_text, (10, 40))
    subwindow.blit(level_text, (10, 70))
    subwindow.blit(pieces_text, (10, 100))
    subwindow.blit(lines_text, (10, 130))
    # Next tetromino:
    next_text = tetris_font_small.render("Next:", True, WHITE)
    subwindow.blit(next_text, (10, 160))
    if next_tetromino:
        start_x = 10
        start_y = 180
        color_index = (SHAPES.index(next_tetromino) + level - 1) % len(COLORS) + 1
        for row_idx, row in enumerate(next_tetromino):
            for col_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(subwindow, COLORS[color_index-1],
                                     (start_x+col_idx*BLOCK_SIZE, start_y+row_idx*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
    # Tetris flash:
    if is_tetris:
        time_since_flash = pygame.time.get_ticks() - tetris_last_flash
        if time_since_flash < tetris_flash_time:
            flashing_color = random.choice(COLORS)
            flash_text = tetris_font_medium.render("TetraFusion!", True, flashing_color)
            text_x = (SUBWINDOW_WIDTH - flash_text.get_width()) // 2
            text_y = SCREEN_HEIGHT - 240
            subwindow.blit(flash_text, (text_x, text_y))
    # Sound Bar:
    current_volume = pygame.mixer.music.get_volume() if pygame.mixer.music.get_busy() else 0
    sound_label = tetris_font_small.render("Music:", True, WHITE)
    subwindow.blit(sound_label, (10, SCREEN_HEIGHT - 220))
    bar_x = 10
    bar_y = SCREEN_HEIGHT - 200
    bar_width = SUBWINDOW_WIDTH - 20
    bar_height = 20
    sound_bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(subwindow, WHITE, sound_bar_rect, 2)
    fill_width = int(current_volume * bar_width)
    pygame.draw.rect(subwindow, (0,200,0), (bar_x, bar_y, fill_width, bar_height))
    # Buttons:
    if settings.get('use_custom_music', False):
        btn_space = 40
        button_width = (SUBWINDOW_WIDTH - btn_space) // 3
        button_y = SCREEN_HEIGHT - 60
        restart_button_rect = pygame.Rect(10, button_y, button_width, 30)
        skip_button_rect = pygame.Rect(20+button_width, button_y, button_width, 30)
        menu_button_rect = pygame.Rect(30+2*button_width, button_y, button_width, 30)
        pygame.draw.rect(subwindow, (50,50,200), restart_button_rect)
        restart_text = tetris_font_small.render("Restart", True, WHITE)
        subwindow.blit(restart_text, (restart_button_rect.x+(restart_button_rect.width-restart_text.get_width())//2,
                                       restart_button_rect.y+(restart_button_rect.height-restart_text.get_height())//2))
        pygame.draw.rect(subwindow, (200,200,50), skip_button_rect)
        skip_text = tetris_font_small.render("Skip Track", True, WHITE)
        subwindow.blit(skip_text, (skip_button_rect.x+(skip_button_rect.width-skip_text.get_width())//2,
                                   skip_button_rect.y+(skip_button_rect.height-skip_text.get_height())//2))
        pygame.draw.rect(subwindow, (200,50,50), menu_button_rect)
        menu_text = tetris_font_small.render("Main Menu", True, WHITE)
        subwindow.blit(menu_text, (menu_button_rect.x+(menu_button_rect.width-menu_text.get_width())//2,
                                   menu_button_rect.y+(menu_button_rect.height-menu_text.get_height())//2))
    else:
        button_width = (SUBWINDOW_WIDTH - 30) // 2
        button_y = SCREEN_HEIGHT - 60
        restart_button_rect = pygame.Rect(10, button_y, button_width, 30)
        menu_button_rect = pygame.Rect(20+button_width, button_y, button_width, 30)
        pygame.draw.rect(subwindow, (50,50,200), restart_button_rect)
        restart_text = tetris_font_small.render("Restart", True, WHITE)
        subwindow.blit(restart_text, (restart_button_rect.x+(restart_button_rect.width-restart_text.get_width())//2,
                                       restart_button_rect.y+(restart_button_rect.height-restart_text.get_height())//2))
        pygame.draw.rect(subwindow, (200,50,50), menu_button_rect)
        menu_text = tetris_font_small.render("Main Menu", True, WHITE)
        subwindow.blit(menu_text, (menu_button_rect.x+(menu_button_rect.width-menu_text.get_width())//2,
                                   menu_button_rect.y+(menu_button_rect.height-menu_text.get_height())//2))
    screen.blit(subwindow, (SCREEN_WIDTH, 0))

# -------------------------- Ghost Piece (Drop Shadow) --------------------------
def draw_ghost_piece(tetromino, offset, grid):
    # Compute landing position:
    ghost_y = offset[1]
    while valid_position(tetromino, [offset[0], ghost_y + 1], grid):
        ghost_y += 1
    ghost_offset = [offset[0], ghost_y]
    ghost_alpha = 128  # 50% transparency
    ghost_color = (128, 128, 128)  # fixed gray for ghost piece
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = (ghost_offset[0] + cx) * BLOCK_SIZE
                y = (ghost_offset[1] + cy) * BLOCK_SIZE
                ghost_block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                ghost_block.fill((*ghost_color, ghost_alpha))
                screen.blit(ghost_block, (x, y))

# -------------------------- Custom Music Functions --------------------------
def play_custom_music(settings):
    global custom_music_playlist, current_track_index
    if not settings.get('music_enabled', True):
        pygame.mixer.music.stop()
        return
    update_custom_music_playlist(settings)
    if custom_music_playlist:
        track = custom_music_playlist[current_track_index]
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(track)
            # Play track once (no looping) so MUSIC_END_EVENT is triggered.
            pygame.mixer.music.play(0)
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        except Exception as e:
            print(f"Error playing custom music: {e}")
    else:
        print("No music files found in the selected directory.")

def skip_current_track():
    global custom_music_playlist, current_track_index
    if custom_music_playlist:
        current_track_index = (current_track_index + 1) % len(custom_music_playlist)
        try:
            pygame.mixer.music.load(custom_music_playlist[current_track_index])
            pygame.mixer.music.play(0)
        except Exception as e:
            print(f"Error skipping to next track: {e}")

def stop_music():
    pygame.mixer.music.stop()

# -------------------------- Menu System --------------------------
def draw_main_menu():
    screen.fill(BLACK)
    title_text = tetris_font_large.render("TetraFusion", True, random.choice(COLORS))
    start_text = tetris_font_medium.render("Press ENTER to Start", True, WHITE)
    options_text = tetris_font_medium.render("Press O for Options", True, WHITE)
    exit_text = tetris_font_medium.render("Press ESC to Quit", True, WHITE)
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//3))
    screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, SCREEN_HEIGHT//2))
    screen.blit(options_text, (SCREEN_WIDTH//2 - options_text.get_width()//2, SCREEN_HEIGHT//2+50))
    screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT//2+100))
    pygame.display.flip()

def main_menu():
    while True:
        draw_main_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return
                elif event.key == pygame.K_o:
                    options_menu()
                elif event.key == pygame.K_ESCAPE:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()

def options_menu():
    global settings
    selected_option = 0
    options = [
        ('left', 'Left'),
        ('right', 'Right'),
        ('down', 'Down'),
        ('rotate', 'Rotate'),
        ('pause', 'Pause'),
        ('hard_drop', 'Hard Drop'),
        ('difficulty', 'Difficulty'),
        ('flame_trails', 'Flame Trails'),
        ('grid_opacity', 'Grid Opacity'),
        ('grid_lines', 'Grid Lines'),
        ('ghost_piece', 'Ghost Piece'),
        ('music_enabled', 'Music'),
        ('use_custom_music', 'Use Custom Music'),
        ('select_music_dir', 'Select Music Directory'),
        ('back', 'Back to Main Menu')
    ]
    changing_key = None
    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Options", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
        for i, (key, label) in enumerate(options):
            color = RED if i==selected_option else WHITE
            text = label
            if key in settings['controls']:
                text = f"{label}: {pygame.key.name(settings['controls'][key]).upper()}"
            elif key=='difficulty':
                text = f"Difficulty: {settings['difficulty'].capitalize()}"
            elif key=='flame_trails':
                text = f"Flame Trails: {'On' if settings['flame_trails'] else 'Off'}"
            elif key=='grid_opacity':
                text = f"Grid Opacity: {settings['grid_opacity']}"
            elif key=='grid_lines':
                text = f"Grid Lines: {'On' if settings.get('grid_lines', True) else 'Off'}"
            elif key=='ghost_piece':
                text = f"Ghost Piece: {'On' if settings.get('ghost_piece', True) else 'Off'}"
            elif key=='music_enabled':
                text = f"Music: {'On' if settings.get('music_enabled', True) else 'Off'}"
            elif key=='use_custom_music':
                text = f"Use Custom Music: {'On' if settings.get('use_custom_music', False) else 'Off'}"
            elif key=='select_music_dir':
                dir_display = settings.get('music_directory', '')
                text = f"Select Music Directory: {dir_display if dir_display else 'Not Selected'}"
            option_text = tetris_font_medium.render(text, True, color)
            screen.blit(option_text, (SCREEN_WIDTH//2 - option_text.get_width()//2, 150+i*50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if changing_key:
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                elif event.key==pygame.K_UP:
                    selected_option = (selected_option-1)%len(options)
                elif event.key==pygame.K_DOWN:
                    selected_option = (selected_option+1)%len(options)
                elif event.key==pygame.K_RETURN:
                    current_key = options[selected_option][0]
                    if current_key in settings['controls']:
                        changing_key = current_key
                    elif current_key=='difficulty':
                        difficulties = ['easy', 'normal', 'hard', 'very hard']
                        new_idx = (difficulties.index(settings['difficulty'])+1)%len(difficulties)
                        settings['difficulty'] = difficulties[new_idx]
                    elif current_key=='flame_trails':
                        settings['flame_trails'] = not settings['flame_trails']
                    elif current_key=='grid_opacity':
                        settings['grid_opacity'] = (settings['grid_opacity']+64)%256
                    elif current_key=='grid_lines':
                        settings['grid_lines'] = not settings.get('grid_lines', True)
                    elif current_key=='ghost_piece':
                        settings['ghost_piece'] = not settings.get('ghost_piece', True)
                    elif current_key=='music_enabled':
                        settings['music_enabled'] = not settings.get('music_enabled', True)
                        if not settings['music_enabled']:
                            stop_music()
                        else:
                            if settings.get('use_custom_music', False):
                                play_custom_music(settings)
                            else:
                                try:
                                    pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                                    pygame.mixer.music.play(-1)
                                except Exception as e:
                                    print(f"Error loading default music: {e}")
                    elif current_key=='use_custom_music':
                        settings['use_custom_music'] = not settings.get('use_custom_music', False)
                        if settings['use_custom_music']:
                            play_custom_music(settings)
                        else:
                            try:
                                pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                                pygame.mixer.music.play(-1)
                            except Exception as e:
                                print(f"Error loading default music: {e}")
                    elif current_key=='select_music_dir':
                        root = tk.Tk()
                        root.withdraw()
                        selected_dir = filedialog.askdirectory()
                        if selected_dir:
                            settings['music_directory'] = selected_dir
                            if settings.get('use_custom_music', False):
                                play_custom_music(settings)
                        root.destroy()
                    elif current_key=='back':
                        save_settings(settings)
                        return
                elif event.key==pygame.K_ESCAPE:
                    save_settings(settings)
                    return

def pause_game():
    global settings
    pause_text = tetris_font_large.render("PAUSED", True, WHITE)
    paused = True
    pygame.event.clear(pygame.KEYDOWN)
    while paused:
        screen.fill(BLACK)
        screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if event.key==settings['controls']['pause'] or event.key==pygame.K_ESCAPE:
                    paused = False

def display_game_over(score):
    global high_score, high_score_name
    if score > high_score:
        initials = ""
        input_active = True
        while input_active:
            screen.fill(BLACK)
            game_over_text = tetris_font_large.render("NEW HIGH SCORE!", True, RED)
            score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
            initials_text = tetris_font_medium.render(f"Enter Initials: {initials}", True, WHITE)
            menu_text = tetris_font_small.render("Press M for Menu or ENTER to Save", True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 50))
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
            screen.blit(initials_text, (SCREEN_WIDTH//2 - initials_text.get_width()//2, 250))
            screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, 350))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_RETURN and initials:
                        high_score = score
                        high_score_name = initials
                        save_high_score(high_score, high_score_name)
                        input_active = False
                    elif event.key==pygame.K_BACKSPACE:
                        initials = initials[:-1]
                    elif len(initials)<3 and event.unicode.isalnum():
                        initials += event.unicode.upper()
                    elif event.key==pygame.K_m:
                        main_menu()
                        return
    else:
        screen.fill(BLACK)
        game_over_text = tetris_font_large.render("GAME OVER", True, RED)
        score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
        restart_text = tetris_font_small.render("Press R to Restart", True, WHITE)
        menu_text = tetris_font_small.render("Press M for Menu", True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 50))
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT-130))
        screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, SCREEN_HEIGHT-100))
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_r:
                        run_game()
                        return
                    elif event.key==pygame.K_m:
                        main_menu()
                        return

def place_tetromino(tetromino, offset, grid, color_index):
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = offset[0] + cx
                y = offset[1] + cy
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    grid[y][x] = color_index

# -------------------------- Ghost Piece (Drop Shadow) --------------------------
def draw_ghost_piece(tetromino, offset, grid):
    # Compute landing position.
    ghost_y = offset[1]
    while valid_position(tetromino, [offset[0], ghost_y+1], grid):
        ghost_y += 1
    ghost_offset = [offset[0], ghost_y]
    ghost_alpha = 128  # 50% transparency
    ghost_color = (128, 128, 128)  # fixed gray color for ghost piece
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = (ghost_offset[0] + cx) * BLOCK_SIZE
                y = (ghost_offset[1] + cy) * BLOCK_SIZE
                ghost_block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                ghost_block.fill((*ghost_color, ghost_alpha))
                screen.blit(ghost_block, (x, y))

# -------------------------- Custom Music Functions --------------------------
def play_custom_music(settings):
    global custom_music_playlist, current_track_index
    if not settings.get('music_enabled', True):
        pygame.mixer.music.stop()
        return
    update_custom_music_playlist(settings)
    if custom_music_playlist:
        track = custom_music_playlist[current_track_index]
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play(0)  # play once so MUSIC_END_EVENT fires
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        except Exception as e:
            print(f"Error playing custom music: {e}")
    else:
        print("No music files found in the selected directory.")

def skip_current_track():
    global custom_music_playlist, current_track_index
    if custom_music_playlist:
        current_track_index = (current_track_index + 1) % len(custom_music_playlist)
        try:
            pygame.mixer.music.load(custom_music_playlist[current_track_index])
            pygame.mixer.music.play(0)
        except Exception as e:
            print(f"Error skipping track: {e}")

def stop_music():
    pygame.mixer.music.stop()

# -------------------------- Menu System --------------------------
def draw_main_menu():
    screen.fill(BLACK)
    title_text = tetris_font_large.render("TetraFusion", True, random.choice(COLORS))
    start_text = tetris_font_medium.render("Press ENTER to Start", True, WHITE)
    options_text = tetris_font_medium.render("Press O for Options", True, WHITE)
    exit_text = tetris_font_medium.render("Press ESC to Quit", True, WHITE)
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//3))
    screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, SCREEN_HEIGHT//2))
    screen.blit(options_text, (SCREEN_WIDTH//2 - options_text.get_width()//2, SCREEN_HEIGHT//2+50))
    screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT//2+100))
    pygame.display.flip()

def main_menu():
    while True:
        draw_main_menu()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_RETURN:
                    return
                elif event.key==pygame.K_o:
                    options_menu()
                elif event.key==pygame.K_ESCAPE:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()

def options_menu():
    global settings
    selected_option = 0
    options = [
        ('left', 'Left'),
        ('right', 'Right'),
        ('down', 'Down'),
        ('rotate', 'Rotate'),
        ('pause', 'Pause'),
        ('hard_drop', 'Hard Drop'),
        ('difficulty', 'Difficulty'),
        ('flame_trails', 'Flame Trails'),
        ('grid_opacity', 'Grid Opacity'),
        ('grid_lines', 'Grid Lines'),
        ('ghost_piece', 'Ghost Piece'),
        ('music_enabled', 'Music'),
        ('use_custom_music', 'Use Custom Music'),
        ('select_music_dir', 'Select Music Directory'),
        ('back', 'Back to Main Menu')
    ]
    changing_key = None
    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Options", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
        for i, (key, label) in enumerate(options):
            color = RED if i==selected_option else WHITE
            text = label
            if key in settings['controls']:
                text = f"{label}: {pygame.key.name(settings['controls'][key]).upper()}"
            elif key=='difficulty':
                text = f"Difficulty: {settings['difficulty'].capitalize()}"
            elif key=='flame_trails':
                text = f"Flame Trails: {'On' if settings['flame_trails'] else 'Off'}"
            elif key=='grid_opacity':
                text = f"Grid Opacity: {settings['grid_opacity']}"
            elif key=='grid_lines':
                text = f"Grid Lines: {'On' if settings.get('grid_lines', True) else 'Off'}"
            elif key=='ghost_piece':
                text = f"Ghost Piece: {'On' if settings.get('ghost_piece', True) else 'Off'}"
            elif key=='music_enabled':
                text = f"Music: {'On' if settings.get('music_enabled', True) else 'Off'}"
            elif key=='use_custom_music':
                text = f"Use Custom Music: {'On' if settings.get('use_custom_music', False) else 'Off'}"
            elif key=='select_music_dir':
                dir_display = settings.get('music_directory', '')
                text = f"Select Music Directory: {dir_display if dir_display else 'Not Selected'}"
            option_text = tetris_font_medium.render(text, True, color)
            screen.blit(option_text, (SCREEN_WIDTH//2 - option_text.get_width()//2, 150+i*50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if changing_key:
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                elif event.key==pygame.K_UP:
                    selected_option = (selected_option-1)%len(options)
                elif event.key==pygame.K_DOWN:
                    selected_option = (selected_option+1)%len(options)
                elif event.key==pygame.K_RETURN:
                    current_key = options[selected_option][0]
                    if current_key in settings['controls']:
                        changing_key = current_key
                    elif current_key=='difficulty':
                        difficulties = ['easy', 'normal', 'hard', 'very hard']
                        new_idx = (difficulties.index(settings['difficulty'])+1)%len(difficulties)
                        settings['difficulty'] = difficulties[new_idx]
                    elif current_key=='flame_trails':
                        settings['flame_trails'] = not settings['flame_trails']
                    elif current_key=='grid_opacity':
                        settings['grid_opacity'] = (settings['grid_opacity']+64)%256
                    elif current_key=='grid_lines':
                        settings['grid_lines'] = not settings.get('grid_lines', True)
                    elif current_key=='ghost_piece':
                        settings['ghost_piece'] = not settings.get('ghost_piece', True)
                    elif current_key=='music_enabled':
                        settings['music_enabled'] = not settings.get('music_enabled', True)
                        if not settings['music_enabled']:
                            stop_music()
                        else:
                            if settings.get('use_custom_music', False):
                                play_custom_music(settings)
                            else:
                                try:
                                    pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                                    pygame.mixer.music.play(-1)
                                except Exception as e:
                                    print(f"Error loading default music: {e}")
                    elif current_key=='use_custom_music':
                        settings['use_custom_music'] = not settings.get('use_custom_music', False)
                        if settings['use_custom_music']:
                            play_custom_music(settings)
                        else:
                            try:
                                pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                                pygame.mixer.music.play(-1)
                            except Exception as e:
                                print(f"Error loading default music: {e}")
                    elif current_key=='select_music_dir':
                        root = tk.Tk()
                        root.withdraw()
                        selected_dir = filedialog.askdirectory()
                        if selected_dir:
                            settings['music_directory'] = selected_dir
                            if settings.get('use_custom_music', False):
                                play_custom_music(settings)
                        root.destroy()
                    elif current_key=='back':
                        save_settings(settings)
                        return
                elif event.key==pygame.K_ESCAPE:
                    save_settings(settings)
                    return

def pause_game():
    global settings
    pause_text = tetris_font_large.render("PAUSED", True, WHITE)
    paused = True
    pygame.event.clear(pygame.KEYDOWN)
    while paused:
        screen.fill(BLACK)
        screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if event.key==settings['controls']['pause'] or event.key==pygame.K_ESCAPE:
                    paused = False

def display_game_over(score):
    global high_score, high_score_name
    if score > high_score:
        initials = ""
        input_active = True
        while input_active:
            screen.fill(BLACK)
            game_over_text = tetris_font_large.render("NEW HIGH SCORE!", True, RED)
            score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
            initials_text = tetris_font_medium.render(f"Enter Initials: {initials}", True, WHITE)
            menu_text = tetris_font_small.render("Press M for Menu or ENTER to Save", True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 50))
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
            screen.blit(initials_text, (SCREEN_WIDTH//2 - initials_text.get_width()//2, 250))
            screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, 350))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_RETURN and initials:
                        high_score = score
                        high_score_name = initials
                        save_high_score(high_score, high_score_name)
                        input_active = False
                    elif event.key==pygame.K_BACKSPACE:
                        initials = initials[:-1]
                    elif len(initials)<3 and event.unicode.isalnum():
                        initials += event.unicode.upper()
                    elif event.key==pygame.K_m:
                        main_menu()
                        return
    else:
        screen.fill(BLACK)
        game_over_text = tetris_font_large.render("GAME OVER", True, RED)
        score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
        restart_text = tetris_font_small.render("Press R to Restart", True, WHITE)
        menu_text = tetris_font_small.render("Press M for Menu", True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 50))
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT-130))
        screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, SCREEN_HEIGHT-100))
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_r:
                        run_game()
                        return
                    elif event.key==pygame.K_m:
                        main_menu()
                        return

def place_tetromino(tetromino, offset, grid, color_index):
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = offset[0] + cx
                y = offset[1] + cy
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    grid[y][x] = color_index

# -------------------------- Ghost Piece (Drop Shadow) --------------------------
def draw_ghost_piece(tetromino, offset, grid):
    # Calculate landing position for the ghost piece.
    ghost_y = offset[1]
    while valid_position(tetromino, [offset[0], ghost_y+1], grid):
        ghost_y += 1
    ghost_offset = [offset[0], ghost_y]
    ghost_alpha = 128  # 50% transparency
    ghost_color = (128, 128, 128)  # Fixed gray for ghost piece
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = (ghost_offset[0] + cx) * BLOCK_SIZE
                y = (ghost_offset[1] + cy) * BLOCK_SIZE
                ghost_block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                ghost_block.fill((*ghost_color, ghost_alpha))
                screen.blit(ghost_block, (x, y))

# -------------------------- Custom Music Functions --------------------------
def play_custom_music(settings):
    global custom_music_playlist, current_track_index
    if not settings.get('music_enabled', True):
        pygame.mixer.music.stop()
        return
    update_custom_music_playlist(settings)
    if custom_music_playlist:
        track = custom_music_playlist[current_track_index]
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play(0)  # play once so MUSIC_END_EVENT fires
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        except Exception as e:
            print(f"Error playing custom music: {e}")
    else:
        print("No music files found in the selected directory.")

def skip_current_track():
    global custom_music_playlist, current_track_index
    if custom_music_playlist:
        current_track_index = (current_track_index + 1) % len(custom_music_playlist)
        try:
            pygame.mixer.music.load(custom_music_playlist[current_track_index])
            pygame.mixer.music.play(0)
        except Exception as e:
            print(f"Error skipping to next track: {e}")

def stop_music():
    pygame.mixer.music.stop()

# -------------------------- Menu System --------------------------
def draw_main_menu():
    screen.fill(BLACK)
    title_text = tetris_font_large.render("TetraFusion", True, random.choice(COLORS))
    start_text = tetris_font_medium.render("Press ENTER to Start", True, WHITE)
    options_text = tetris_font_medium.render("Press O for Options", True, WHITE)
    exit_text = tetris_font_medium.render("Press ESC to Quit", True, WHITE)
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//3))
    screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, SCREEN_HEIGHT//2))
    screen.blit(options_text, (SCREEN_WIDTH//2 - options_text.get_width()//2, SCREEN_HEIGHT//2+50))
    screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT//2+100))
    pygame.display.flip()

def main_menu():
    while True:
        draw_main_menu()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_RETURN:
                    return
                elif event.key==pygame.K_o:
                    options_menu()
                elif event.key==pygame.K_ESCAPE:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()

def options_menu():
    global settings
    selected_option = 0
    options = [
        ('left', 'Left'),
        ('right', 'Right'),
        ('down', 'Down'),
        ('rotate', 'Rotate'),
        ('pause', 'Pause'),
        ('hard_drop', 'Hard Drop'),
        ('difficulty', 'Difficulty'),
        ('flame_trails', 'Flame Trails'),
        ('grid_opacity', 'Grid Opacity'),
        ('grid_lines', 'Grid Lines'),
        ('ghost_piece', 'Ghost Piece'),
        ('music_enabled', 'Music'),
        ('use_custom_music', 'Use Custom Music'),
        ('select_music_dir', 'Select Music Directory'),
        ('back', 'Back to Main Menu')
    ]
    changing_key = None
    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Options", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
        for i, (key, label) in enumerate(options):
            color = RED if i==selected_option else WHITE
            text = label
            if key in settings['controls']:
                text = f"{label}: {pygame.key.name(settings['controls'][key]).upper()}"
            elif key=='difficulty':
                text = f"Difficulty: {settings['difficulty'].capitalize()}"
            elif key=='flame_trails':
                text = f"Flame Trails: {'On' if settings['flame_trails'] else 'Off'}"
            elif key=='grid_opacity':
                text = f"Grid Opacity: {settings['grid_opacity']}"
            elif key=='grid_lines':
                text = f"Grid Lines: {'On' if settings.get('grid_lines', True) else 'Off'}"
            elif key=='ghost_piece':
                text = f"Ghost Piece: {'On' if settings.get('ghost_piece', True) else 'Off'}"
            elif key=='music_enabled':
                text = f"Music: {'On' if settings.get('music_enabled', True) else 'Off'}"
            elif key=='use_custom_music':
                text = f"Use Custom Music: {'On' if settings.get('use_custom_music', False) else 'Off'}"
            elif key=='select_music_dir':
                dir_display = settings.get('music_directory', '')
                text = f"Select Music Directory: {dir_display if dir_display else 'Not Selected'}"
            option_text = tetris_font_medium.render(text, True, color)
            screen.blit(option_text, (SCREEN_WIDTH//2 - option_text.get_width()//2, 150+i*50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if changing_key:
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                elif event.key==pygame.K_UP:
                    selected_option = (selected_option-1)%len(options)
                elif event.key==pygame.K_DOWN:
                    selected_option = (selected_option+1)%len(options)
                elif event.key==pygame.K_RETURN:
                    current_key = options[selected_option][0]
                    if current_key in settings['controls']:
                        changing_key = current_key
                    elif current_key=='difficulty':
                        difficulties = ['easy', 'normal', 'hard', 'very hard']
                        new_idx = (difficulties.index(settings['difficulty'])+1)%len(difficulties)
                        settings['difficulty'] = difficulties[new_idx]
                    elif current_key=='flame_trails':
                        settings['flame_trails'] = not settings['flame_trails']
                    elif current_key=='grid_opacity':
                        settings['grid_opacity'] = (settings['grid_opacity']+64)%256
                    elif current_key=='grid_lines':
                        settings['grid_lines'] = not settings.get('grid_lines', True)
                    elif current_key=='ghost_piece':
                        settings['ghost_piece'] = not settings.get('ghost_piece', True)
                    elif current_key=='music_enabled':
                        settings['music_enabled'] = not settings.get('music_enabled', True)
                        if not settings['music_enabled']:
                            stop_music()
                        else:
                            if settings.get('use_custom_music', False):
                                play_custom_music(settings)
                            else:
                                try:
                                    pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                                    pygame.mixer.music.play(-1)
                                except Exception as e:
                                    print(f"Error loading default music: {e}")
                    elif current_key=='use_custom_music':
                        settings['use_custom_music'] = not settings.get('use_custom_music', False)
                        if settings['use_custom_music']:
                            play_custom_music(settings)
                        else:
                            try:
                                pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                                pygame.mixer.music.play(-1)
                            except Exception as e:
                                print(f"Error loading default music: {e}")
                    elif current_key=='select_music_dir':
                        root = tk.Tk()
                        root.withdraw()
                        selected_dir = filedialog.askdirectory()
                        if selected_dir:
                            settings['music_directory'] = selected_dir
                            if settings.get('use_custom_music', False):
                                play_custom_music(settings)
                        root.destroy()
                    elif current_key=='back':
                        save_settings(settings)
                        return
                elif event.key==pygame.K_ESCAPE:
                    save_settings(settings)
                    return

def pause_game():
    global settings
    pause_text = tetris_font_large.render("PAUSED", True, WHITE)
    paused = True
    pygame.event.clear(pygame.KEYDOWN)
    while paused:
        screen.fill(BLACK)
        screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if event.key==settings['controls']['pause'] or event.key==pygame.K_ESCAPE:
                    paused = False

def display_game_over(score):
    global high_score, high_score_name
    if score > high_score:
        initials = ""
        input_active = True
        while input_active:
            screen.fill(BLACK)
            game_over_text = tetris_font_large.render("NEW HIGH SCORE!", True, RED)
            score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
            initials_text = tetris_font_medium.render(f"Enter Initials: {initials}", True, WHITE)
            menu_text = tetris_font_small.render("Press M for Menu or ENTER to Save", True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 50))
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
            screen.blit(initials_text, (SCREEN_WIDTH//2 - initials_text.get_width()//2, 250))
            screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, 350))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_RETURN and initials:
                        high_score = score
                        high_score_name = initials
                        save_high_score(high_score, high_score_name)
                        input_active = False
                    elif event.key==pygame.K_BACKSPACE:
                        initials = initials[:-1]
                    elif len(initials)<3 and event.unicode.isalnum():
                        initials += event.unicode.upper()
                    elif event.key==pygame.K_m:
                        main_menu()
                        return
    else:
        screen.fill(BLACK)
        game_over_text = tetris_font_large.render("GAME OVER", True, RED)
        score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
        restart_text = tetris_font_small.render("Press R to Restart", True, WHITE)
        menu_text = tetris_font_small.render("Press M for Menu", True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 50))
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT-130))
        screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, SCREEN_HEIGHT-100))
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_r:
                        run_game()
                        return
                    elif event.key==pygame.K_m:
                        main_menu()
                        return

def place_tetromino(tetromino, offset, grid, color_index):
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = offset[0] + cx
                y = offset[1] + cy
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    grid[y][x] = color_index

# -------------------------- Ghost Piece (Drop Shadow) --------------------------
def draw_ghost_piece(tetromino, offset, grid):
    ghost_y = offset[1]
    while valid_position(tetromino, [offset[0], ghost_y+1], grid):
        ghost_y += 1
    ghost_offset = [offset[0], ghost_y]
    ghost_alpha = 128
    ghost_color = (128,128,128)
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = (ghost_offset[0] + cx) * BLOCK_SIZE
                y = (ghost_offset[1] + cy) * BLOCK_SIZE
                ghost_block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                ghost_block.fill((*ghost_color, ghost_alpha))
                screen.blit(ghost_block, (x, y))

# -------------------------- Custom Music Functions --------------------------
def play_custom_music(settings):
    global custom_music_playlist, current_track_index
    if not settings.get('music_enabled', True):
        pygame.mixer.music.stop()
        return
    update_custom_music_playlist(settings)
    if custom_music_playlist:
        track = custom_music_playlist[current_track_index]
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play(0)
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        except Exception as e:
            print(f"Error playing custom music: {e}")
    else:
        print("No music files found in the selected directory.")

def skip_current_track():
    global custom_music_playlist, current_track_index
    if custom_music_playlist:
        current_track_index = (current_track_index + 1) % len(custom_music_playlist)
        try:
            pygame.mixer.music.load(custom_music_playlist[current_track_index])
            pygame.mixer.music.play(0)
        except Exception as e:
            print(f"Error skipping track: {e}")

def stop_music():
    pygame.mixer.music.stop()

# -------------------------- Menu System --------------------------
def draw_main_menu():
    screen.fill(BLACK)
    title_text = tetris_font_large.render("TetraFusion", True, random.choice(COLORS))
    start_text = tetris_font_medium.render("Press ENTER to Start", True, WHITE)
    options_text = tetris_font_medium.render("Press O for Options", True, WHITE)
    exit_text = tetris_font_medium.render("Press ESC to Quit", True, WHITE)
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//3))
    screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, SCREEN_HEIGHT//2))
    screen.blit(options_text, (SCREEN_WIDTH//2 - options_text.get_width()//2, SCREEN_HEIGHT//2+50))
    screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT//2+100))
    pygame.display.flip()

def main_menu():
    while True:
        draw_main_menu()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_RETURN:
                    return
                elif event.key==pygame.K_o:
                    options_menu()
                elif event.key==pygame.K_ESCAPE:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()

def options_menu():
    global settings
    selected_option = 0
    options = [
        ('left', 'Left'),
        ('right', 'Right'),
        ('down', 'Down'),
        ('rotate', 'Rotate'),
        ('pause', 'Pause'),
        ('hard_drop', 'Hard Drop'),
        ('difficulty', 'Difficulty'),
        ('flame_trails', 'Flame Trails'),
        ('grid_opacity', 'Grid Opacity'),
        ('grid_lines', 'Grid Lines'),
        ('ghost_piece', 'Ghost Piece'),
        ('music_enabled', 'Music'),
        ('use_custom_music', 'Use Custom Music'),
        ('select_music_dir', 'Select Music Directory'),
        ('back', 'Back to Main Menu')
    ]
    changing_key = None
    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Options", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
        for i, (key, label) in enumerate(options):
            color = RED if i==selected_option else WHITE
            text = label
            if key in settings['controls']:
                text = f"{label}: {pygame.key.name(settings['controls'][key]).upper()}"
            elif key=='difficulty':
                text = f"Difficulty: {settings['difficulty'].capitalize()}"
            elif key=='flame_trails':
                text = f"Flame Trails: {'On' if settings['flame_trails'] else 'Off'}"
            elif key=='grid_opacity':
                text = f"Grid Opacity: {settings['grid_opacity']}"
            elif key=='grid_lines':
                text = f"Grid Lines: {'On' if settings.get('grid_lines', True) else 'Off'}"
            elif key=='ghost_piece':
                text = f"Ghost Piece: {'On' if settings.get('ghost_piece', True) else 'Off'}"
            elif key=='music_enabled':
                text = f"Music: {'On' if settings.get('music_enabled', True) else 'Off'}"
            elif key=='use_custom_music':
                text = f"Use Custom Music: {'On' if settings.get('use_custom_music', False) else 'Off'}"
            elif key=='select_music_dir':
                dir_display = settings.get('music_directory', '')
                text = f"Select Music Directory: {dir_display if dir_display else 'Not Selected'}"
            option_text = tetris_font_medium.render(text, True, color)
            screen.blit(option_text, (SCREEN_WIDTH//2 - option_text.get_width()//2, 150+i*50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if changing_key:
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                elif event.key==pygame.K_UP:
                    selected_option = (selected_option-1)%len(options)
                elif event.key==pygame.K_DOWN:
                    selected_option = (selected_option+1)%len(options)
                elif event.key==pygame.K_RETURN:
                    current_key = options[selected_option][0]
                    if current_key in settings['controls']:
                        changing_key = current_key
                    elif current_key=='difficulty':
                        difficulties = ['easy', 'normal', 'hard', 'very hard']
                        new_idx = (difficulties.index(settings['difficulty'])+1)%len(difficulties)
                        settings['difficulty'] = difficulties[new_idx]
                    elif current_key=='flame_trails':
                        settings['flame_trails'] = not settings['flame_trails']
                    elif current_key=='grid_opacity':
                        settings['grid_opacity'] = (settings['grid_opacity']+64)%256
                    elif current_key=='grid_lines':
                        settings['grid_lines'] = not settings.get('grid_lines', True)
                    elif current_key=='ghost_piece':
                        settings['ghost_piece'] = not settings.get('ghost_piece', True)
                    elif current_key=='music_enabled':
                        settings['music_enabled'] = not settings.get('music_enabled', True)
                        if not settings['music_enabled']:
                            stop_music()
                        else:
                            if settings.get('use_custom_music', False):
                                play_custom_music(settings)
                            else:
                                try:
                                    pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                                    pygame.mixer.music.play(-1)
                                except Exception as e:
                                    print(f"Error loading default music: {e}")
                    elif current_key=='use_custom_music':
                        settings['use_custom_music'] = not settings.get('use_custom_music', False)
                        if settings['use_custom_music']:
                            play_custom_music(settings)
                        else:
                            try:
                                pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                                pygame.mixer.music.play(-1)
                            except Exception as e:
                                print(f"Error loading default music: {e}")
                    elif current_key=='select_music_dir':
                        root = tk.Tk()
                        root.withdraw()
                        selected_dir = filedialog.askdirectory()
                        if selected_dir:
                            settings['music_directory'] = selected_dir
                            if settings.get('use_custom_music', False):
                                play_custom_music(settings)
                        root.destroy()
                    elif current_key=='back':
                        save_settings(settings)
                        return
                elif event.key==pygame.K_ESCAPE:
                    save_settings(settings)
                    return

def pause_game():
    global settings
    pause_text = tetris_font_large.render("PAUSED", True, WHITE)
    paused = True
    pygame.event.clear(pygame.KEYDOWN)
    while paused:
        screen.fill(BLACK)
        screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==pygame.KEYDOWN:
                if event.key==settings['controls']['pause'] or event.key==pygame.K_ESCAPE:
                    paused = False

def display_game_over(score):
    global high_score, high_score_name
    if score > high_score:
        initials = ""
        input_active = True
        while input_active:
            screen.fill(BLACK)
            game_over_text = tetris_font_large.render("NEW HIGH SCORE!", True, RED)
            score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
            initials_text = tetris_font_medium.render(f"Enter Initials: {initials}", True, WHITE)
            menu_text = tetris_font_small.render("Press M for Menu or ENTER to Save", True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 50))
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
            screen.blit(initials_text, (SCREEN_WIDTH//2 - initials_text.get_width()//2, 250))
            screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, 350))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_RETURN and initials:
                        high_score = score
                        high_score_name = initials
                        save_high_score(high_score, high_score_name)
                        input_active = False
                    elif event.key==pygame.K_BACKSPACE:
                        initials = initials[:-1]
                    elif len(initials)<3 and event.unicode.isalnum():
                        initials += event.unicode.upper()
                    elif event.key==pygame.K_m:
                        main_menu()
                        return
    else:
        screen.fill(BLACK)
        game_over_text = tetris_font_large.render("GAME OVER", True, RED)
        score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
        restart_text = tetris_font_small.render("Press R to Restart", True, WHITE)
        menu_text = tetris_font_small.render("Press M for Menu", True, WHITE)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 50))
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 150))
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT-130))
        screen.blit(menu_text, (SCREEN_WIDTH//2 - menu_text.get_width()//2, SCREEN_HEIGHT-100))
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_r:
                        run_game()
                        return
                    elif event.key==pygame.K_m:
                        main_menu()
                        return

def place_tetromino(tetromino, offset, grid, color_index):
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = offset[0] + cx
                y = offset[1] + cy
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    grid[y][x] = color_index

# -------------------------- Game Loop --------------------------
def run_game():
    global high_score, high_score_name, subwindow_visible, last_click_time, settings, heartbeat_playing, game_command
    global restart_button_rect, menu_button_rect, skip_button_rect, sound_bar_rect, current_track_index, custom_music_playlist
    game_command = None
    controls = settings['controls']
    difficulty = settings['difficulty']
    flame_trails_enabled = settings['flame_trails']
    grid_color = tuple(settings['grid_color'])
    grid_opacity = settings.get('grid_opacity', 128)
    grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    draw_3d_grid(grid_surface, grid_color, grid_opacity)
    
    difficulty_speeds = {
        'easy': 1500,
        'normal': 1000,
        'hard': 600,
        'very hard': 400
    }
    base_fall_speed = difficulty_speeds.get(difficulty, 1000)
    fall_speed = base_fall_speed

    level = 1
    lines_cleared_total = 0
    pieces_dropped = 0
    wind_particles = []
    trail_particles = []
    explosion_particles = []
    dust_particles = []
    screen_shake = 0
    grid = create_grid()
    tetromino_bag = TetrominoBag(SHAPES)
    tetromino = tetromino_bag.get_next_tetromino()
    next_tetromino = tetromino_bag.get_next_tetromino()
    color_index = (SHAPES.index(tetromino) + level - 1) % len(COLORS) + 1
    offset = [GRID_WIDTH//2 - len(tetromino[0])//2, 0]
    score = 0
    fast_fall = False
    last_fall_time = pygame.time.get_ticks()
    game_over = False
    left_pressed = False
    right_pressed = False
    last_horizontal_move = 0
    move_interval = 150
    fast_move_interval = 50
    is_tetris = False
    tetris_flash_time = 2000
    tetris_last_flash = 0

    in_level_transition = False
    transition_start_time = 0
    TRANSITION_DURATION = 2000
    FLASH_INTERVAL = 100
    last_flash_time = 0
    flash_count = 0

    pygame.key.set_repeat(300, 100)

    while True:
        current_time = pygame.time.get_ticks()
        shake_intensity = screen_shake * 2
        shake_x = random.randint(-shake_intensity, shake_intensity) if screen_shake > 0 else 0
        shake_y = random.randint(-shake_intensity, shake_intensity) if screen_shake > 0 else 0

        if game_over:
            if heartbeat_playing and heartbeat_sound:
                heartbeat_sound.stop()
                heartbeat_playing = False
            if game_over_sound:
                game_over_sound.play()
            display_game_over(score)
            return

        if in_level_transition:
            if current_time - transition_start_time > TRANSITION_DURATION:
                in_level_transition = False
                grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                draw_3d_grid(grid_surface, grid_color, grid_opacity)
                for y in range(GRID_HEIGHT):
                    for x in range(GRID_WIDTH):
                        if grid[y][x] != 0:
                            grid[y][x] = random.randint(1, len(COLORS))
            else:
                if current_time - last_flash_time > FLASH_INTERVAL:
                    for y in range(GRID_HEIGHT):
                        for x in range(GRID_WIDTH):
                            if grid[y][x] != 0:
                                grid[y][x] = random.randint(1, len(COLORS))
                    last_flash_time = current_time
                    flash_count += 1
            screen.fill(BLACK)
            screen.blit(grid_surface, (0,0))
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if grid[y][x]:
                        draw_3d_block(screen, COLORS[grid[y][x]-1],
                                      x*BLOCK_SIZE+shake_x,
                                      y*BLOCK_SIZE+shake_y,
                                      BLOCK_SIZE)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0,0))
            level_text = tetris_font_large.render(f"LEVEL {level}", True, random.choice(COLORS))
            level_shake_x = random.randint(-10,10)
            level_shake_y = random.randint(-10,10)
            screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2+level_shake_x,
                                      SCREEN_HEIGHT//2 - level_text.get_height()//2+level_shake_y))
        screen.fill(BLACK)
        screen.blit(grid_surface, (0,0))
        if settings.get('grid_lines', True):
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if grid[y][x]:
                        draw_3d_block(screen, COLORS[grid[y][x]-1],
                                      x*BLOCK_SIZE+shake_x,
                                      y*BLOCK_SIZE+shake_y,
                                      BLOCK_SIZE)
                    pygame.draw.rect(screen, grid_color,
                                     (x*BLOCK_SIZE+shake_x, y*BLOCK_SIZE+shake_y, BLOCK_SIZE, BLOCK_SIZE), 1)
        else:
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if grid[y][x]:
                        draw_3d_block(screen, COLORS[grid[y][x]-1],
                                      x*BLOCK_SIZE+shake_x,
                                      y*BLOCK_SIZE+shake_y,
                                      BLOCK_SIZE)
        # Draw ghost piece (drop shadow) on top of placed blocks.
        if settings.get('ghost_piece', True):
            draw_ghost_piece(tetromino, offset, grid)
        # Draw falling tetromino.
        for cy, row in enumerate(tetromino):
            for cx, cell in enumerate(row):
                if cell:
                    draw_3d_block(screen, COLORS[color_index-1],
                                  (offset[0]+cx)*BLOCK_SIZE+shake_x,
                                  (offset[1]+cy)*BLOCK_SIZE+shake_y,
                                  BLOCK_SIZE)
        draw_subwindow(score, next_tetromino, level, pieces_dropped, lines_cleared_total, is_tetris, tetris_last_flash, tetris_flash_time)
        if is_danger_zone_active(grid):
            if not heartbeat_playing and heartbeat_sound:
                heartbeat_sound.play(-1)
                heartbeat_playing = True
        else:
            if heartbeat_playing and heartbeat_sound:
                heartbeat_sound.stop()
                heartbeat_playing = False
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type==MUSIC_END_EVENT:
                if settings.get('use_custom_music', False) and custom_music_playlist:
                    current_track_index = (current_track_index + 1) % len(custom_music_playlist)
                    try:
                        pygame.mixer.music.load(custom_music_playlist[current_track_index])
                        pygame.mixer.music.play(0)
                    except Exception as e:
                        print(f"Error loading next track: {e}")
            elif event.type==pygame.MOUSEBUTTONDOWN:
                if event.pos[0] >= SCREEN_WIDTH:
                    rel_x = event.pos[0] - SCREEN_WIDTH
                    rel_y = event.pos[1]
                    if sound_bar_rect and sound_bar_rect.collidepoint(rel_x, rel_y):
                        new_volume = (rel_x - sound_bar_rect.x) / sound_bar_rect.width
                        pygame.mixer.music.set_volume(new_volume)
                    if restart_button_rect and restart_button_rect.collidepoint(rel_x, rel_y):
                        game_command = "restart"
                        return
                    if settings.get('use_custom_music', False):
                        if skip_button_rect and skip_button_rect.collidepoint(rel_x, rel_y):
                            skip_current_track()
                    if menu_button_rect and menu_button_rect.collidepoint(rel_x, rel_y):
                        game_command = "menu"
                        return
            elif event.type==pygame.MOUSEMOTION:
                if event.buttons[0]:
                    if event.pos[0] >= SCREEN_WIDTH:
                        rel_x = event.pos[0] - SCREEN_WIDTH
                        if sound_bar_rect and sound_bar_rect.collidepoint(rel_x, event.pos[1]):
                            new_volume = (rel_x - sound_bar_rect.x) / sound_bar_rect.width
                            pygame.mixer.music.set_volume(new_volume)
            elif event.type==pygame.KEYDOWN:
                if event.key==controls['left']:
                    left_pressed = True
                    new_x = offset[0] - 1
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                    last_horizontal_move = current_time
                elif event.key==controls['right']:
                    right_pressed = True
                    new_x = offset[0] + 1
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                    last_horizontal_move = current_time
                elif event.key==controls['down']:
                    fast_fall = True
                elif event.key==controls['rotate']:
                    rotated, new_offset = rotate_tetromino_with_kick(tetromino, offset, grid)
                    tetromino, offset = rotated, new_offset
                elif event.key==settings['controls']['pause']:
                    pause_game()
                elif event.key==controls['hard_drop']:
                    hard_drop_rows = 0
                    temp_offset = offset.copy()
                    while valid_position(tetromino, [temp_offset[0], temp_offset[1]+1], grid):
                        temp_offset[1] += 1
                        hard_drop_rows += 1
                    offset[1] = temp_offset[1]
                    score += hard_drop_rows * 2
                    for _ in range(20 + hard_drop_rows * 5):
                        dust_particles.append(DustParticle(
                            (offset[0] + random.uniform(-1, len(tetromino[0])+1)) * BLOCK_SIZE,
                            (offset[1] + len(tetromino)) * BLOCK_SIZE
                        ))
            elif event.type==pygame.KEYUP:
                if event.key==controls['left']:
                    left_pressed = False
                elif event.key==controls['right']:
                    right_pressed = False
                elif event.key==controls['down']:
                    fast_fall = False

        if left_pressed or right_pressed:
            time_since_last_move = current_time - last_horizontal_move
            required_delay = fast_move_interval if time_since_last_move > move_interval else move_interval
            if time_since_last_move >= required_delay:
                direction = -1 if left_pressed else 1
                new_x = offset[0] + direction
                if valid_position(tetromino, [new_x, offset[1]], grid):
                    offset[0] = new_x
                last_horizontal_move = current_time

        current_fall_speed = 50 if fast_fall else fall_speed
        if current_time - last_fall_time > current_fall_speed:
            if valid_position(tetromino, [offset[0], offset[1]+1], grid):
                offset[1] += 1
            else:
                if check_game_over(grid):
                    game_over = True
                else:
                    original_grid = [row[:] for row in grid]
                    place_tetromino(tetromino, offset, grid, color_index)
                    grid, lines_cleared = clear_lines(grid)
                    lines_cleared_total += lines_cleared
                    score = update_score(score, lines_cleared)
                    pieces_dropped += 1
                    if lines_cleared > 0:
                        screen_shake = 8 + lines_cleared * 3
                        full_lines = [y for y in range(GRID_HEIGHT) if all(original_grid[y])]
                        for y in full_lines:
                            for x in range(GRID_WIDTH):
                                if original_grid[y][x] != 0:
                                    explosion_particles.append(Explosion(
                                        x * BLOCK_SIZE + BLOCK_SIZE//2,
                                        y * BLOCK_SIZE + BLOCK_SIZE//2,
                                        COLORS[original_grid[y][x]-1],
                                        particle_count=45,
                                        max_speed=15,
                                        duration=75
                                    ))
                    if lines_cleared == 4:
                        is_tetris = True
                        tetris_last_flash = current_time
                    new_level = lines_cleared_total // 10 + 1
                    if new_level > level:
                        level = new_level
                        fall_speed = max(50, int(base_fall_speed * (0.85 ** (level-1))))
                        in_level_transition = True
                        transition_start_time = current_time
                        last_flash_time = current_time
                        flash_count = 0
                    tetromino = next_tetromino
                    color_index = (SHAPES.index(tetromino) + level - 1) % len(COLORS) + 1
                    next_tetromino = tetromino_bag.get_next_tetromino()
                    offset = [GRID_WIDTH//2 - len(tetromino[0])//2, 0]
            last_fall_time = current_time

        if flame_trails_enabled and (left_pressed or right_pressed or fast_fall):
            num_particles = random.randint(3, 5)
            spawn_offset = 15
            for _ in range(num_particles):
                if left_pressed:
                    direction = "left"
                    spawn_x = (offset[0]-1)*BLOCK_SIZE + random.randint(-spawn_offset, 0)
                    spawn_y = (offset[1] + random.uniform(0.2, 0.8)*len(tetromino)) * BLOCK_SIZE
                elif right_pressed:
                    direction = "right"
                    spawn_x = (offset[0] + len(tetromino[0]))*BLOCK_SIZE + random.randint(0, spawn_offset)
                    spawn_y = (offset[1] + random.uniform(0.2, 0.8)*len(tetromino)) * BLOCK_SIZE
                else:
                    direction = "down"
                    spawn_x = (offset[0] + random.uniform(0.2, 0.8)*len(tetromino[0]))*BLOCK_SIZE
                    spawn_y = (offset[1] + len(tetromino))*BLOCK_SIZE - spawn_offset
                trail_particles.append(TrailParticle(spawn_x, spawn_y, direction))
        wind_force = (
            -4.0 if left_pressed else 
            4.0 if right_pressed else 0,
            5.0 if fast_fall else 0
        )
        for particle in trail_particles[:]:
            particle.update(wind_force, screen)
            if particle.age >= particle.max_age:
                trail_particles.remove(particle)
        for particle in dust_particles[:]:
            particle.update()
            if particle.age >= particle.max_age:
                dust_particles.remove(particle)
        for explosion in explosion_particles[:]:
            explosion.update()
            if explosion.lifetime <= 0:
                explosion_particles.remove(explosion)
        screen_shake = max(0, screen_shake - 1)
        screen.fill(BLACK)
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if grid[y][x]:
                    draw_3d_block(screen, COLORS[grid[y][x]-1],
                                  x*BLOCK_SIZE+shake_x,
                                  y*BLOCK_SIZE+shake_y,
                                  BLOCK_SIZE)
                if settings.get('grid_lines', True):
                    pygame.draw.rect(screen, grid_color,
                                     (x*BLOCK_SIZE+shake_x, y*BLOCK_SIZE+shake_y, BLOCK_SIZE, BLOCK_SIZE), 1)
        for explosion in explosion_particles:
            explosion.draw(screen, (shake_x, shake_y))
        for cy, row in enumerate(tetromino):
            for cx, cell in enumerate(row):
                if cell:
                    draw_3d_block(screen, COLORS[color_index-1],
                                  (offset[0]+cx)*BLOCK_SIZE+shake_x,
                                  (offset[1]+cy)*BLOCK_SIZE+shake_y,
                                  BLOCK_SIZE)
        for particle in trail_particles:
            particle.draw(screen)
        for particle in dust_particles:
            particle.draw(screen)
        draw_subwindow(score, next_tetromino, level, pieces_dropped, lines_cleared_total, is_tetris, tetris_last_flash, tetris_flash_time)
        pygame.display.flip()
        clock.tick(60)

# -------------------------- Main --------------------------
def main():
    global settings, game_command
    settings = load_settings()
    if settings.get('music_enabled', True):
        if settings.get('use_custom_music', False):
            play_custom_music(settings)
        else:
            try:
                pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"Error loading default background music: {e}")
    while True:
        main_menu()
        while True:
            run_game()
            if game_command == "menu":
                break
        # When inner loop breaks (command == "menu"), return to main menu.

if __name__ == "__main__":
    main()
