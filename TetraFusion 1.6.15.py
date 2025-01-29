import pygame
import random
import sys
import os
import math

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
pygame.display.set_caption("TetraFusion 1.6.15")
clock = pygame.time.Clock()

subwindow_visible = True
last_click_time = 0

# New Function: Draw 3D Block
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

def draw_3d_grid(grid, surface):
    """
    Draw the Tetris grid in a 2.5D perspective style.
    Each cell with a non-zero value is rendered as a block.
    """
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x]:  # If the cell is occupied
                color = COLORS[grid[y][x] - 1]  # Get the block's color
                cell_x = x * BLOCK_SIZE
                cell_y = y * BLOCK_SIZE - y * 5  # Apply perspective skew
                draw_3d_block(surface, color, cell_x, cell_y, BLOCK_SIZE)
            # Draw grid lines (preserved from your original version)
            pygame.draw.rect(surface, WHITE, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

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
    def __init__(self, x, y, angle, speed, turbulence_factor=0.2):
        self.x = x
        self.y = y
        self.base_speed = speed  # Store original speed
        self.speed = speed
        self.turbulence_factor = turbulence_factor
        self.alpha = 255
        self.size = random.randint(3, 5)  # Even larger particles
        self.curve_offset = random.uniform(-3, 3)  # More dramatic curves
        self.color = random.choice(COLORS)
        self.vertical_drift = random.uniform(-1, 2)  # Stronger vertical variation
        self.rotation = random.uniform(-10, 10)  # Faster rotation
        self.direction_modifier = 1  # For directional boosts

    def update(self, wind_force):
        # Apply exponential wind force based on direction
        self.x += (self.speed ** 1.5) * wind_force[0] * 2.5 * self.direction_modifier
        self.y += (self.speed ** 1.2) * wind_force[1] * 2.0
        
        # Dynamic turbulence that increases with speed
        turbulence_intensity = self.speed * 0.1
        self.x += math.sin(pygame.time.get_ticks() * 0.015 * self.speed) * turbulence_intensity
        self.y += math.cos(pygame.time.get_ticks() * 0.012 * self.speed) * turbulence_intensity
        
        # Add directional momentum preservation
        self.x += self.curve_offset * turbulence_intensity * 2
        self.y += self.vertical_drift * turbulence_intensity * 1.5
        
        # Speed-based alpha decay with exponential fade
        self.alpha -= 6 + int(self.speed * 3)
        self.alpha = max(0, self.alpha)
        
        # Evolve parameters with momentum
        self.curve_offset += random.uniform(-0.3, 0.3) * self.speed
        self.vertical_drift += random.uniform(-0.2, 0.2) * self.speed
        self.rotation += self.curve_offset * 2  # Rotation tied to movement
        self.speed *= 0.97  # Gradual speed decay

    def draw(self, screen):
        # Create particle with dynamic size based on speed
        current_size = self.size + int(self.speed * 0.5)
        particle_surface = pygame.Surface((current_size*2, current_size*2), pygame.SRCALPHA)
        
        # Speed-based color intensity
        intensity = min(1.0, self.speed/8.0)
        draw_color = (
            int(self.color[0] * intensity),
            int(self.color[1] * intensity),
            int(self.color[2] * intensity),
            self.alpha
        )
        
        # Glowing core effect
        pygame.draw.circle(particle_surface, draw_color, 
                         (current_size, current_size), current_size)
        
        # Apply dramatic rotation and scaling
        rotated_surface = pygame.transform.rotozoom(
            particle_surface, 
            self.rotation, 
            1.0 + (self.speed * 0.05)
        )
        screen.blit(rotated_surface, 
                  (int(self.x)-current_size, int(self.y)-current_size))

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
            angle = random.uniform(1.5, 3.5)    # Strong right angle
            speed = random.uniform(5, 9)
            dir_mod = random.uniform(1.2, 1.8)
        elif direction == "down":
            angle = random.uniform(2.0, 4.0)    # Steep downward angle
            speed = random.uniform(7, 12)       # Faster speed
            dir_mod = random.uniform(2.0, 2.5)  # Stronger modifier
        else:
            angle = random.uniform(-1.0, 1.0)
            speed = random.uniform(3, 5)
            dir_mod = 1.0
            
        particle = TrailParticle(
            tetromino_x + random.uniform(-spread, spread),
            tetromino_y + random.uniform(-spread, spread),
            angle, 
            speed,
            turbulence_factor=random.uniform(0.2, 0.3)
        )
        particle.direction_modifier = dir_mod
        wind_particles.append(particle)

def draw_wind_particles(direction):
    # More intense directional forces
    wind_forces = {
        "left": (-6, 0.8),   # Powerful left push
        "right": (6, 0.8),   # Powerful right push
        "down": (0, 8)       # Meteor-like downward force
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
        particle.update(current_force)
        if particle.alpha <= 0:
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

def draw_main_menu():
    screen.fill(BLACK)
    title_text = tetris_font_large.render("TetraFusion", True, random.choice(COLORS))
    instructions_text = tetris_font_medium.render("Press ENTER to Start", True, WHITE)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 3))
    screen.blit(instructions_text, (SCREEN_WIDTH // 2 - instructions_text.get_width() // 2, SCREEN_HEIGHT // 2))
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

def pause_game():
    pause_text = tetris_font_large.render("PAUSED", True, WHITE)
    paused = True
    while paused:
        screen.fill(BLACK)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
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
    global trail_particles, explosion_particles, screen_shake, rotation_angle, color_pulse

    # Game initialization
    level = 1
    lines_cleared_total = 0
    pieces_dropped = 0
    wind_particles = []
    trail_particles = []
    explosion_particles = []
    screen_shake = 0
    direction = 0  # Properly initialized direction variable
    grid = create_grid()
    tetromino_bag = TetrominoBag(SHAPES)
    tetromino = tetromino_bag.get_next_tetromino()
    next_tetromino = tetromino_bag.get_next_tetromino()
    color_index = (SHAPES.index(tetromino) + level - 1) % len(COLORS) + 1
    offset = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]

    # Game state variables
    score = 0
    base_fall_speed = 1000  # Normal starting speed (1 second)
    fall_speed = base_fall_speed
    fast_fall = False
    last_fall_time = pygame.time.get_ticks()
    game_over = False
    move_queue = []
    last_left_press = 0
    last_right_press = 0
    move_delay = 200  # Comfortable initial delay
    repeat_delay = 50  # Smooth repeat rate
    is_tetris = False
    tetris_flash_time = 2000
    tetris_last_flash = 0

    # Configure key repeat for smooth movement
    pygame.key.set_repeat(200, 50)

    while True:
        current_time = pygame.time.get_ticks()
        # Enhanced screen shake calculation
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

        # Heartbeat sound logic
        if is_danger_zone_active(grid):
            if not heartbeat_playing:
                heartbeat_sound.play(-1)
                heartbeat_playing = True
        else:
            if heartbeat_playing:
                heartbeat_sound.stop()
                heartbeat_playing = False

        # Event handling with input buffering
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if 'left' not in move_queue:
                        move_queue.append('left')
                        last_left_press = current_time
                        direction = -1
                        # Initial immediate movement
                        new_x = offset[0] - 1
                        if valid_position(tetromino, [new_x, offset[1]], grid):
                            offset[0] = new_x
                elif event.key == pygame.K_RIGHT:
                    if 'right' not in move_queue:
                        move_queue.append('right')
                        last_right_press = current_time
                        direction = 1
                        # Initial immediate movement
                        new_x = offset[0] + 1
                        if valid_position(tetromino, [new_x, offset[1]], grid):
                            offset[0] = new_x
                elif event.key == pygame.K_DOWN:
                    fast_fall = True
                elif event.key == pygame.K_UP:
                    rotated, new_offset = rotate_tetromino_with_kick(tetromino, offset, grid)
                    tetromino, offset = rotated, new_offset
                elif event.key == pygame.K_p:
                    pause_game()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    move_queue = [m for m in move_queue if m != 'left']
                    if not move_queue: direction = 0
                elif event.key == pygame.K_RIGHT:
                    move_queue = [m for m in move_queue if m != 'right']
                    if not move_queue: direction = 0
                elif event.key == pygame.K_DOWN:
                    fast_fall = False

        # Optimized movement logic with momentum control
        if move_queue:
            current_move = move_queue[-1]  # Last direction takes priority
            time_since_last = current_time - (last_left_press if current_move == 'left' else last_right_press)

            if time_since_last > move_delay:
                # Calculate movement speed with gradual acceleration
                speed_factor = min(1.5, 1 + (time_since_last - move_delay)/1000)
                effective_delay = repeat_delay / speed_factor

                if current_time - (last_left_press if current_move == 'left' else last_right_press) > effective_delay:
                    new_x = offset[0] + (-1 if current_move == 'left' else 1)
                    if valid_position(tetromino, [new_x, offset[1]], grid):
                        offset[0] = new_x
                        # Update timing with momentum factor
                        adjusted_time = current_time - int(effective_delay * 0.8)
                        if current_move == 'left':
                            last_left_press = adjusted_time
                        else:
                            last_right_press = adjusted_time

        # Game logic
        current_fall_speed = 50 if fast_fall else fall_speed

        # Gravity system
        if current_time - last_fall_time > current_fall_speed:
            if valid_position(tetromino, [offset[0], offset[1] + 1], grid):
                offset[1] += 1
            else:
                if check_game_over(grid):
                    game_over = True
                else:
                    place_tetromino(tetromino, offset, grid, color_index)
                    grid, lines_cleared = clear_lines(grid)
                    lines_cleared_total += lines_cleared
                    score = update_score(score, lines_cleared)
                    pieces_dropped += 1

                    # Enhanced explosion effects
                    if lines_cleared > 0:
                        screen_shake = 8 + lines_cleared * 3  # Stronger shake for more lines
                        for y in range(GRID_HEIGHT):
                            if all(grid[y]):
                                for x in range(GRID_WIDTH):
                                    # Create larger explosions
                                    explosion_particles.append(Explosion(
                                        x * BLOCK_SIZE + BLOCK_SIZE//2,
                                        y * BLOCK_SIZE + BLOCK_SIZE//2,
                                        COLORS[color_index-1],
                                        particle_count=35,
                                        max_speed=12,
                                        duration=60
                                    ))

                    if lines_cleared == 4:
                        is_tetris = True
                        tetris_last_flash = current_time

                    # Level progression with smooth speed increase
                    new_level = lines_cleared_total // 10 + 1
                    if new_level > level:
                        level = new_level
                        fall_speed = max(50, int(base_fall_speed * (0.85 ** (level-1))))

                    # Get next piece
                    tetromino = next_tetromino
                    color_index = (SHAPES.index(tetromino) + level - 1) % len(COLORS) + 1
                    next_tetromino = tetromino_bag.get_next_tetromino()
                    offset = [GRID_WIDTH//2 - len(tetromino[0])//2, 0]
            
            last_fall_time = current_time

        # Particle effects
        for _ in range(2):
            trail_particles.append(TrailParticle(
                offset[0]*BLOCK_SIZE + random.randint(0, len(tetromino[0])*BLOCK_SIZE),
                offset[1]*BLOCK_SIZE + random.randint(0, len(tetromino)*BLOCK_SIZE),
                random.uniform(0, 360),
                random.uniform(1, 3)
            ))

        # Update particles with directional influence
        for particle in trail_particles[:]:
            particle.update((direction, 1))
            if particle.alpha <= 0:
                trail_particles.remove(particle)

        # Update explosions
        for explosion in explosion_particles[:]:
            explosion.update()
            if explosion.lifetime <= 0:
                explosion_particles.remove(explosion)

        # Gradually reduce screen shake
        screen_shake = max(0, screen_shake - 1)

        # Drawing sequence
        screen.fill(BLACK)
        
        # Draw grid with shake offset
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if grid[y][x]:
                    draw_3d_block(
                        screen, COLORS[grid[y][x]-1],
                        x * BLOCK_SIZE + shake_x,
                        y * BLOCK_SIZE + shake_y,
                        BLOCK_SIZE
                    )
                # Grid lines
                pygame.draw.rect(screen, WHITE, 
                               (x * BLOCK_SIZE + shake_x, y * BLOCK_SIZE + shake_y, 
                                BLOCK_SIZE, BLOCK_SIZE), 1)

        # Draw explosions with screen shake
        for explosion in explosion_particles:
            explosion.draw(screen, (shake_x, shake_y))

        # Draw current piece with shake
        for cy, row in enumerate(tetromino):
            for cx, cell in enumerate(row):
                if cell:
                    draw_3d_block(
                        screen, COLORS[color_index-1],
                        (offset[0]+cx)*BLOCK_SIZE + shake_x,
                        (offset[1]+cy)*BLOCK_SIZE + shake_y,
                        BLOCK_SIZE
                    )

        # Draw particle trails
        for particle in trail_particles:
            particle.draw(screen)

        # Draw UI panel
        if subwindow_visible:
            draw_subwindow(score, next_tetromino, level, pieces_dropped, 
                         lines_cleared_total, is_tetris, tetris_last_flash, tetris_flash_time)

        pygame.display.flip()
        clock.tick(60)

def main():
    while True:  # Main loop to control game flow
        main_menu()  # Display the main menu
        run_game()  # Start the game after leaving the menu

# Start the program
if __name__ == "__main__":
    main()
