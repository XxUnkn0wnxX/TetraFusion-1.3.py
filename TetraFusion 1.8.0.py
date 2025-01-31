import pygame
import random
import sys
import os
import math
import json

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 450
SCREEN_HEIGHT = 930
BLOCK_SIZE = 30
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE
SUBWINDOW_WIDTH = 369
DOUBLE_CLICK_TIME = 300

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
COLORS = [(0, 255, 255), (255, 165, 0), (0, 0, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (128, 0, 128)]

HEARTBEAT_SOUND_PATH = "Audio/heartbeat_grid_almost_full.ogg"
heartbeat_sound = pygame.mixer.Sound(HEARTBEAT_SOUND_PATH)
heartbeat_playing = False  # Track whether the heartbeat sound is currently playing

BACKGROUND_MUSIC_PATH = "Audio/Background.ogg"
LINE_CLEAR_SOUND_PATH = "Audio/Lineclear.ogg"
MULTIPLE_LINE_CLEAR_SOUND_PATH = "Audio/MultipleLineclear.ogg"
GAME_OVER_SOUND_PATH = "Audio/GAMEOVER.ogg"

SHAPES = [
    [[1, 1, 1], [0, 1, 0]],
    [[1, 1], [1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 1, 1, 1]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [1, 1, 1]]
]

pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
pygame.mixer.music.play(-1)
line_clear_sound = pygame.mixer.Sound(LINE_CLEAR_SOUND_PATH)
multiple_line_clear_sound = pygame.mixer.Sound(MULTIPLE_LINE_CLEAR_SOUND_PATH)
game_over_sound = pygame.mixer.Sound(GAME_OVER_SOUND_PATH)

# Load Tetris font
TETRIS_FONT_PATH = "assets/tetris-blocks.TTF"
try:
    tetris_font_large = pygame.font.Font(TETRIS_FONT_PATH, 40)
    tetris_font_medium = pygame.font.Font(TETRIS_FONT_PATH, 27)
    tetris_font_small = pygame.font.Font(TETRIS_FONT_PATH, 18)
except FileNotFoundError:
    print(f"Font file not found: {TETRIS_FONT_PATH}")
    sys.exit()

screen = pygame.display.set_mode((SCREEN_WIDTH + SUBWINDOW_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("TetraFusion 1.8.00")
clock = pygame.time.Clock()

subwindow_visible = True
last_click_time = 0

# Settings System
def load_settings(filename="settings.json"):
    default_settings = {
        'controls': {
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'down': pygame.K_DOWN,
            'rotate': pygame.K_UP,
            'pause': pygame.K_p
        },
        'difficulty': 'normal',
        'flame_trails': True,
        'grid_color': [200, 200, 200],  # Default grid color (light gray)
        'grid_opacity': 128  # Default grid opacity (50%)
    }
    
    try:
        with open(filename, "r") as file:
            saved_settings = json.load(file)

            # Convert control keys back from strings to pygame constants
            if 'controls' in saved_settings:
                for key, value in saved_settings['controls'].items():
                    if isinstance(value, str):  # Convert key name to constant
                        saved_settings['controls'][key] = getattr(pygame, f'K_{value.lower()}', default_settings['controls'][key])

            # Ensure all necessary keys exist
            for key, default_value in default_settings.items():
                if key not in saved_settings:
                    saved_settings[key] = default_value

            return saved_settings

    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return default_settings

# Draw 3D Block
def draw_3d_block(screen, color, x, y, block_size):
    """
    Draw a single Tetris block in a 2.5D perspective style with uniform shading on all faces.
    :param screen: Pygame surface to draw on.
    :param color: Base color of the block (tuple).
    :param x: X-coordinate of the top-left of the block.
    :param y: Y-coordinate of the top-left of the block.
    :param block_size: Size of the block (in pixels).
    """
    # Define shades for 3D effect
    top_color = tuple(min(255, c + 40) for c in color)  # Lighter top face
    side_color = tuple(max(0, c - 40) for c in color)  # Darker side face
    front_color = color  # Front face is the base color

    # Ensure front face is inside the block size (avoid leaking outside)
    front_rect = pygame.Rect(x + 5, y + 5, block_size - 10, block_size - 10)

    # Top face (perspective effect)
    top_polygon = [
        (x, y),  # Top-left
        (x + block_size, y),  # Top-right
        (x + block_size - 5, y + 5),  # Bottom-right (perspective skew)
        (x + 5, y + 5),  # Bottom-left (perspective skew)
    ]
    pygame.draw.polygon(screen, top_color, top_polygon)

    # Left face (darker shadow)
    left_polygon = [
        (x, y),  # Top-left
        (x + 5, y + 5),  # Bottom-left (perspective skew)
        (x + 5, y + block_size + 5),  # Bottom-left of front face
        (x, y + block_size),  # Bottom-left corner
    ]
    pygame.draw.polygon(screen, side_color, left_polygon)

    # Right face (lighter shadow)
    right_polygon = [
        (x + block_size, y),  # Top-right
        (x + block_size - 5, y + 5),  # Bottom-right (perspective skew)
        (x + block_size - 5, y + block_size + 5),  # Bottom-right of front face
        (x + block_size, y + block_size),  # Bottom-right corner
    ]
    pygame.draw.polygon(screen, side_color, right_polygon)

    # Draw the front face with the base color
    pygame.draw.rect(screen, front_color, front_rect)

    # Add a black outline around the whole block to prevent color leakage
    outline_color = (0, 0, 0)  # Black outline
    pygame.draw.rect(screen, outline_color, front_rect, 2)  # Border around the front face

    # Add outlines to other faces if needed for further separation
    pygame.draw.polygon(screen, outline_color, top_polygon, 2)  # Outline around the top face
    pygame.draw.polygon(screen, outline_color, left_polygon, 2)  # Outline around the left face
    pygame.draw.polygon(screen, outline_color, right_polygon, 2)  # Outline around the right face

def draw_3d_grid(grid_surface, grid_color, grid_opacity):
    """
    Draws the static grid lines only once and stores it on a separate surface.
    Applies the correct transparency based on menu settings (0 - 192).
    """
    grid_surface.fill((0, 0, 0, 0))  # Clear previous grid

    # Ensure grid_opacity stays between 0 (fully transparent) and 192 (semi-transparent)
    alpha_value = max(0, min(192, grid_opacity))  # Clamp between 0 and 192
    grid_color_with_alpha = (*grid_color, alpha_value)  # Apply alpha channel

    for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
        pygame.draw.line(grid_surface, grid_color_with_alpha, (x, 0), (x, SCREEN_HEIGHT), 1)

    for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
        pygame.draw.line(grid_surface, grid_color_with_alpha, (0, y), (SCREEN_WIDTH, y), 1)

def load_high_score(filename="high_score.txt"):
    try:
        print(f"Trying to load high score from {filename}")
        if os.path.exists(filename):
            with open(filename, "r") as file:
                content = file.read().strip()
                print(f"File content: '{content}'")
                if content:
                    parts = content.split(maxsplit=1)
                    return int(parts[0]), parts[1] if len(parts) > 1 else "---"
        return 0, "---"
    except Exception as e:
        print(f"Error loading high score: {e}")
        return 0, "---"

def save_high_score(high_score, high_score_name, filename="high_score.txt"):
    try:
        print(f"Trying to save high score to {filename}")
        with open(filename, "w") as file:
            file.write(f"{high_score} {high_score_name}")
        print(f"High score saved: {high_score} {high_score_name}")
    except Exception as e:
        print(f"Error saving high score: {e}")

high_score, high_score_name = load_high_score()
print(f"Loaded high score: {high_score} {high_score_name}")

class TrailParticle:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction  # Store direction for angle adjustment

        # Set angle based on direction
        if direction == "left":
            self.angle = random.uniform(math.pi / 2, 3 * math.pi / 2)  # Leftward angles
        elif direction == "right":
            self.angle = random.uniform(-math.pi / 2, math.pi / 2)  # Rightward angles
        elif direction == "down":
            self.angle = random.uniform(math.pi / 2 - math.pi / 8, math.pi / 2 + math.pi / 8)  # Downward
        else:
            self.angle = random.uniform(-math.pi, math.pi)  # Default random

        self.speed = random.uniform(1.5, 3.0)
        self.age = 0
        self.max_age = random.randint(40, 60)  # Extended lifespan
        self.size = random.randint(12, 20)  # Larger particle size for visibility
        self.colors = self.generate_color_ramp()
        self.turbulence = random.uniform(0.5, 1.5)
        self.gravity = -0.1  # Lift effect for flame-like motion
        self.drift_x = random.uniform(-0.5, 0.5)
        self.drift_y = random.uniform(-0.5, 0.5)

    def generate_color_ramp(self):
        return [
            (255, 240, 150),  # Bright yellow (core)
            (255, 180, 80),  # Vibrant orange
            (255, 90, 40)  # Deep red
        ]

    def update(self, wind_force=(0, 0), screen=None):
        # Movement with turbulence and wind
        self.x += math.cos(self.angle) * self.speed + self.drift_x + wind_force[0]
        self.y += math.sin(self.angle) * self.speed + self.drift_y + wind_force[1]

        # Clamp position to screen bounds if available
        if screen:
            self.x = max(self.size, min(screen.get_width() - self.size, self.x))
            self.y = max(self.size, min(screen.get_height() - self.size, self.y))

        # Apply physics
        self.speed *= 0.92
        self.drift_x *= 0.7
        self.drift_y *= 0.7
        self.y += self.gravity

        # Age and fade
        self.age += 1
        self.size = max(5, self.size * 0.95)  # Ensure minimum particle size

    def draw(self, screen):
        if self.age >= self.max_age:
            return

        # Skip drawing if outside screen bounds
        if not (0 <= self.x <= screen.get_width() and 0 <= self.y <= screen.get_height()):
            return

        # Color and alpha calculations
        color_progress = self.age / self.max_age
        if color_progress < 0.33:
            color = self.colors[0]
        elif color_progress < 0.66:
            color = self.colors[1]
        else:
            color = self.colors[2]

        alpha = int(255 * (1 - color_progress ** 1.5))  # More gradual fading

        # Direct particle drawing for better blending and performance
        radius = int(self.size)
        blended_color = (color[0], color[1], color[2], alpha)

        # Create a surface for the particle
        particle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, blended_color, (radius, radius), radius)
        screen.blit(particle_surface, (int(self.x - radius), int(self.y - radius)))

def create_wind_particles(tetromino_x, tetromino_y, direction):
    particle_count = random.randint(15, 25)  # Double the particles
    spread = 40  # Increased spread area

    for _ in range(particle_count):
        # Direction-based force multipliers
        if direction == "left":
            angle = random.uniform(-3.5, -1.5)  # Aggressive left angle
            speed = random.uniform(5, 9)
            dir_mod = random.uniform(1.2, 1.8)
        elif direction == "right":
            angle = random.uniform(1.5, 3.5)  # Strong right angle
            speed = random.uniform(5, 9)
            dir_mod = random.uniform(1.2, 1.8)
        elif direction == "down":
            angle = random.uniform(2.0, 4.0)  # Steep downward angle
            speed = random.uniform(7, 12)  # Faster speed
            dir_mod = random.uniform(2.0, 2.5)  # Stronger modifier
        else:
            angle = random.uniform(-1.0, 1.0)
            speed = random.uniform(3, 5)
            dir_mod = 1.0

        particle = TrailParticle(
            tetromino_x + random.uniform(-spread, spread),
            tetromino_y + random.uniform(-spread, spread),
            direction
        )
        particle.speed = speed
        particle.angle = angle
        particle.direction_modifier = dir_mod
        wind_particles.append(particle)

def draw_wind_particles(direction):
    # More intense directional forces
    wind_forces = {
        "left": (-6, 0.8),  # Powerful left push
        "right": (6, 0.8),  # Powerful right push
        "down": (0, 8)  # Meteor-like downward force
    }

    current_force = wind_forces.get(direction, (0, 1))

    # Add screen shake based on direction
    shake_intensity = {
        "left": (-3, 0),
        "right": (3, 0),
        "down": (0, 5)
    }.get(direction, (0, 0))

    # Apply force to all particles
    for particle in wind_particles[:]:
        particle.update(current_force, screen)
        if particle.age >= particle.max_age:
            wind_particles.remove(particle)
        else:
            particle.draw(screen)

    # Return shake intensity to apply to game camera
    return shake_intensity
            
class Explosion:
    def __init__(self, x, y, color, particle_count=30, max_speed=8, duration=45):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []
        self.lifetime = duration
        for _ in range(particle_count):
            self.particles.append([
                x + random.uniform(-15, 15),  # Wider spread
                y + random.uniform(-15, 15),
                random.uniform(-max_speed, max_speed),  # Faster particles
                random.uniform(-max_speed, max_speed),
                random.uniform(0.1, 0.3),  # Slower gravity
                random.randint(200, 255)  # Longer fade
            ])

    def update(self):
        self.lifetime -= 1
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[4]  # Gravity
            p[5] = max(0, p[5] - 4)  # Slower fade

    def draw(self, surface, offset=(0,0)):
        for p in self.particles:
            if p[5] > 0:
                size = 4 + int(p[5]/50)  # Size decreases with alpha
                pygame.draw.circle(surface, 
                                 (*self.color, p[5]), 
                                 (int(p[0] + offset[0]), int(p[1] + offset[1])), 
                                 size)
                             
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

def create_grid():
    """
    Create a clean grid filled with zeros.
    """
    return [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def is_danger_zone_active(grid):
    """
    Check if any block is in the top 4 rows of the grid.
    :param grid: The game grid.
    :return: True if any block is in the top 4 rows, False otherwise.
    """
    for y in range(4):  # Check rows 0 through 3
        if any(grid[y]):  # If any cell in the row is non-zero
            return True
    return False

def draw_grid(grid):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x]:
                block_color = COLORS[grid[y][x] - 1]
                draw_3d_block(screen, block_color, x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE)
            # Optional: Draw grid lines
            pygame.draw.rect(screen, WHITE, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

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
    """
    Rotates the tetromino and adjusts its position to avoid collisions with walls or other blocks.
    :param tetromino: Current tetromino shape.
    :param offset: Current position of the tetromino (x, y).
    :param grid: The game grid.
    :return: The rotated tetromino and adjusted offset.
    """
    # Rotate the tetromino
    rotated = [list(row) for row in zip(*tetromino[::-1])]

    # List of possible adjustments for wall kicks
    kicks = [
        (0, 0),  # No adjustment
        (-1, 0),  # Move left
        (1, 0),  # Move right
        (0, -1),  # Move up (only for T-shaped or flat pieces)
        (-2, 0),  # Big left kick
        (2, 0),   # Big right kick
    ]

    for dx, dy in kicks:
        new_offset = [offset[0] + dx, offset[1] + dy]
        if valid_position(rotated, new_offset, grid):
            return rotated, new_offset

    # If no valid position, return the original tetromino and offset
    return tetromino, offset

def clear_lines(grid):
    full_lines = [y for y in range(GRID_HEIGHT) if all(grid[y])]
    if full_lines:
        if len(full_lines) == 4:  # Check for a Tetris (clearing 4 lines)
            multiple_line_clear_sound.play()
        else:  # Play the normal sound for 1-3 lines
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
    subwindow = pygame.Surface((SUBWINDOW_WIDTH, SCREEN_HEIGHT))
    subwindow.fill(BLACK)
    
    score_text = tetris_font_small.render(f"Score: {score}", True, WHITE)
    high_score_text = tetris_font_small.render(f"High Score: {high_score} ({high_score_name})", True, WHITE)
    level_text = tetris_font_small.render(f"Level: {level}", True, WHITE)
    pieces_text = tetris_font_small.render(f"Pieces Dropped: {pieces_dropped}", True, WHITE)
    lines_text = tetris_font_small.render(f"Lines Cleared: {lines_cleared_total}", True, WHITE)

    # Render texts at different y positions to avoid overlap
    subwindow.blit(score_text, (10, 10))
    subwindow.blit(high_score_text, (10, 40))
    subwindow.blit(level_text, (10, 70))  # Adjusted y position for level
    subwindow.blit(pieces_text, (10, 100))
    subwindow.blit(lines_text, (10, 130))  # Adjusted y position for lines

    next_text = tetris_font_small.render("Next:", True, WHITE)
    subwindow.blit(next_text, (10, 160))

    # Rendering next tetromino if available
    if next_tetromino:
        start_x = 10
        start_y = 180
        color_index = (SHAPES.index(next_tetromino) + level - 1) % len(COLORS) + 1
        for row_idx, row in enumerate(next_tetromino):
            for col_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        subwindow,
                        COLORS[color_index - 1],
                        (start_x + col_idx * BLOCK_SIZE, start_y + row_idx * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                    )

    # Flash "TetraFusion" if a Tetris occurred
    if is_tetris:
        time_since_flash = pygame.time.get_ticks() - tetris_last_flash
        if time_since_flash < tetris_flash_time:
            flashing_color = random.choice(COLORS)
            flash_text = tetris_font_medium.render("TetraFusion!", True, flashing_color)
            text_x = (SUBWINDOW_WIDTH - flash_text.get_width()) // 2
            text_y = SCREEN_HEIGHT - 50
            subwindow.blit(flash_text, (text_x, text_y))
        else:
            # Reset Tetris effect
            is_tetris = False

    screen.blit(subwindow, (SCREEN_WIDTH, 0))

# Menu System
def draw_main_menu():
    screen.fill(BLACK)
    title_text = tetris_font_large.render("TetraFusion", True, random.choice(COLORS))
    start_text = tetris_font_medium.render("Press ENTER to Start", True, WHITE)
    options_text = tetris_font_medium.render("Press O for Options", True, WHITE)
    exit_text = tetris_font_medium.render("Press ESC to Quit", True, WHITE)

    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 3))
    screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT // 2))
    screen.blit(options_text, (SCREEN_WIDTH // 2 - options_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(exit_text, (SCREEN_WIDTH // 2 - exit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))

    pygame.display.flip()
    
def main_menu():
    while True:
        draw_main_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    run_game()  # Start a fresh game
                    return  # Exit the menu loop after starting the game
                elif event.key == pygame.K_o:
                    options_menu()  # Open options menu
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()  # Allow quitting from the menu
                    
def options_menu():
    global settings
    selected_option = 0
    options = [
        ('left', 'Left'), ('right', 'Right'), ('down', 'Down'),
        ('rotate', 'Rotate'), ('pause', 'Pause'), ('difficulty', 'Difficulty'),
        ('flame_trails', 'Flame Trails'), ('grid_opacity', 'Grid Opacity'),
        ('back', 'Back to Main Menu')
    ]
    changing_key = None

    while True:
        screen.fill(BLACK)
        title_text = tetris_font_large.render("Options", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))

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

            option_text = tetris_font_medium.render(text, True, color)
            screen.blit(option_text, (SCREEN_WIDTH // 2 - option_text.get_width() // 2, 150 + i * 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if changing_key:  # If user is changing a key, update it
                    settings['controls'][changing_key] = event.key
                    changing_key = None
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    current_key = options[selected_option][0]
                    if current_key in settings['controls']:
                        changing_key = current_key  # Wait for key press to update control
                    elif current_key == 'difficulty':
                        difficulties = ['easy', 'normal', 'hard', 'very hard']
                        new_idx = (difficulties.index(settings['difficulty']) + 1) % 4
                        settings['difficulty'] = difficulties[new_idx]
                    elif current_key == 'flame_trails':
                        settings['flame_trails'] = not settings['flame_trails']
                    elif current_key == 'grid_opacity':
                        settings['grid_opacity'] = (settings['grid_opacity'] + 64) % 256
                    elif current_key == 'back':
                        save_settings(settings)
                        return
                elif event.key == pygame.K_ESCAPE:
                    save_settings(settings)
                    return
                        
def save_settings(settings, filename="settings.json"):
    # Convert pygame key constants to string names
    controls_dict = {
        control: pygame.key.name(key).upper() for control, key in settings['controls'].items()
    }

    settings_to_save = {
        'controls': controls_dict,
        'difficulty': settings['difficulty'],
        'flame_trails': settings['flame_trails'],
        'grid_color': settings['grid_color'],
        'grid_opacity': settings['grid_opacity']
    }

    try:
        with open(filename, "w") as file:
            json.dump(settings_to_save, file, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")                    

def pause_game():
    global settings
    pause_text = tetris_font_large.render("PAUSED", True, WHITE)
    paused = True
    
    # Clear any existing key events to prevent immediate unpause
    pygame.event.clear(pygame.KEYDOWN)
    
    while paused:
        screen.fill(BLACK)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == settings['controls']['pause']:
                    paused = False
                # Allow escape as universal pause breaker
                elif event.key == pygame.K_ESCAPE:
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

            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 50))
            screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 150))
            screen.blit(initials_text, (SCREEN_WIDTH // 2 - initials_text.get_width() // 2, 250))
            screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, 350))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
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
                        main_menu()
                        return
    else:
        screen.fill(BLACK)
        game_over_text = tetris_font_large.render("GAME OVER", True, RED)
        score_text = tetris_font_medium.render(f"Score: {score}", True, WHITE)
        restart_text = tetris_font_small.render("Press R to Restart", True, WHITE)
        menu_text = tetris_font_small.render("Press M for Menu", True, WHITE)

        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 50))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 150))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT - 130))
        screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, SCREEN_HEIGHT - 100))
        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        run_game()  # Restart the game
                        return
                    elif event.key == pygame.K_m:
                        main_menu()  # Return to the main menu
                        return
                        
                        

def place_tetromino(tetromino, offset, grid, color_index):
    """
    Place a tetromino on the grid and mark its cells with the correct color index.
    :param tetromino: The current tetromino shape (2D list).
    :param offset: The (x, y) position of the tetromino on the grid.
    :param grid: The grid where the tetromino is being placed.
    :param color_index: The index of the color to mark the grid cells with.
    """
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:  # Only update cells that are part of the tetromino
                x = offset[0] + cx
                y = offset[1] + cy
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:  # Ensure within grid bounds
                    grid[y][x] = color_index

def run_game():
    global high_score, high_score_name, subwindow_visible, last_click_time
    global level, lines_cleared_total, pieces_dropped, wind_particles, heartbeat_playing
    global trail_particles, explosion_particles, screen_shake, settings

    # Load settings
    controls = settings['controls']
    difficulty = settings['difficulty']
    flame_trails_enabled = settings['flame_trails']
    grid_color = tuple(settings['grid_color'])
    grid_opacity = settings.get('grid_opacity', 128)

    # Pre-render grid surface once
    grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    draw_3d_grid(grid_surface, grid_color, grid_opacity)

    # Difficulty-based speed adjustments
    difficulty_speeds = {
        'easy': 1200,
        'normal': 1000,
        'hard': 800,
        'very hard': 600
    }
    base_fall_speed = difficulty_speeds.get(difficulty, 1000)
    fall_speed = base_fall_speed

    # Game initialization
    level = 1
    lines_cleared_total = 0
    pieces_dropped = 0
    wind_particles = []
    trail_particles = []
    explosion_particles = []
    screen_shake = 0
    grid = create_grid()
    tetromino_bag = TetrominoBag(SHAPES)
    tetromino = tetromino_bag.get_next_tetromino()
    next_tetromino = tetromino_bag.get_next_tetromino()
    color_index = (SHAPES.index(tetromino) + level - 1) % len(COLORS) + 1
    offset = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]

    # Game state variables
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
    
    # Level transition variables
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
            if heartbeat_playing:
                heartbeat_sound.stop()
                heartbeat_playing = False
            game_over_sound.play()
            display_game_over(score)
            return

        # Handle level transition effects
        if in_level_transition:
            if current_time - transition_start_time > TRANSITION_DURATION:
                in_level_transition = False
                # Recreate grid surface with new settings
                grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                draw_3d_grid(grid_surface, grid_color, grid_opacity)
                # Apply final color changes
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
            
            # Skip normal game logic during transition
            screen.fill(BLACK)
            screen.blit(grid_surface, (0, 0))
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if grid[y][x]:
                        draw_3d_block(
                            screen, COLORS[grid[y][x]-1],
                            x * BLOCK_SIZE + shake_x,
                            y * BLOCK_SIZE + shake_y,
                            BLOCK_SIZE
                        )
            
            # Draw transition overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            level_text = tetris_font_large.render(f"LEVEL {level}", True, random.choice(COLORS))
            screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, 
                                    SCREEN_HEIGHT//2 - level_text.get_height()//2))

        # Main drawing sequence
        screen.fill(BLACK)
        screen.blit(grid_surface, (0, 0))  # Static pre-rendered grid

        # Draw placed blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if grid[y][x]:
                    draw_3d_block(
                        screen, COLORS[grid[y][x]-1],
                        x * BLOCK_SIZE + shake_x,
                        y * BLOCK_SIZE + shake_y,
                        BLOCK_SIZE
                    )

        # Draw current piece
        for cy, row in enumerate(tetromino):
            for cx, cell in enumerate(row):
                if cell:
                    draw_3d_block(
                        screen, COLORS[color_index-1],
                        (offset[0]+cx)*BLOCK_SIZE + shake_x,
                        (offset[1]+cy)*BLOCK_SIZE + shake_y,
                        BLOCK_SIZE
                    )

        # Draw UI elements
        if subwindow_visible:
            draw_subwindow(score, next_tetromino, level, pieces_dropped, lines_cleared_total)

        # Heartbeat sound logic
        if is_danger_zone_active(grid):
            if not heartbeat_playing:
                heartbeat_sound.play(-1)
                heartbeat_playing = True
        else:
            if heartbeat_playing:
                heartbeat_sound.stop()
                heartbeat_playing = False

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
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
                elif event.key == settings['controls']['pause']:
                    pause_game()
            elif event.type == pygame.KEYUP:
                if event.key == controls['left']:
                    left_pressed = False
                elif event.key == controls['right']:
                    right_pressed = False
                elif event.key == controls['down']:
                    fast_fall = False

        # Horizontal movement logic
        if left_pressed or right_pressed:
            time_since_last_move = current_time - last_horizontal_move
            required_delay = fast_move_interval if time_since_last_move > move_interval else move_interval
            
            if time_since_last_move >= required_delay:
                direction = -1 if left_pressed else 1
                new_x = offset[0] + direction
                if valid_position(tetromino, [new_x, offset[1]], grid):
                    offset[0] = new_x
                last_horizontal_move = current_time

        # Falling logic
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

        # Flame Particle Effects
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

        # Particle Updates
        wind_force = (
            -4.0 if left_pressed else 
            4.0 if right_pressed else 
            0,
            5.0 if fast_fall else 0
        )

        for particle in trail_particles[:]:
            particle.update(wind_force, screen)
            if particle.age >= particle.max_age:
                trail_particles.remove(particle)

        # Update explosions
        for explosion in explosion_particles[:]:
            explosion.update()
            if explosion.lifetime <= 0:
                explosion_particles.remove(explosion)

        screen_shake = max(0, screen_shake - 1)

        # Drawing sequence
        screen.fill(BLACK)
        
        # Draw grid with screen shake and configured grid color
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if grid[y][x]:
                    draw_3d_block(
                        screen, COLORS[grid[y][x]-1],
                        x * BLOCK_SIZE + shake_x,
                        y * BLOCK_SIZE + shake_y,
                        BLOCK_SIZE
                    )
                pygame.draw.rect(screen, grid_color, 
                               (x * BLOCK_SIZE + shake_x, y * BLOCK_SIZE + shake_y, 
                                BLOCK_SIZE, BLOCK_SIZE), 1)

        # Draw explosions
        for explosion in explosion_particles:
            explosion.draw(screen, (shake_x, shake_y))

        # Draw current piece
        for cy, row in enumerate(tetromino):
            for cx, cell in enumerate(row):
                if cell:
                    draw_3d_block(
                        screen, COLORS[color_index-1],
                        (offset[0]+cx)*BLOCK_SIZE + shake_x,
                        (offset[1]+cy)*BLOCK_SIZE + shake_y,
                        BLOCK_SIZE
                    )

        # Draw particles
        for particle in trail_particles:
            particle.draw(screen)

        # Draw UI panel
        if subwindow_visible:
            draw_subwindow(score, next_tetromino, level, pieces_dropped, 
                         lines_cleared_total, is_tetris, tetris_last_flash, tetris_flash_time)

        pygame.display.flip()
        clock.tick(60)

def main():
    global settings
    settings = load_settings()
    while True:
        main_menu()
        run_game()

# Start the program
if __name__ == "__main__":
    main()
