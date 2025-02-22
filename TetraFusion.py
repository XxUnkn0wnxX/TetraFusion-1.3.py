# Game Ver 1.9.3.2
# Dependencies: pip install mutagen

import pygame
import random
import sys
import os
import math
import json
import glob
from mutagen import File  # Reads audio metadata safely
import tkinter as tk
from tkinter import filedialog
import copy  # Needed for deepcopy

pygame.init()
pygame.mixer.set_num_channels(32)
pygame.mixer.init()

GAME_CAPTION = "TetraFusion 1.9.3.2"  # Moved to top

last_track_index = None  # Stores the current track index at game over.

# -------------------------- Global Music Playlist Variables --------------------------
MUSIC_END_EVENT = pygame.USEREVENT + 1
custom_music_playlist = []  # Sorted list of music files (alphabetical order)
current_track_index = 0

# List of common audio file extensions
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a", ".wma"}

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
    """
    Recursively search the given directory for valid audio files.
    Uses both file extension checking and Mutagen to ensure the file is playable.
    The search order is as follows:
      1. Process files in the current directory first. Within the directory, files are sorted so that
         filenames starting with digits (0-9) come first, then those starting with English letters (A-Z),
         then all other files.
      2. Then process each subdirectory (in sorted order using the same criteria), appending their files.
    Returns a list of valid file paths in the order they are found.
    """
    music_files = []
    unsupported_files = []
    
    try:
        items = os.listdir(directory)
    except Exception as e:
        print(f"Error reading directory {directory}: {e}")
        return []

    # Separate items into files and subdirectories, ignoring hidden items.
    files = []
    subdirs = []
    for item in items:
        if item.startswith('.'):
            continue  # Skip hidden files/directories.
        full_path = os.path.join(directory, item)
        if os.path.isfile(full_path):
            files.append(item)
        elif os.path.isdir(full_path):
            subdirs.append(item)
    
    # Define a key function for sorting:
    # Category 0: Files starting with a digit (0-9)
    # Category 1: Files starting with an English letter (A-Z)
    # Category 2: All others (e.g., non-English characters, symbols)
    def sort_key(name):
        first_char = name[0]
        if first_char.isdigit():
            cat = 0
        elif "A" <= first_char.upper() <= "Z":
            cat = 1
        else:
            cat = 2
        return (cat, name.upper())
    
    # Sort the files and subdirectories using the key.
    files.sort(key=sort_key)
    subdirs.sort(key=sort_key)
    
    # Process files in the current directory.
    for file in files:
        full_path = os.path.join(directory, file)
        ext = os.path.splitext(full_path)[1].lower()
        # Check if file extension is a known audio format.
        if ext in AUDIO_EXTENSIONS:
            try:
                # Verify the file with Mutagen (checks actual audio header)
                if File(full_path) is not None:
                    music_files.append(full_path)
                else:
                    unsupported_files.append(file)
            except Exception as e:
                print(f"Skipping {file}: Error reading file - {e}")
                unsupported_files.append(file)
        else:
            unsupported_files.append(file)
    
    # Process each subdirectory recursively.
    for sub in subdirs:
        sub_path = os.path.join(directory, sub)
        # Append files from the subdirectory after processing the current directory.
        music_files.extend(get_music_files(sub_path))
    
    # Print unsupported files (if any) along with supported formats.
    if unsupported_files:
        print(f"Unsupported files detected in '{directory}':")
        for file in unsupported_files:
            print(f"  {file}")
        print("Supported formats are:", ", ".join(sorted(AUDIO_EXTENSIONS)))
    
    return music_files

def update_custom_music_playlist(settings):
    """Updates the custom music playlist based on user settings."""
    global custom_music_playlist, current_track_index

    if not settings.get('use_custom_music', False):
        custom_music_playlist = [BACKGROUND_MUSIC_PATH]
        current_track_index = 0
        return

    music_directory = settings['music_directory'].strip()
    if not os.path.isdir(music_directory):
        print("Invalid music directory; defaulting to default background music.")
        settings['music_directory'] = ""
        save_settings(settings)
        custom_music_playlist = [BACKGROUND_MUSIC_PATH]
        current_track_index = 0
        return

    # Get files that are recognized as actual audio formats
    playlist = get_music_files(music_directory)

    # Validate that Pygame can load the audio files
    valid_playlist = []
    for track in playlist:
        try:
            pygame.mixer.Sound(track)  # Test if Pygame can load it
            valid_playlist.append(track)
        except pygame.error as e:
            print(f"Skipping unsupported track: {track} - {e}")

    if not valid_playlist:
        print("No playable audio files found; defaulting to background music.")
        valid_playlist = [BACKGROUND_MUSIC_PATH]

    custom_music_playlist = valid_playlist
    current_track_index = 0

# macOS Dialog Thing

if sys.platform == "darwin":
    try:
        from AppKit import NSOpenPanel, NSApplication
    except ImportError:
        NSOpenPanel = None

    def select_music_directory():
        # Use NSOpenPanel on macOS if available.
        if NSOpenPanel is None:
            # Fallback if PyObjC is not installed.
            root = tk.Tk()
            root.withdraw()
            selected = filedialog.askdirectory()
            root.destroy()
            return selected
        panel = NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(False)
        panel.setCanChooseDirectories_(True)
        panel.setAllowsMultipleSelection_(False)
        result = panel.runModal()
        # Restore focus to the game window.
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        if result == 1:
            # panel.URL() returns an NSURL; we need its path.
            return panel.URL().path()
        return ""
else:
    # On non-macOS, simply use tkinter's filedialog.
    def select_music_directory():
        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askdirectory()
        root.destroy()
        return selected


# -------------------------- Constants --------------------------
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 930
BLOCK_SIZE = 30
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE
SUBWINDOW_WIDTH = 369
DOUBLE_CLICK_TIME = 300

hold_piece = None
hold_used = False  # Prevent repeated holds until the current piece locks in

YELLOW = (255, 255, 0)
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

# -------------------------- Helper for Rotations --------------------------
def rotate_matrix(matrix):
    """Rotates a matrix (list of lists) 90° clockwise."""
    return [list(row) for row in zip(*matrix[::-1])]

# -------------------------- Updated: get_shape_index Function --------------------------
def get_shape_index(tetromino):
    """
    Returns the index of the given tetromino shape in the SHAPES list.
    Checks all four rotations to find a match.
    If no match is found, prints an error and returns None.
    """
    for index, shape in enumerate(SHAPES):
        candidate = tetromino
        for _ in range(4):
            if candidate == shape:
                return index
            candidate = rotate_matrix(candidate)
    print("Error: Tetromino shape not found in SHAPES list.")
    return None

# -------------------------- Fonts --------------------------
TETRIS_FONT_PATH = "assets/tetris-blocks.TTF"
try:
    tetris_font_large = pygame.font.Font(TETRIS_FONT_PATH, 40)
    tetris_font_medium = pygame.font.Font(TETRIS_FONT_PATH, 27)
    tetris_font_small = pygame.font.Font(TETRIS_FONT_PATH, 18)
    tetris_font_smaller = pygame.font.Font(TETRIS_FONT_PATH, 16)
    tetris_font_tiny = pygame.font.Font(TETRIS_FONT_PATH, 14)
except FileNotFoundError:
    print(f"Font file not found: {TETRIS_FONT_PATH}")
    sys.exit()

screen = pygame.display.set_mode((SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(GAME_CAPTION)
clock = pygame.time.Clock()

subwindow_visible = True
last_click_time = 0

# Global variables for in-game buttons and sound bar (subwindow coordinates)
restart_button_rect = None
menu_button_rect = None
skip_button_rect = None  # Only if custom music is enabled
sound_bar_rect = None
game_command = None  # "restart" or "menu" when a button is clicked

import os, json, pygame

# -------------------------- Settings System --------------------------

import os, json, pygame

def load_settings(filename="settings.json"):
    """Loads game settings from a JSON file, ensuring all required keys exist."""
    default_settings = {
        "controls": {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "down": pygame.K_DOWN,
            "rotate": pygame.K_UP,
            "pause": pygame.K_p,
            "hard_drop": pygame.K_SPACE,
            "hold": pygame.K_c,
            "skip_track": pygame.K_x
        },
        "controller_controls": {
            "left": 14,
            "right": 15,
            "down": 13,
            "rotate": 0,
            "hard_drop": 1,
            "hold": 2,
            "pause": 3,
            "skip_track": 4
        },
        "controller_menu_navigation": {
            "up": 11,
            "down": 12,
            "select": 0,
            "back": 1
        },
        # New key for controller behavior settings:
        "controller_settings": {
            "analog_threshold": 0.5,
            "joy_delay": 150,
            "hat_threshold": 0.5
        },
        "difficulty": "normal",
        "flame_trails": True,
        "grid_color": [200, 200, 200],
        "grid_opacity": 255,
        "grid_lines": True,
        "ghost_piece": True,
        "music_enabled": True,
        "use_custom_music": False,
        "music_directory": ""
    }

    if not os.path.exists(filename):
        save_settings(default_settings, filename)
        return default_settings

    try:
        with open(filename, "r") as file:
            saved_settings = json.load(file)

        # Ensure required keys exist.
        saved_settings.setdefault("controls", {})
        saved_settings.setdefault("controller_controls", default_settings["controller_controls"])
        saved_settings.setdefault("controller_menu_navigation", default_settings["controller_menu_navigation"])
        saved_settings.setdefault("controller_settings", default_settings["controller_settings"])

        # For controller_controls and menu navigation, ensure no key is left as None.
        for key, default_val in default_settings["controller_controls"].items():
            if saved_settings["controller_controls"].get(key) is None:
                saved_settings["controller_controls"][key] = default_val
        for key, default_val in default_settings["controller_menu_navigation"].items():
            if saved_settings["controller_menu_navigation"].get(key) is None:
                saved_settings["controller_menu_navigation"][key] = default_val
        for key, default_val in default_settings["controller_settings"].items():
            if saved_settings["controller_settings"].get(key) is None:
                saved_settings["controller_settings"][key] = default_val

        # Convert string keys back to pygame key constants for keyboard controls.
        for key, default_value in default_settings["controls"].items():
            if key in saved_settings["controls"]:
                val = saved_settings["controls"][key]
                if isinstance(val, str):
                    try:
                        saved_settings["controls"][key] = pygame.key.key_code(val.lower())
                    except KeyError:
                        print(f"Warning: Unrecognized key '{val}' in settings. Resetting to default.")
                        saved_settings["controls"][key] = default_value
                elif not isinstance(val, int):
                    saved_settings["controls"][key] = default_value
            else:
                saved_settings["controls"][key] = default_value

        # Ensure every key from default_settings exists.
        for key, default_value in default_settings.items():
            if key not in saved_settings:
                saved_settings[key] = default_value

        return saved_settings

    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading settings ({e}), using defaults.")
        return default_settings

def save_settings(settings, filename="settings.json"):
    """Saves the game settings to a JSON file."""
    try:
        settings_to_save = {
            "controls": {control: pygame.key.name(key).upper() for control, key in settings["controls"].items()},
            "controller_controls": {control: settings["controller_controls"].get(control) for control in settings.get("controller_controls", {})},
            "controller_menu_navigation": {control: settings["controller_menu_navigation"].get(control) for control in settings.get("controller_menu_navigation", {})},
            "controller_settings": settings.get("controller_settings", {}),
            "difficulty": settings.get("difficulty", "normal"),
            "flame_trails": settings.get("flame_trails", True),
            "grid_color": settings.get("grid_color", [200, 200, 200]),
            "grid_opacity": settings.get("grid_opacity", 255),
            "grid_lines": settings.get("grid_lines", True),
            "ghost_piece": settings.get("ghost_piece", True),
            "music_enabled": settings.get("music_enabled", True),
            "use_custom_music": settings.get("use_custom_music", False),
            "music_directory": settings.get("music_directory", "")
        }

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
                                                         
# -------------------------- Joystick Initialization --------------------------
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

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

# ---------- FIXED draw_3d_grid (using full opacity value and thicker lines) ----------
def draw_3d_grid(grid_surface, grid_color, grid_opacity):
    if not settings.get('grid_lines', True):
        grid_surface.fill((0, 0, 0, 0))
        return
    grid_surface.fill((0, 0, 0, 0))
    alpha_color = (grid_color[0], grid_color[1], grid_color[2], grid_opacity)
    thickness = 2  # Thicker grid lines
    for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
        pygame.draw.line(grid_surface, alpha_color, (x, 0), (x, SCREEN_HEIGHT), thickness)
    for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
        pygame.draw.line(grid_surface, alpha_color, (0, y), (SCREEN_WIDTH, y), thickness)
    pygame.draw.line(grid_surface, alpha_color, (SCREEN_WIDTH - 1, 0), (SCREEN_WIDTH - 1, SCREEN_HEIGHT), thickness)

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
                if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT or (y >= 0 and grid[y][x]):
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
        if len(full_lines) == 4 and multiple_line_clear_sound:
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

def draw_subwindow(score, next_tetromino, level, pieces_dropped, lines_cleared_total,
                   is_tetris=False, tetris_last_flash=0, tetris_flash_time=2000):
    global restart_button_rect, menu_button_rect, skip_button_rect, sound_bar_rect
    subwindow = pygame.Surface((SUBWINDOW_WIDTH, SCREEN_HEIGHT))
    subwindow.fill(BLACK)
    
    # --- Game Info Section ---
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
    
    # --- Next Tetromino Section ---
    next_label = tetris_font_small.render("Next:", True, WHITE)
    subwindow.blit(next_label, (10, 160))
    if next_tetromino:
        start_x = 10
        start_y = 180
        # Use get_shape_index() to get the correct shape index.
        shape_index = get_shape_index(next_tetromino)
        if shape_index is None:
            shape_index = 0
        color_index = (shape_index + level - 1) % len(COLORS) + 1
        for row_idx, row in enumerate(next_tetromino):
            for col_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(subwindow, COLORS[color_index - 1],
                                     (start_x + col_idx * BLOCK_SIZE,
                                      start_y + row_idx * BLOCK_SIZE,
                                      BLOCK_SIZE, BLOCK_SIZE))
    
    # --- Separator Line ---
    separator_y = 180 + 4 * BLOCK_SIZE + 10  # Adjust based on next piece display height
    pygame.draw.line(subwindow, WHITE, (10, separator_y), (SUBWINDOW_WIDTH - 10, separator_y), 2)
    
    # --- Hold Section (Placed Under Next) ---
    hold_label = tetris_font_small.render("Hold:", True, WHITE)
    hold_y = separator_y + 10
    subwindow.blit(hold_label, (10, hold_y))
    if hold_piece is not None:
        start_x = 10
        start_y = hold_y + 20
        # Use get_shape_index() for the hold piece as well.
        shape_index = get_shape_index(hold_piece)
        if shape_index is None:
            shape_index = 0
        color_index = (shape_index + level - 1) % len(COLORS) + 1
        for row_idx, row in enumerate(hold_piece):
            for col_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(subwindow, COLORS[color_index - 1],
                                     (start_x + col_idx * BLOCK_SIZE,
                                      start_y + row_idx * BLOCK_SIZE,
                                      BLOCK_SIZE, BLOCK_SIZE))
    else:
        placeholder = tetris_font_small.render("-", True, WHITE)
        subwindow.blit(placeholder, (10, hold_y + 20))
    
    # --- Tetris Flash ---
    if is_tetris:
        time_since_flash = pygame.time.get_ticks() - tetris_last_flash
        if time_since_flash < tetris_flash_time:
            flashing_color = random.choice(COLORS)
            flash_text = tetris_font_medium.render("TetraFusion!", True, flashing_color)
            text_x = (SUBWINDOW_WIDTH - flash_text.get_width()) // 2
            text_y = SCREEN_HEIGHT - 240
            subwindow.blit(flash_text, (text_x, text_y))
    
    # --- Sound Bar ---
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
    pygame.draw.rect(subwindow, (0, 200, 0), (bar_x, bar_y, fill_width, bar_height))
    
    # --- Buttons ---
    if settings.get('use_custom_music', False):
        # If custom music is ON, we show 3 buttons: Restart, Skip, Main Menu
        btn_space = 40
        button_width = (SUBWINDOW_WIDTH - btn_space) // 3
        button_y = SCREEN_HEIGHT - 60
        
        restart_button_rect = pygame.Rect(10, button_y, button_width, 30)
        skip_button_rect = pygame.Rect(20 + button_width, button_y, button_width, 30)
        menu_button_rect = pygame.Rect(30 + 2 * button_width, button_y, button_width, 30)
        pygame.draw.rect(subwindow, (50, 50, 200), restart_button_rect)
        restart_text = tetris_font_small.render("Restart", True, WHITE)
        subwindow.blit(restart_text, (
            restart_button_rect.x + (restart_button_rect.width - restart_text.get_width()) // 2,
            restart_button_rect.y + (restart_button_rect.height - restart_text.get_height()) // 2))
        pygame.draw.rect(subwindow, (200, 200, 50), skip_button_rect)
        skip_text = tetris_font_smaller.render("Skip Track", True, WHITE)
        subwindow.blit(skip_text, (
            skip_button_rect.x + (skip_button_rect.width - skip_text.get_width()) // 2,
            skip_button_rect.y + (skip_button_rect.height - skip_text.get_height()) // 2))
        pygame.draw.rect(subwindow, (200, 50, 50), menu_button_rect)
        menu_text = tetris_font_small.render("Main Menu", True, WHITE)
        subwindow.blit(menu_text, (
            menu_button_rect.x + (menu_button_rect.width - menu_text.get_width()) // 2,
            menu_button_rect.y + (menu_button_rect.height - menu_text.get_height()) // 2))
    else:
        # If custom music is OFF, we show 2 buttons: Restart, Main Menu
        button_width = (SUBWINDOW_WIDTH - 30) // 2
        button_y = SCREEN_HEIGHT - 60
        
        restart_button_rect = pygame.Rect(10, button_y, button_width, 30)
        menu_button_rect    = pygame.Rect(20 + button_width, button_y, button_width, 30)
        skip_button_rect    = None  # Not used in this mode
        
        pygame.draw.rect(subwindow, (50, 50, 200), restart_button_rect)
        restart_text = tetris_font_small.render("Restart", True, WHITE)
        subwindow.blit(restart_text, (
            restart_button_rect.x + (restart_button_rect.width - restart_text.get_width()) // 2,
            restart_button_rect.y + (restart_button_rect.height - restart_text.get_height()) // 2))
        pygame.draw.rect(subwindow, (200, 50, 50), menu_button_rect)
        menu_text = tetris_font_small.render("Main Menu", True, WHITE)
        subwindow.blit(menu_text, (
            menu_button_rect.x + (menu_button_rect.width - menu_text.get_width()) // 2,
            menu_button_rect.y + (menu_button_rect.height - menu_text.get_height()) // 2))
    
    # Finally, draw the subwindow onto the main screen
    screen.blit(subwindow, (SCREEN_WIDTH, 0))

# ---------- Updated Ghost Piece with Color Option ----------
def draw_ghost_piece(tetromino, offset, grid, color):
    if not settings.get('ghost_piece', True):
        return

    # Determine the landing position by dropping the tetromino until it can no longer move down.
    ghost_y = offset[1]
    while valid_position(tetromino, [offset[0], ghost_y + 1], grid):
        ghost_y += 1
    ghost_offset = [offset[0], ghost_y]
    ghost_fill_alpha = int(255 * 0.2)   # 20% opacity fill
    ghost_outline_alpha = int(255 * 0.4)  # 40% opacity outline
    border_thickness = 2
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                x = (ghost_offset[0] + cx) * BLOCK_SIZE
                y = (ghost_offset[1] + cy) * BLOCK_SIZE
                ghost_block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                ghost_block.fill((color[0], color[1], color[2], ghost_fill_alpha))
                pygame.draw.rect(ghost_block, (color[0], color[1], color[2], ghost_outline_alpha),
                                 (0, 0, BLOCK_SIZE, BLOCK_SIZE), border_thickness)
                screen.blit(ghost_block, (x, y))

    # Overlay the shadow on supported cells.
    draw_shadow_reflection(tetromino, ghost_offset, grid)


# -------------------------- Shadow Reflection --------------------------
def draw_shadow_reflection(tetromino, ghost_offset, grid):
    # Set a very transparent shadow.
    shadow_alpha = 10  # Lower value = more transparent.
    shadow_color = (30, 30, 30)  # Dark shadow color.

    # For each cell in the tetromino, determine if it is "supported"
    # (i.e. its cell below is either the floor or occupied by a placed block).
    # If so, draw a shadow overlay on that cell.
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:
                gx = ghost_offset[0] + cx
                gy = ghost_offset[1] + cy

                # Check if this ghost cell is supported:
                is_on_floor = (gy == GRID_HEIGHT - 1)
                is_supported = (gy + 1 < GRID_HEIGHT and grid[gy + 1][gx] != 0)
                if is_on_floor or is_supported:
                    x = gx * BLOCK_SIZE
                    y = gy * BLOCK_SIZE
                    shadow_block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                    shadow_block.fill((shadow_color[0], shadow_color[1], shadow_color[2], shadow_alpha))
                    screen.blit(shadow_block, (x, y))

# -------------------------- Custom Music Functions --------------------------
def play_custom_music(settings):
    global custom_music_playlist, current_track_index, last_track_index
    if not settings.get('music_enabled', True):
        pygame.mixer.music.stop()
        return

    update_custom_music_playlist(settings)
    
    # Restore a previously saved track index if applicable; otherwise, start at 0.
    if settings.get('use_custom_music', False) and last_track_index is not None and last_track_index < len(custom_music_playlist):
        current_track_index = last_track_index
    else:
        current_track_index = 0

    if custom_music_playlist:
        track = custom_music_playlist[current_track_index]
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(1.0)  # Set volume to 100%
            pygame.mixer.music.play(0)  # Play once so MUSIC_END_EVENT fires when the track ends.
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        except Exception as e:
            print(f"Error playing custom music: {e}")
    else:
        # Fallback: if no custom music files are found, load default background music.
        print("No music files found in the selected directory; loading default background music.")
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
            pygame.mixer.music.set_volume(1.0)  # Set volume to 100%
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading default background music: {e}")

def load_next_track(update_last_index=False):
    global current_track_index, last_track_index
    # Increment track index cyclically.
    current_track_index = (current_track_index + 1) % len(custom_music_playlist)
    try:
        pygame.mixer.music.load(custom_music_playlist[current_track_index])
        pygame.mixer.music.play(0)  # Play once so MUSIC_END_EVENT fires when the track ends.
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        if update_last_index:
            last_track_index = current_track_index
    except Exception as e:
        print(f"Error loading next track: {e}")

def skip_current_track():
    # If music is disabled, do nothing.
    if not settings.get('music_enabled', True):
        return
    if custom_music_playlist:
        load_next_track(update_last_index=True)

def stop_music():
    pygame.mixer.music.stop()
    
def handle_music_end_event():
    if settings.get('use_custom_music', False) and custom_music_playlist:
        load_next_track(update_last_index=False)

# -------------------------- Menu System --------------------------
def draw_main_menu(selected_index, menu_options):
    """
    Draws the main menu screen with a title and a list of selectable options.
    The option at index 'selected_index' is highlighted.
    """
    screen.fill(BLACK)
    title_text = tetris_font_large.render("TetraFusion", True, random.choice(COLORS))
    # Draw title above the menu options.
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//3 - 100))
    # Draw each menu option.
    for i, option in enumerate(menu_options):
        color = RED if i == selected_index else WHITE
        option_text = tetris_font_medium.render(option, True, color)
        x = SCREEN_WIDTH//2 - option_text.get_width()//2
        y = SCREEN_HEIGHT//2 + i * 50
        screen.blit(option_text, (x, y))
    pygame.display.flip()

def main_menu():
    global game_command
    # Start background music if enabled.
    if settings.get('music_enabled', True):
        if settings.get('use_custom_music', False):
            # If custom music is enabled, start it if not already playing.
            if not pygame.mixer.music.get_busy():
                play_custom_music(settings)
        else:
            # Otherwise, load and loop the default background music.
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                    pygame.mixer.music.set_volume(1.0)  # Set volume to 100%
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                except Exception as e:
                    print(f"Error loading default background music: {e}")
                    
    # Define the menu options.
    menu_options = ["Start", "Options", "Quit"]
    selected_index = 0
    joy_delay = 150  # milliseconds delay for joystick hat input
    last_move = pygame.time.get_ticks()
    
    # Optional: a flag to prevent repeated fallback triggers
    fallback_triggered = False

    while True:
        draw_main_menu(selected_index, menu_options)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type == MUSIC_END_EVENT:
                handle_music_end_event()
            # --- Keyboard Input ---
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected_index = (selected_index + 1) % len(menu_options)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected_index = (selected_index - 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    if menu_options[selected_index] == "Start":
                        return  # Exit menu and start game
                    elif menu_options[selected_index] == "Options":
                        options_menu()
                    elif menu_options[selected_index] == "Quit":
                        save_settings(settings)
                        pygame.quit()
                        sys.exit()
                elif event.key == pygame.K_o:
                    options_menu()
                elif event.key == pygame.K_ESCAPE:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
            # --- Controller Navigation using controller_menu_navigation settings ---
            elif event.type == pygame.JOYBUTTONDOWN:
                nav = settings.get("controller_menu_navigation", {})
                up_btn = nav.get("up")
                down_btn = nav.get("down")
                select_btn = nav.get("select")
                # Check if the pressed button matches one of our navigation bindings.
                if up_btn is not None and event.button == up_btn:
                    selected_index = (selected_index - 1) % len(menu_options)
                elif down_btn is not None and event.button == down_btn:
                    selected_index = (selected_index + 1) % len(menu_options)
                elif select_btn is not None and event.button == select_btn:
                    if menu_options[selected_index] == "Start":
                        return
                    elif menu_options[selected_index] == "Options":
                        options_menu()
                    elif menu_options[selected_index] == "Quit":
                        save_settings(settings)
                        pygame.quit()
                        sys.exit()
            # --- Optional: D-Pad (Hat) Navigation ---
            elif event.type == pygame.JOYHATMOTION:
                hx, hy = event.value
                if hy == 1:
                    selected_index = (selected_index - 1) % len(menu_options)
                elif hy == -1:
                    selected_index = (selected_index + 1) % len(menu_options)
        
        # Fallback for Custom Music Looping:
        if settings.get('use_custom_music', False):
            if not pygame.mixer.music.get_busy() and not fallback_triggered:
                fallback_triggered = True  # Mark that fallback has been triggered.
                load_next_track(update_last_index=False)
            elif pygame.mixer.music.get_busy():
                # Reset the flag when music is playing normally.
                fallback_triggered = False

        # Additionally, handle the skip command:
        if game_command == "skip":
            skip_current_track()
            game_command = None

        clock.tick(30)

# Main Options
def options_menu():
    global settings, last_track_index
    selected_option = 0
    enter_pressed = False  # Flag to track whether Enter is held down
    options = [
        ('keybinds', 'Keyboard Keybinds'),
        ('controller_keybinds', 'Controller Keybinds'),
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

    # Define vertical spacing for options and desired extra bottom padding.
    option_spacing = 45
    extra_bottom_padding = 0

    # Total height = (number of options * spacing) + extra bottom padding
    total_options_height = (len(options) * option_spacing) + extra_bottom_padding

    # Calculate base_y so that the list is vertically centered.
    base_y = (SCREEN_HEIGHT - total_options_height) // 2

    # --- Sub-Function: process_navigation_events ---
    def process_navigation_events(options, selected_option, changing_key, enter_pressed):
        """
        Processes both keyboard and controller (including D-pad) navigation events
        for the options menu. Returns updated values for selected_option, changing_key,
        enter_pressed, and an action flag (which will be the current option key if selected,
        or "back" if the user wants to exit).
        """
        action = None  # Action flag to indicate an option was chosen.
        for event in pygame.event.get():
            # ---------------------- QUIT EVENT ----------------------
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            # ---------------------- MUSIC END EVENT ----------------------
            elif event.type == MUSIC_END_EVENT:
                handle_music_end_event()
            # ---------------------- CONTROLLER EVENTS (JOYBUTTONDOWN) ----------------------
            elif event.type == pygame.JOYBUTTONDOWN:
                if changing_key is None:  # Only process navigation if not capturing a new key binding.
                    nav = settings.get("controller_menu_navigation", {})
                    up_btn = nav.get("up")
                    down_btn = nav.get("down")
                    select_btn = nav.get("select")
                    back_btn = nav.get("back")
                    if up_btn is not None and event.button == up_btn:
                        selected_option = (selected_option - 1) % len(options)
                    elif down_btn is not None and event.button == down_btn:
                        selected_option = (selected_option + 1) % len(options)
                    elif select_btn is not None and event.button == select_btn:
                        current_key = options[selected_option][0]
                        # For options that capture keyboard bindings, ignore controller select.
                        if current_key not in settings['controls']:
                            action = current_key
                    elif back_btn is not None and event.button == back_btn:
                        action = "back"
            # ---------------------- D-PAD (JOYHATMOTION) NAVIGATION ----------------------
            elif event.type == pygame.JOYHATMOTION:
                if changing_key is None:
                    hx, hy = event.value
                    if hy == 1:
                        selected_option = (selected_option - 1) % len(options)
                    elif hy == -1:
                        selected_option = (selected_option + 1) % len(options)
            # ---------------------- KEYBOARD EVENTS (NAVIGATION & BINDING) ----------------------
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if changing_key is not None:
                        changing_key = None  # Cancel pending binding capture.
                    else:
                        action = "back"
                elif changing_key is not None:
                    # When capturing a new key binding, only keyboard keys are processed.
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                elif event.key == pygame.K_RETURN and not enter_pressed:
                    enter_pressed = True  # Mark Enter as pressed.
                    current_key = options[selected_option][0]
                    if current_key in settings['controls']:
                        # Begin capturing a new keyboard binding.
                        changing_key = current_key
                    else:
                        action = current_key
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RETURN:
                    enter_pressed = False
        return selected_option, changing_key, enter_pressed, action

    # ---------------------- MAIN LOOP FOR OPTIONS MENU ----------------------
    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Options", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        
        # Render each option.
        for i, (key, label) in enumerate(options):
            color = RED if i == selected_option else WHITE
            text = label
            if key in settings['controls']:
                text = f"{label}: {pygame.key.name(settings['controls'][key]).upper()}"
            elif key == 'difficulty':
                text = f"Difficulty: {settings['difficulty'].capitalize()}"
            elif key == 'flame_trails':
                text = f"Flame Trails: {'On' if settings['flame_trails'] else 'Off'}"
            elif key == 'grid_opacity':
                text = f"Grid Opacity: {settings['grid_opacity']}"
            elif key == 'grid_lines':
                text = f"Grid Lines: {'On' if settings.get('grid_lines', True) else 'Off'}"
            elif key == 'ghost_piece':
                text = f"Ghost Piece: {'On' if settings.get('ghost_piece', True) else 'Off'}"
            elif key == 'music_enabled':
                text = f"Music: {'On' if settings.get('music_enabled', True) else 'Off'}"
            elif key == 'use_custom_music':
                text = f"Use Custom Music: {'On' if settings.get('use_custom_music', False) else 'Off'}"
            elif key == 'select_music_dir':
                dir_display = settings.get('music_directory', '')
                text = f"Dir: {dir_display}" if dir_display else "Music Dir: Not Selected"
            option_text = tetris_font_medium.render(text, True, color)
            # Scale the text for select_music_dir based on whether a valid path is set.
            if key == 'select_music_dir':
                if settings.get('music_directory', ''):
                    scale_factor = 0.6  # When a valid music directory is set.
                else:
                    scale_factor = 1.0  # When no valid music directory is set.
                scaled_width = int(option_text.get_width() * scale_factor)
                scaled_height = int(option_text.get_height() * scale_factor)
                option_text = pygame.transform.scale(option_text, (scaled_width, scaled_height))
            y_coordinate = base_y + i * option_spacing
            screen.blit(option_text, (SCREEN_WIDTH // 2 - option_text.get_width() // 2, y_coordinate))
        
        pygame.display.flip()

        # Call the navigation sub-function to process events.
        selected_option, changing_key, enter_pressed, action = process_navigation_events(
            options, selected_option, changing_key, enter_pressed
        )
        # Process the returned action flag.
        if action is not None:
            current_key = action
            if current_key == 'keybinds':
                keyboard_keybinds_menu()
                pygame.event.clear()
            elif current_key == 'controller_keybinds':
                controller_keybinds_menu()
                pygame.event.clear()
            elif current_key == 'difficulty':
                difficulties = ['easy', 'normal', 'hard', 'very hard']
                new_idx = (difficulties.index(settings['difficulty']) + 1) % len(difficulties)
                settings['difficulty'] = difficulties[new_idx]
            elif current_key == 'flame_trails':
                settings['flame_trails'] = not settings['flame_trails']
            elif current_key == 'grid_opacity':
                if settings['grid_opacity'] < 255:
                    new_opacity = settings['grid_opacity'] + 64
                    settings['grid_opacity'] = new_opacity if new_opacity <= 255 else 255
                else:
                    settings['grid_opacity'] = 0
            elif current_key == 'grid_lines':
                settings['grid_lines'] = not settings.get('grid_lines', True)
            elif current_key == 'ghost_piece':
                settings['ghost_piece'] = not settings.get('ghost_piece', True)
            elif current_key == 'music_enabled':
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
            elif current_key == 'use_custom_music':
                settings['use_custom_music'] = not settings.get('use_custom_music', False)
                last_track_index = None
                if settings.get('music_enabled', True):
                    if settings.get('use_custom_music', False):
                        play_custom_music(settings)
                    else:
                        try:
                            pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                            pygame.mixer.music.play(-1)
                        except Exception as e:
                            print(f"Error loading default background music: {e}")
                else:
                    stop_music()
            elif current_key == 'select_music_dir':
                selected_dir = select_music_directory()
                if selected_dir:
                    settings['music_directory'] = selected_dir
                    last_track_index = None
                    if settings.get('use_custom_music', False) and settings.get('music_enabled', True):
                        play_custom_music(settings)
            elif current_key == 'back':
                save_settings(settings)
                return

# Options Keyboard Controls            
def keyboard_keybinds_menu():
    selected_option = 0
    changing_key = None
    enter_pressed = False  # Flag to track whether Enter is held down

    # Ensure the music skip key is available.
    if 'skip_track' not in settings['controls']:
        settings['controls']['skip_track'] = pygame.K_x

    # List of keybind options: first element is the setting key,
    # second element is a label to show.
    keybind_options = [
        ('left', 'Move Left'),
        ('right', 'Move Right'),
        ('down', 'Soft Drop'),
        ('rotate', 'Rotate'),
        ('hard_drop', 'Hard Drop'),
        ('hold', 'Hold Piece'),
        ('pause', 'Pause'),
        ('skip_track', 'Skip Track'),
        ('back', 'Back to Options')
    ]
    option_spacing = 45
    base_y = 150  # starting vertical position

    # --- Sub-Function: process_kb_nav_events ---
    def process_kb_nav_events(options, selected_option, changing_key, enter_pressed):
        """
        Processes both keyboard and controller (including D-pad) navigation events
        for the keyboard keybinds menu. Returns updated values for selected_option,
        changing_key, enter_pressed, and an action flag.
        
        NOTE:
          - This menu supports full controller navigation so that you can move up and down
            and use the controller "back" button to exit.
          - When the controller's select button is pressed on a bindable option,
            binding capture is triggered (changing_key is set) so that subsequent controller keys
            will not bind anything; only a keyboard key will be accepted.
          - The action flag will be "back" if the user wants to exit, or None otherwise.
        """
        action = None  # Will hold the action if one is triggered.
        # ---------------------- Process Each Event ----------------------
        for event in pygame.event.get():
            # ---------------------- QUIT EVENT ----------------------
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            # ---------------------- MUSIC END EVENT ----------------------
            elif event.type == MUSIC_END_EVENT:
                handle_music_end_event()
            # ---------------------- CONTROLLER EVENTS (JOYBUTTONDOWN) ----------------------
            elif event.type == pygame.JOYBUTTONDOWN:
                # Only process controller navigation if NOT in binding mode.
                if changing_key is None:
                    nav = settings.get("controller_menu_navigation", {})
                    up_btn = nav.get("up")
                    down_btn = nav.get("down")
                    select_btn = nav.get("select")
                    back_btn = nav.get("back")
                    if up_btn is not None and event.button == up_btn:
                        selected_option = (selected_option - 1) % len(options)
                    elif down_btn is not None and event.button == down_btn:
                        selected_option = (selected_option + 1) % len(options)
                    # Controller Back button exits the menu.
                    elif back_btn is not None and event.button == back_btn:
                        action = "back"
                    # Controller Select triggers binding mode for bindable options.
                    elif select_btn is not None and event.button == select_btn:
                        current_key = options[selected_option][0]
                        if current_key == "back":
                            action = "back"
                        else:
                            # Trigger binding capture if this option is bindable.
                            if current_key in settings['controls']:
                                changing_key = current_key
            # ---------------------- D-PAD (JOYHATMOTION) NAVIGATION ----------------------
            elif event.type == pygame.JOYHATMOTION:
                if changing_key is None:
                    hx, hy = event.value
                    if hy == 1:
                        selected_option = (selected_option - 1) % len(options)
                    elif hy == -1:
                        selected_option = (selected_option + 1) % len(options)
            # ---------------------- KEYBOARD EVENTS (NAVIGATION & BINDING) ----------------------
            elif event.type == pygame.KEYDOWN:
                # ESC cancels binding capture or exits the menu.
                if event.key == pygame.K_ESCAPE:
                    if changing_key is not None:
                        changing_key = None  # Cancel pending binding
                    else:
                        action = "back"
                # If waiting for a new key, capture the key press (keyboard only).
                elif changing_key is not None:
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                # Process selection with Enter (keyboard only).
                elif event.key == pygame.K_RETURN and not enter_pressed:
                    enter_pressed = True  # Mark Enter as pressed.
                    current_key = options[selected_option][0]
                    if current_key == 'back':
                        action = "back"
                    else:
                        # Begin capturing a new binding for this option (keyboard only).
                        changing_key = current_key
                # Navigate using Up arrow.
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                # Navigate using Down arrow.
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
            # ---------------------- KEYUP EVENT ----------------------
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RETURN:
                    enter_pressed = False  # Reset flag when Enter is released
        return selected_option, changing_key, enter_pressed, action

    # ---------------------- MAIN LOOP FOR KEYBOARD KEYBINDS MENU ----------------------
    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Keyboard Keybinds", True, WHITE)
        scaled_title = pygame.transform.scale(
            title_text,
            (int(title_text.get_width() * 0.8), int(title_text.get_height() * 0.8))
        )
        screen.blit(
            scaled_title,
            (SCREEN_WIDTH // 2 - scaled_title.get_width() // 2, 50)
        )
    
        # Render each keybind option.
        for i, (key, label) in enumerate(keybind_options):
            # Decide the overall color for the label (red if selected, else white).
            color = RED if i == selected_option else WHITE
        
            # Y-position for this line
            y_coordinate = base_y + i * option_spacing
            x_center = SCREEN_WIDTH // 2  # We'll center things horizontally

            # If key is in our controls dict, we do two-part rendering: label + key
            if key in settings['controls']:
                # 1) Label portion
                label_text = label + ": "
                label_surface = tetris_font_medium.render(label_text, True, color)

                # 2) Key portion - if we are capturing a binding (changing_key == key), show it in yellow
                if changing_key == key:
                    key_color = YELLOW
                else:
                    key_color = color

                key_name = pygame.key.name(settings['controls'][key]).upper()
                key_surface = tetris_font_medium.render(key_name, True, key_color)

                # Now blit them side by side (still centered as a whole).
                combined_width = label_surface.get_width() + key_surface.get_width()
                x_start = x_center - combined_width // 2
                screen.blit(label_surface, (x_start, y_coordinate))
                screen.blit(key_surface, (x_start + label_surface.get_width(), y_coordinate))

            else:
                # If it's not actually in settings['controls'], just render a single label.
                display_text = label
                option_text = tetris_font_medium.render(display_text, True, color)
                screen.blit(
                    option_text,
                    (x_center - option_text.get_width() // 2, y_coordinate)
                )
    
        pygame.display.flip()

        # Call the navigation sub-function to process events.
        selected_option, changing_key, enter_pressed, action = process_kb_nav_events(
            keybind_options, selected_option, changing_key, enter_pressed
        )

        # Process any action returned from the sub-function.
        if action is not None:
            if action == "back":
                return

# Options Controller Controls         
def controller_keybinds_menu():
    selected_option = 0
    changing_button = None
    enter_pressed = False  # Flag to track whether Enter is held down

    # Ensure that a controller_controls dictionary exists in settings.
    if 'controller_controls' not in settings:
        settings['controller_controls'] = {
            'left': 14,
            'right': 15,
            'down': 13,
            'rotate': 0,
            'hard_drop': 1,
            'hold': 2,
            'pause': 3,
            'skip_track': 4
        }

    # Define your controller options.
    controller_options = [
        ('controller_menu_keybinds', 'Menu Nav Bindings'),
        ('left', 'Move Left'),
        ('right', 'Move Right'),
        ('down', 'Soft Drop'),
        ('rotate', 'Rotate'),
        ('hard_drop', 'Hard Drop'),
        ('hold', 'Hold Piece'),
        ('pause', 'Pause'),
        ('back', 'Back to Options')
    ]
    
    # Define which options are bindable in controller_controls.
    bindable_keys = {"left", "right", "down", "rotate", "hard_drop", "hold", "pause", "skip_track"}

    option_spacing = 45
    base_y = 150  # starting vertical position for options

    def process_ctrl_nav_events(options, selected_option, changing_button, enter_pressed):
        action = None  # Will hold the action if one is triggered.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type == MUSIC_END_EVENT:
                handle_music_end_event()
            # When in binding mode, capture not only button presses but also hat and axis events.
            elif changing_button is not None:
                if event.type == pygame.JOYBUTTONDOWN:
                    # Use the button value as usual.
                    settings['controller_controls'][changing_button] = event.button
                    changing_button = None
                elif event.type == pygame.JOYHATMOTION:
                    # If the hat has a non-zero value, store it as a tuple.
                    if event.value != (0, 0):
                        settings['controller_controls'][changing_button] = ("hat", event.value)
                        changing_button = None
                elif event.type == pygame.JOYAXISMOTION:
                    # For analog stick events, only capture if value exceeds a threshold.
                    analog_threshold = settings["controller_settings"].get("analog_threshold", 0.5)
                    if event.axis in (0, 1) and abs(event.value) >= analog_threshold:
                        direction = "positive" if event.value > 0 else "negative"
                        settings['controller_controls'][changing_button] = ("axis", event.axis, direction)
                        changing_button = None
            else:
                # Not in binding mode – process navigation.
                if event.type == pygame.JOYBUTTONDOWN:
                    nav = settings.get("controller_menu_navigation", {})
                    up_btn = nav.get("up")
                    down_btn = nav.get("down")
                    select_btn = nav.get("select")
                    back_btn = nav.get("back")
                    if up_btn is not None and event.button == up_btn:
                        selected_option = (selected_option - 1) % len(options)
                    elif down_btn is not None and event.button == down_btn:
                        selected_option = (selected_option + 1) % len(options)
                    elif back_btn is not None and event.button == back_btn:
                        action = "back"
                    elif select_btn is not None and event.button == select_btn:
                        current_option = options[selected_option][0]
                        if current_option == 'back':
                            action = "back"
                        else:
                            if current_option in settings['controller_controls']:
                                changing_button = current_option
                elif event.type == pygame.JOYHATMOTION:
                    hx, hy = event.value
                    if hy == 1:
                        selected_option = (selected_option - 1) % len(options)
                    elif hy == -1:
                        selected_option = (selected_option + 1) % len(options)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        action = "back"
                    elif event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(options)
                    elif event.key == pygame.K_RETURN and not enter_pressed:
                        enter_pressed = True
                        current_option = options[selected_option][0]
                        if current_option == 'back':
                            action = "back"
                        else:
                            if current_option in settings['controller_controls']:
                                changing_button = current_option
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_RETURN:
                        enter_pressed = False
        return selected_option, changing_button, enter_pressed, action

    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Controller Keybinds", True, WHITE)
        scaled_title = pygame.transform.scale(title_text, (int(title_text.get_width() * 0.8), int(title_text.get_height() * 0.8)))
        screen.blit(scaled_title, (SCREEN_WIDTH // 2 - scaled_title.get_width() // 2, 50))
    
        # Render each controller option.
        for i, (key, label) in enumerate(controller_options):
            color = RED if i == selected_option else WHITE
            y_coordinate = base_y + i * option_spacing
            x_center = SCREEN_WIDTH // 2
            if key in bindable_keys:
                label_text = label + ": "
                label_surface = tetris_font_medium.render(label_text, True, color)
                current_binding = settings['controller_controls'].get(key)
                if current_binding is None:
                    binding_str = "(none)"
                elif isinstance(current_binding, tuple):
                    # For hat or axis bindings, format them specially.
                    if current_binding[0] == "hat":
                        binding_str = f"Hat {current_binding[1]}"
                    elif current_binding[0] == "axis":
                        binding_str = f"Axis {current_binding[1]} {current_binding[2]}"
                    else:
                        binding_str = str(current_binding)
                else:
                    binding_str = f"Button {current_binding}"
                binding_color = YELLOW if changing_button == key else color
                binding_surface = tetris_font_medium.render(binding_str, True, binding_color)
                combined_width = label_surface.get_width() + binding_surface.get_width()
                x_start = x_center - (combined_width // 2)
                screen.blit(label_surface, (x_start, y_coordinate))
                screen.blit(binding_surface, (x_start + label_surface.get_width(), y_coordinate))
            else:
                option_text = tetris_font_medium.render(label, True, color)
                screen.blit(option_text, (x_center - option_text.get_width() // 2, y_coordinate))
    
        pygame.display.flip()
        selected_option, changing_button, enter_pressed, action = process_ctrl_nav_events(controller_options, selected_option, changing_button, enter_pressed)
        if action is not None:
            if action == "back":
                return
            elif action == "menu_nav":
                controller_menu_nav_menu()

# Options Controller Menu Keybinds
def controller_menu_nav_menu():
    selected_option = 0
    changing_button = None
    enter_pressed = False  # Flag to track whether Enter is held down

    # Ensure the "controller_menu_navigation" settings exist.
    if "controller_menu_navigation" not in settings:
        settings["controller_menu_navigation"] = {
            "up": None,
            "down": None,
            "left": None,
            "right": None,
            "select": None,
            "back": None
        }

    # Define menu navigation options.
    # The first four options are bindable; the final option ("exit") is non-bindable.
    menu_nav_options = [
        ("up", "Menu Up"),
        ("down", "Menu Down"),
        ("select", "Menu Select"),
        ("back", "Menu Back"),
        ("exit", "Back to Controller Keybinds")
    ]
    
    # Define which options are bindable.
    bindable_keys = {"up", "down", "select", "back"}

    option_spacing = 45
    base_y = 150  # Starting vertical position for the options

    # --- Sub-Function: process_menu_nav_events ---
    def process_menu_nav_events(options, selected_option, changing_button, enter_pressed):
        """
        Processes both keyboard and controller (including D-pad) navigation events
        for the controller menu navigation bindings menu. Returns updated values for 
        selected_option, changing_button, enter_pressed, and an action flag.
        
        NOTE:
          - In this menu, binding capture is triggered by Enter (keyboard) or the controller
            select button. However, once binding mode is active (i.e. changing_button is not None),
            only controller key inputs (JOYBUTTONDOWN) will update the binding in settings["controller_menu_navigation"].
          - Keyboard events are allowed for navigation but are not used to update the binding.
          - The action flag will be "exit" (or "back") if the user selects that option.
        """
        action = None  # Will hold the action if one is triggered.
        # ---------------------- Process Each Event ----------------------
        for event in pygame.event.get():
            # ---------------------- QUIT EVENT ----------------------
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            # ---------------------- MUSIC END EVENT ----------------------
            elif event.type == MUSIC_END_EVENT:
                handle_music_end_event()
            # ---------------------- CONTROLLER EVENTS (JOYBUTTONDOWN) ----------------------
            elif event.type == pygame.JOYBUTTONDOWN:
                if changing_button is not None:
                    # In binding mode: capture the controller button and update the binding.
                    settings["controller_menu_navigation"][changing_button] = event.button
                    changing_button = None
                else:
                    # Not in binding mode: process navigation via controller buttons.
                    # Lookup our controller navigation keys from settings.
                    nav = settings.get("controller_menu_navigation", {})
                    up_btn = nav.get("up")
                    down_btn = nav.get("down")
                    select_btn = nav.get("select")
                    back_btn = nav.get("back")
                    if up_btn is not None and event.button == up_btn:
                        selected_option = (selected_option - 1) % len(options)
                    elif down_btn is not None and event.button == down_btn:
                        selected_option = (selected_option + 1) % len(options)
                    elif back_btn is not None and event.button == back_btn:
                        action = "back"
                    elif select_btn is not None and event.button == select_btn:
                        current_option = options[selected_option][0]
                        if current_option == "exit":
                            action = "exit"
                        else:
                            # Trigger binding capture for this option if it is bindable.
                            if current_option in bindable_keys:
                                changing_button = current_option
            # ---------------------- D-PAD (JOYHATMOTION) NAVIGATION ----------------------
            elif event.type == pygame.JOYHATMOTION:
                if changing_button is None:
                    hx, hy = event.value
                    if hy == 1:
                        selected_option = (selected_option - 1) % len(options)
                    elif hy == -1:
                        selected_option = (selected_option + 1) % len(options)
            # ---------------------- KEYBOARD EVENTS (NAVIGATION) ----------------------
            elif event.type == pygame.KEYDOWN:
                # Keyboard navigation is allowed, but keyboard keys will not update the binding.
                if event.key == pygame.K_ESCAPE:
                    if changing_button is not None:
                        changing_button = None  # Cancel pending binding.
                    else:
                        action = "back"
                elif changing_button is None:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(options)
                    # Use Enter to trigger binding capture (keyboard can trigger, but binding update is done via controller).
                    elif event.key == pygame.K_RETURN and not enter_pressed:
                        enter_pressed = True
                        current_option = options[selected_option][0]
                        if current_option == "exit":
                            action = "exit"
                        else:
                            if current_option in bindable_keys:
                                changing_button = current_option
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RETURN:
                    enter_pressed = False
        return selected_option, changing_button, enter_pressed, action

    # ---------------------- MAIN LOOP FOR CONTROLLER MENU NAV KEYBINDS ----------------------
    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Menu Nav Bindings", True, WHITE)
        scaled_title = pygame.transform.scale(
            title_text,
            (int(title_text.get_width() * 0.8), int(title_text.get_height() * 0.8))
        )
        screen.blit(
            scaled_title,
            (SCREEN_WIDTH // 2 - scaled_title.get_width() // 2, 50)
        )
    
        # Render each menu navigation option.
        for i, (key, label) in enumerate(menu_nav_options):
            # Decide the overall color (red if selected, else white).
            color = RED if i == selected_option else WHITE
        
            y_coordinate = base_y + i * option_spacing
            x_center = SCREEN_WIDTH // 2
        
            if key in bindable_keys:
                # 1) Render the label part
                label_text = label + ": "
                label_surface = tetris_font_medium.render(label_text, True, color)
            
                # 2) Decide on the actual button text
                current_binding = settings["controller_menu_navigation"].get(key)
                if current_binding is not None:
                    binding_str = f"Button {current_binding}"
                else:
                    binding_str = "(none)"

                # If we're currently capturing this key's binding, make it yellow
                if changing_button == key:
                    binding_color = YELLOW
                else:
                    binding_color = color

                binding_surface = tetris_font_medium.render(binding_str, True, binding_color)

                # Combine side by side, still center as a whole
                combined_width = label_surface.get_width() + binding_surface.get_width()
                x_start = x_center - (combined_width // 2)
            
                # Blit
                screen.blit(label_surface, (x_start, y_coordinate))
                screen.blit(binding_surface, (x_start + label_surface.get_width(), y_coordinate))
        
            else:
                # Non-bindable option (e.g. "exit"). Render as a single string.
                display_text = label
                option_text = tetris_font_medium.render(display_text, True, color)
            
                # If this is the "exit" option, scale it as before.
                if key == "exit":
                    option_text = pygame.transform.scale(
                        option_text,
                        (int(option_text.get_width() * 0.85), int(option_text.get_height() * 0.85))
                    )
            
                screen.blit(
                    option_text,
                    (x_center - option_text.get_width() // 2, y_coordinate)
                )

        pygame.display.flip()

        # Process events and handle actions.
        selected_option, changing_button, enter_pressed, action = process_menu_nav_events(
            menu_nav_options, selected_option, changing_button, enter_pressed
        )
        if action is not None:
            if action == "exit" or action == "back":
                return

def pause_game():
    global settings
    pause_text = tetris_font_large.render("PAUSED", True, WHITE)
    paused = True
    pygame.event.clear(pygame.KEYDOWN)
    
    # Pause the music as soon as the game is paused
    pygame.mixer.music.pause()
    
    while paused:
        screen.fill(BLACK)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                # Unpause if the pause key (or Escape) is pressed on the keyboard.
                if event.key == settings['controls']['pause'] or event.key == pygame.K_ESCAPE:
                    paused = False
            elif event.type == pygame.JOYBUTTONDOWN:
                # Unpause if the controller's pause/back button is pressed.
                if settings.get('controller_controls', {}).get('pause') is not None and event.button == settings['controller_controls']['pause']:
                    paused = False

    # Unpause the music when the game is resumed.
    pygame.mixer.music.unpause()

def display_game_over(score):
    global high_score, high_score_name

    # ---------------- Helper Functions for Duplicate Logic ----------------
    def restart_game():
        if settings.get('music_enabled', True):
            if settings.get('use_custom_music', False):
                play_custom_music(settings)
            else:
                try:
                    pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                except Exception as e:
                    print(f"Error loading default background music: {e}")
        else:
            stop_music()
        run_game()

    def go_to_main_menu():
        main_menu()

    # ---------------- NEW HIGH SCORE BRANCH ----------------
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
                if event.type == pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and initials:
                        high_score = score
                        high_score_name = initials
                        save_high_score(high_score, high_score_name)
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        initials = initials[:-1]
                    elif len(initials) < 3 and event.unicode.isalnum():
                        initials += event.unicode.upper()
                    elif event.key == pygame.K_m:
                        go_to_main_menu()
                        return
                elif event.type == pygame.JOYBUTTONDOWN:
                    if settings.get("controller_menu_navigation"):
                        # Controller select acts like ENTER.
                        if event.button == settings["controller_menu_navigation"].get("select"):
                            if initials:
                                high_score = score
                                high_score_name = initials
                                save_high_score(high_score, high_score_name)
                                input_active = False
                        # Controller back acts like M (menu).
                        elif event.button == settings["controller_menu_navigation"].get("back"):
                            go_to_main_menu()
                            return
        # After saving the high score, restart the game.
        restart_game()
        return

    # ---------------- NORMAL GAME OVER BRANCH ----------------
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
                if event.type == pygame.QUIT:
                    save_settings(settings)
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        restart_game()
                        return
                    elif event.key == pygame.K_m:
                        go_to_main_menu()
                        return
                elif event.type == pygame.JOYBUTTONDOWN:
                    if settings.get("controller_menu_navigation"):
                        # Controller select acts as R (restart).
                        if event.button == settings["controller_menu_navigation"].get("select"):
                            restart_game()
                            return
                        # Controller back acts as M (menu).
                        elif event.button == settings["controller_menu_navigation"].get("back"):
                            go_to_main_menu()
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
    global hold_piece, hold_used  # Hold piece globals

    # Initialize joystick if available.
    joy = None
    if pygame.joystick.get_count() > 0:
        joy = pygame.joystick.Joystick(0)
        joy.init()

    # Reset hold state on game start.
    hold_piece = None
    hold_used = False
    game_command = None

    # Retrieve our key mapping settings.
    controls = settings['controls']              # Keyboard controls
    cc = settings.get('controller_controls', {})   # Controller controls mapping

    # Retrieve other settings.
    difficulty = settings['difficulty']
    flame_trails_enabled = settings['flame_trails']
    grid_color = tuple(settings['grid_color'])
    grid_opacity = settings.get('grid_opacity', 255)
    grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    draw_3d_grid(grid_surface, grid_color, grid_opacity)

    # Set up difficulty/fall speeds.
    difficulty_speeds = {
        'easy': 1500,
        'normal': 1000,
        'hard': 600,
        'very hard': 400
    }
    base_fall_speed = difficulty_speeds.get(difficulty, 1000)
    fall_speed = base_fall_speed

    # Initialize game variables.
    level = 1
    lines_cleared_total = 0
    pieces_dropped = 0
    trail_particles = []
    explosion_particles = []
    dust_particles = []
    screen_shake = 0
    grid = create_grid()
    tetromino_bag = TetrominoBag(SHAPES)
    tetromino = tetromino_bag.get_next_tetromino()
    next_tetromino = tetromino_bag.get_next_tetromino()
    shape_index = get_shape_index(tetromino)
    if shape_index is None:
        shape_index = 0
    color_index = (shape_index + level - 1) % len(COLORS) + 1
    offset = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
    score = 0
    fast_fall = False
    last_fall_time = pygame.time.get_ticks()
    game_over = False
    # These flags will be updated by events or polling:
    left_pressed = False
    right_pressed = False
    last_horizontal_move = pygame.time.get_ticks()
    move_interval = 150
    fast_move_interval = 50
    is_tetris = False
    tetris_flash_time = 2000
    tetris_last_flash = 0

    in_level_transition = False
    transition_start_time = 0
    TRANSITION_DURATION = 2000
    FLASH_INTERVAL = 100
    last_flash_time = pygame.time.get_ticks()
    flash_count = 0

    pygame.key.set_repeat(300, 100)
    last_joy_move = pygame.time.get_ticks()
    last_hat_move = pygame.time.get_ticks()  # For throttling D-Pad events

    # -------------------------- Helper Functions --------------------------

    def lock_and_update_tetromino(current_time):
        nonlocal tetromino, offset, score, game_over, grid, lines_cleared_total
        global hold_used
        nonlocal pieces_dropped, screen_shake, is_tetris, tetris_last_flash, level
        nonlocal fall_speed, transition_start_time, last_flash_time, flash_count
        nonlocal next_tetromino, shape_index, color_index, tetromino_bag
        hard_drop_rows = 0
        temp_offset = offset.copy()
        while valid_position(tetromino, [temp_offset[0], temp_offset[1] + 1], grid):
            temp_offset[1] += 1
            hard_drop_rows += 1
        offset[1] = temp_offset[1]
        score += hard_drop_rows * 2
        for _ in range(20 + hard_drop_rows * 5):
            dust_particles.append(DustParticle(
                (offset[0] + random.uniform(-1, len(tetromino[0]) + 1)) * BLOCK_SIZE,
                (offset[1] + len(tetromino)) * BLOCK_SIZE
            ))
        if check_game_over(grid):
            game_over = True
            return
        original_grid = [row[:] for row in grid]
        place_tetromino(tetromino, offset, grid, color_index)
        hold_used = False
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
                            x * BLOCK_SIZE + BLOCK_SIZE // 2,
                            y * BLOCK_SIZE + BLOCK_SIZE // 2,
                            COLORS[original_grid[y][x] - 1],
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
            fall_speed = max(50, int(base_fall_speed * (0.85 ** (level - 1))))
            nonlocal in_level_transition
            in_level_transition = True
            transition_start_time = current_time
            last_flash_time = current_time
            flash_count = 0
        tetromino = next_tetromino
        shape_index = get_shape_index(tetromino) or 0
        color_index = (shape_index + level - 1) % len(COLORS) + 1
        next_tetromino = tetromino_bag.get_next_tetromino()
        offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]

    def process_keyboard_events(events, current_time):
        nonlocal left_pressed, right_pressed, fast_fall, offset, tetromino, last_horizontal_move
        nonlocal shape_index, color_index, score, level, next_tetromino, tetromino_bag
        global game_command, hold_used, hold_piece
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls['left']:
                    left_pressed = True
                    new_x = offset[0] - 1
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                    last_horizontal_move = current_time
                elif event.key == controls['right']:
                    right_pressed = True
                    new_x = offset[0] + 1
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                    last_horizontal_move = current_time
                elif event.key == controls['down']:
                    fast_fall = True
                elif event.key == controls['rotate']:
                    rotated, new_offset = rotate_tetromino_with_kick(tetromino, offset, grid)
                    tetromino, offset = rotated, new_offset
                elif event.key == controls.get('hold', pygame.K_c):
                    if not hold_used:
                        hold_used = True
                        if hold_piece is None:
                            hold_piece = copy.deepcopy(tetromino)
                            tetromino = tetromino_bag.get_next_tetromino()
                            shape_index = get_shape_index(tetromino) or 0
                            color_index = (shape_index + level - 1) % len(COLORS) + 1
                            offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
                        else:
                            tetromino, hold_piece = copy.deepcopy(hold_piece), copy.deepcopy(tetromino)
                            shape_index = get_shape_index(tetromino) or 0
                            color_index = (shape_index + level - 1) % len(COLORS) + 1
                            offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
                elif event.key == controls['hard_drop']:
                    lock_and_update_tetromino(current_time)
                elif event.key == controls['pause']:
                    pause_game()
                elif controls.get('skip_track') and event.key == controls['skip_track']:
                    game_command = "skip"
            elif event.type == pygame.KEYUP:
                if event.key == controls['left']:
                    left_pressed = False
                elif event.key == controls['right']:
                    right_pressed = False
                elif event.key == controls['down']:
                    fast_fall = False

    def process_controller_events(events, current_time):
        nonlocal left_pressed, right_pressed, offset, tetromino, last_horizontal_move, fast_fall
        nonlocal shape_index, color_index, next_tetromino, tetromino_bag, last_joy_move, last_hat_move, level
        global game_command, hold_used, hold_piece
        analog_threshold = settings["controller_settings"].get("analog_threshold", 0.5)
        joy_delay = settings["controller_settings"].get("joy_delay", 150)
        hat_threshold = settings["controller_settings"].get("hat_threshold", 0.5)
        hat_delay = settings["controller_settings"].get("hat_delay", 150)
        analog_deadzone = settings["controller_settings"].get("analog_deadzone", 0.3)
        for event in events:
            if event.type == pygame.JOYBUTTONDOWN:
                if cc.get('left') is not None and event.button == cc.get('left'):
                    left_pressed = True
                    new_x = offset[0] - 1
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                    last_horizontal_move = current_time
                elif cc.get('right') is not None and event.button == cc.get('right'):
                    right_pressed = True
                    new_x = offset[0] + 1
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                    last_horizontal_move = current_time
                elif cc.get('down') is not None and event.button == cc.get('down'):
                    fast_fall = True
                elif cc.get('rotate') is not None and event.button == cc.get('rotate'):
                    rotated, new_offset = rotate_tetromino_with_kick(tetromino, offset, grid)
                    tetromino, offset = rotated, new_offset
                elif cc.get('hard_drop') is not None and event.button == cc.get('hard_drop'):
                    lock_and_update_tetromino(current_time)
                elif cc.get('hold') is not None and event.button == cc.get('hold'):
                    if not hold_used:
                        hold_used = True
                        if hold_piece is None:
                            hold_piece = copy.deepcopy(tetromino)
                            tetromino = tetromino_bag.get_next_tetromino()
                            shape_index = get_shape_index(tetromino) or 0
                            color_index = (shape_index + level - 1) % len(COLORS) + 1
                            offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
                        else:
                            tetromino, hold_piece = copy.deepcopy(hold_piece), copy.deepcopy(tetromino)
                            shape_index = get_shape_index(tetromino) or 0
                            color_index = (shape_index + level - 1) % len(COLORS) + 1
                            offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
                elif cc.get('pause') is not None and event.button == cc.get('pause'):
                    pause_game()
                elif cc.get('skip_track') is not None and event.button == cc.get('skip_track'):
                    game_command = "skip"
            elif event.type == pygame.JOYBUTTONUP:
                if cc.get('left') is not None and event.button == cc.get('left'):
                    left_pressed = False
                elif cc.get('right') is not None and event.button == cc.get('right'):
                    right_pressed = False
                elif cc.get('down') is not None and event.button == cc.get('down'):
                    fast_fall = False
            elif event.type == pygame.JOYHATMOTION:
                if settings["controller_settings"].get("use_dpad", True):
                    if current_time - last_hat_move > hat_delay:
                        last_hat_move = current_time
                        hx, hy = event.value
                        if hx <= -hat_threshold:
                            left_pressed = True
                            new_x = offset[0] - 1
                            if valid_position(tetromino, [new_x, offset[1]], grid):
                                offset[0] = new_x
                            last_horizontal_move = current_time
                        elif hx >= hat_threshold:
                            right_pressed = True
                            new_x = offset[0] + 1
                            if valid_position(tetromino, [new_x, offset[1]], grid):
                                offset[0] = new_x
                            last_horizontal_move = current_time
                        if hy <= -hat_threshold:
                            fast_fall = True
                        else:
                            fast_fall = False
            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:
                    if abs(event.value) < analog_deadzone:
                        # If within deadzone, do not trigger movement.
                        pass
                    else:
                        if event.value <= -analog_threshold:
                            if current_time - last_joy_move > joy_delay:
                                new_x = offset[0] - 1
                                if valid_position(tetromino, [new_x, offset[1]], grid):
                                    offset[0] = new_x
                                last_joy_move = current_time
                        elif event.value >= analog_threshold:
                            if current_time - last_joy_move > joy_delay:
                                new_x = offset[0] + 1
                                if valid_position(tetromino, [new_x, offset[1]], grid):
                                    offset[0] = new_x
                                last_joy_move = current_time
                elif event.axis == 1:
                    if event.value >= analog_threshold:
                        fast_fall = True
                    else:
                        fast_fall = False

    def process_mouse_events(events):
        global game_command
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0] >= SCREEN_WIDTH:
                    rel_x = event.pos[0] - SCREEN_WIDTH
                    rel_y = event.pos[1]
                    if sound_bar_rect and sound_bar_rect.collidepoint(rel_x, rel_y):
                        new_volume = (rel_x - sound_bar_rect.x) / sound_bar_rect.width
                        pygame.mixer.music.set_volume(new_volume)
                    if restart_button_rect and restart_button_rect.collidepoint(rel_x, rel_y):
                        game_command = "restart"
                        return
                    if settings.get('use_custom_music', False) and skip_button_rect:
                        if skip_button_rect.collidepoint(rel_x, rel_y):
                            game_command = "skip"
                    if menu_button_rect and menu_button_rect.collidepoint(rel_x, rel_y):
                        game_command = "menu"
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:
                    if event.pos[0] >= SCREEN_WIDTH:
                        rel_x = event.pos[0] - SCREEN_WIDTH
                        if sound_bar_rect and sound_bar_rect.collidepoint(rel_x, event.pos[1]):
                            new_volume = (rel_x - sound_bar_rect.x) / sound_bar_rect.width
                            pygame.mixer.music.set_volume(new_volume)

    # ------------------------------ Main Loop ------------------------------
    while True:
        current_time = pygame.time.get_ticks()
        shake_intensity = screen_shake * 2
        shake_x = random.randint(-shake_intensity, shake_intensity) if screen_shake > 0 else 0
        shake_y = random.randint(-shake_intensity, shake_intensity) if screen_shake > 0 else 0

        if game_over:
            if heartbeat_playing and heartbeat_sound:
                heartbeat_sound.stop()
            if game_over_sound:
                game_over_sound.play()
            if settings.get('use_custom_music', False):
                last_track_index = current_track_index
            pygame.mixer.music.stop()
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

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                save_settings(settings)
                pygame.quit()
                sys.exit()
            elif event.type == MUSIC_END_EVENT:
                handle_music_end_event()
        process_keyboard_events(events, current_time)
        process_controller_events(events, current_time)
        process_mouse_events(events)

        if game_command in ("restart", "menu"):
            return
        elif game_command == "skip":
            skip_current_track()
            game_command = None

        # Process continuous movement from events.
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
            if valid_position(tetromino, [offset[0], offset[1] + 1], grid):
                offset[1] += 1
            else:
                if check_game_over(grid):
                    game_over = True
                else:
                    original_grid = [row[:] for row in grid]
                    place_tetromino(tetromino, offset, grid, color_index)
                    hold_used = False
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
                                        x * BLOCK_SIZE + BLOCK_SIZE // 2,
                                        y * BLOCK_SIZE + BLOCK_SIZE // 2,
                                        COLORS[original_grid[y][x] - 1],
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
                        fall_speed = max(50, int(base_fall_speed * (0.85 ** (level - 1))))
                        in_level_transition = True
                        transition_start_time = current_time
                        last_flash_time = current_time
                        flash_count = 0
                    tetromino = next_tetromino
                    shape_index = get_shape_index(tetromino) or 0
                    color_index = (shape_index + level - 1) % len(COLORS) + 1
                    next_tetromino = tetromino_bag.get_next_tetromino()
                    offset[:] = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
            last_fall_time = current_time

        # --- Poll Joystick for Flame Effects and Movement Correction ---
        if joy is not None:
            axis_val = joy.get_axis(0)
            hat_x = joy.get_hat(0)[0] if joy.get_numhats() > 0 else 0
            analog_threshold = settings["controller_settings"].get("analog_threshold", 0.5)
            deadzone = settings["controller_settings"].get("analog_deadzone", 0.3)
            # Compute inputs based solely on current joystick state.
            if abs(axis_val) < deadzone:
                poll_left = False
                poll_right = False
            else:
                poll_left = axis_val <= -analog_threshold
                poll_right = axis_val >= analog_threshold
            if settings["controller_settings"].get("use_dpad", True):
                poll_left = poll_left or (hat_x <= -settings["controller_settings"].get("hat_threshold", 0.5))
                poll_right = poll_right or (hat_x >= settings["controller_settings"].get("hat_threshold", 0.5))
            # Override left/right flags from polling (do not OR with previous event state).
            left_pressed = poll_left
            right_pressed = poll_right

        # ------------------------------ Spawn Flame Trail Particles ------------------------------
        if flame_trails_enabled and (left_pressed or right_pressed or fast_fall):
            num_particles = random.randint(3, 5)
            spawn_offset = 15
            for _ in range(num_particles):
                if left_pressed:
                    direction = "left"
                    spawn_x = (offset[0] - 1) * BLOCK_SIZE + random.randint(-spawn_offset, 0)
                    spawn_y = (offset[1] + random.uniform(0.2, 0.8) * len(tetromino)) * BLOCK_SIZE
                elif right_pressed:
                    direction = "right"
                    spawn_x = (offset[0] + len(tetromino[0])) * BLOCK_SIZE + random.randint(0, spawn_offset)
                    spawn_y = (offset[1] + random.uniform(0.2, 0.8) * len(tetromino)) * BLOCK_SIZE
                else:
                    direction = "down"
                    spawn_x = (offset[0] + random.uniform(0.2, 0.8) * len(tetromino[0])) * BLOCK_SIZE
                    spawn_y = (offset[1] + len(tetromino)) * BLOCK_SIZE - spawn_offset
                trail_particles.append(TrailParticle(spawn_x, spawn_y, direction))

        # ------------------------------ Update Particles ------------------------------
        wind_force = ((-4.0 if left_pressed else 4.0 if right_pressed else 0),
                      (5.0 if fast_fall else 0))
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

        # ------------------------------ Update Screen Shake ------------------------------
        screen_shake = max(0, screen_shake - 1)

        # ------------------------------ Danger Zone: Heartbeat Sound ------------------------------
        if is_danger_zone_active(grid):
            if not heartbeat_playing and heartbeat_sound:
                heartbeat_sound.play(-1)
                heartbeat_playing = True
        else:
            if heartbeat_playing and heartbeat_sound:
                heartbeat_sound.stop()
                heartbeat_playing = False

        # ------------------------------ Draw Everything ------------------------------
        screen.fill(BLACK)
        if not in_level_transition:
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if grid[y][x]:
                        draw_3d_block(screen, COLORS[grid[y][x] - 1],
                                      x * BLOCK_SIZE + shake_x,
                                      y * BLOCK_SIZE + shake_y,
                                      BLOCK_SIZE)
            for cy, row in enumerate(tetromino):
                for cx, cell in enumerate(row):
                    if cell:
                        draw_3d_block(screen, COLORS[color_index - 1],
                                      (offset[0] + cx) * BLOCK_SIZE + shake_x,
                                      (offset[1] + cy) * BLOCK_SIZE + shake_y,
                                      BLOCK_SIZE)
            screen.blit(grid_surface, (shake_x, shake_y))
            if settings.get('ghost_piece', True):
                draw_ghost_piece(tetromino, offset, grid, COLORS[color_index - 1])
            for explosion in explosion_particles:
                explosion.draw(screen, (shake_x, shake_y))
            for particle in trail_particles:
                particle.draw(screen)
            for particle in dust_particles:
                particle.draw(screen)
        else:
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if grid[y][x]:
                        draw_3d_block(screen, COLORS[grid[y][x] - 1],
                                      x * BLOCK_SIZE + shake_x,
                                      y * BLOCK_SIZE + shake_y,
                                      BLOCK_SIZE)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            level_text = tetris_font_large.render(f"LEVEL {level}", True, random.choice(COLORS))
            level_shake_x = random.randint(-10, 10)
            level_shake_y = random.randint(-10, 10)
            screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2 + level_shake_x,
                                     SCREEN_HEIGHT // 2 - level_text.get_height() // 2 + level_shake_y))
        draw_subwindow(score, next_tetromino, level, pieces_dropped, lines_cleared_total,
                       is_tetris, tetris_last_flash, tetris_flash_time)
        pygame.display.flip()

        clock.tick(60)
# -------------------------- Main --------------------------
def main():
    global settings, game_command, hold_piece, hold_used
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
        hold_piece = None
        hold_used = False
        while True:
            run_game()
            if game_command == "menu":
                break  # Return to main menu when requested

if __name__ == "__main__":
    main()
