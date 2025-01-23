import pygame
import random
import sys
import os

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
pygame.display.set_caption("TetraFusion 1.3")
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

def draw_3d_grid(grid):
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
                draw_3d_block(screen, color, cell_x, cell_y, BLOCK_SIZE)

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

class Particle:
    def __init__(self, x, y, angle, speed, turbulence_factor=0.05):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.turbulence_factor = turbulence_factor
        self.alpha = 255  # Transparency
        self.size = random.randint(1, 3)  # Particle size
        self.curve_offset = random.uniform(-1, 1)  # Initial curve offset

    def update(self, wind_force):
        self.x += self.speed * wind_force[0] + self.curve_offset * self.turbulence_factor
        self.y += self.speed * wind_force[1]
        self.curve_offset += random.uniform(-0.1, 0.1)
        self.alpha -= 5
        if self.alpha < 0:
            self.alpha = 0

    def draw(self, screen):
        color = (255, 255, 255)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

def create_wind_particles(tetromino_x, tetromino_y, direction):
    for _ in range(random.randint(2, 5)):
        angle = random.uniform(-0.5, 0.5)
        speed = random.uniform(1, 3)
        wind_particles.append(Particle(tetromino_x, tetromino_y, angle, speed))

def draw_wind_particles(direction):
    for particle in wind_particles[:]:
        wind_force = (direction, 1)
        particle.update(wind_force)
        if particle.alpha <= 0:
            wind_particles.remove(particle)
        else:
            particle.draw(screen)

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

def rotate_tetromino(tetromino):
    return [list(row) for row in zip(*tetromino[::-1])]

# Place a tetromino on the grid
def place_tetromino(tetromino, offset, grid, color_index):
    """
    Place a tetromino on the grid and mark its cells with the correct color index.
    """
    for cy, row in enumerate(tetromino):
        for cx, cell in enumerate(row):
            if cell:  # Only update cells that are part of the tetromino
                x = offset[0] + cx
                y = offset[1] + cy
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:  # Stay within bounds
                    grid[y][x] = color_index

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

def draw_subwindow(score, next_tetromino, level, pieces_dropped, lines_cleared_total):
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

def run_game():
    global high_score, high_score_name, subwindow_visible, last_click_time
    global level, lines_cleared_total, pieces_dropped, wind_particles

    # Reset all game variables to ensure a fresh start
    level = 1
    lines_cleared_total = 0
    pieces_dropped = 0
    wind_particles = []
    grid = create_grid()
    tetromino_bag = TetrominoBag(SHAPES)
    tetromino = tetromino_bag.get_next_tetromino()
    next_tetromino = tetromino_bag.get_next_tetromino()
    color_index = (SHAPES.index(tetromino) + level - 1) % len(COLORS) + 1
    offset = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
    pixel_offset = [offset[0] * BLOCK_SIZE, offset[1] * BLOCK_SIZE]
    animation_speed = 10
    score = 0
    fall_speed = 500
    fast_fall = False
    last_fall_time = pygame.time.get_ticks()
    game_over = False
    move_left = move_right = False
    move_delay = 100
    last_move_time = pygame.time.get_ticks()
    direction = 0

    # Main game loop
    while True:
        if game_over:
            game_over_sound.play()
            display_game_over(score)
            return  # Exit `run_game` after the game ends
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    move_left = True
                    direction = -1
                elif event.key == pygame.K_RIGHT:
                    move_right = True
                    direction = 1
                elif event.key == pygame.K_DOWN:
                    fast_fall = True
                elif event.key == pygame.K_UP:
                    rotated = rotate_tetromino(tetromino)
                    if valid_position(rotated, offset, grid):
                        tetromino[:] = rotated[:]
                elif event.key == pygame.K_p:
                    pause_game()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    move_left = False
                    direction = 0
                elif event.key == pygame.K_RIGHT:
                    move_right = False
                    direction = 0
                elif event.key == pygame.K_DOWN:
                    fast_fall = False

        # Game logic (falling tetrominoes, scoring, etc.)
        current_time = pygame.time.get_ticks()
        current_fall_speed = 50 if fast_fall else fall_speed

        if move_left or move_right:
            if current_time - last_move_time > move_delay:
                if move_left and valid_position(tetromino, [offset[0] - 1, offset[1]], grid):
                    offset[0] -= 1
                if move_right and valid_position(tetromino, [offset[0] + 1, offset[1]], grid):
                    offset[0] += 1
                last_move_time = current_time

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

                    new_level = lines_cleared_total // 10 + 1
                    if new_level > level:
                        level = new_level
                        fall_speed = int(fall_speed * 0.85)

                    tetromino = next_tetromino
                    color_index = (SHAPES.index(tetromino) + level - 1) % len(COLORS) + 1
                    next_tetromino = tetromino_bag.get_next_tetromino()
                    offset = [GRID_WIDTH // 2 - len(tetromino[0]) // 2, 0]
                    pixel_offset = [offset[0] * BLOCK_SIZE, offset[1] * BLOCK_SIZE]
            last_fall_time = current_time

        target_pixel_offset = [offset[0] * BLOCK_SIZE, offset[1] * BLOCK_SIZE]
        for i in range(2):
            if pixel_offset[i] < target_pixel_offset[i]:
                pixel_offset[i] = min(pixel_offset[i] + animation_speed, target_pixel_offset[i])
            elif pixel_offset[i] > target_pixel_offset[i]:
                pixel_offset[i] = max(pixel_offset[i] - animation_speed, target_pixel_offset[i])

        if move_left or move_right:
            create_wind_particles(pixel_offset[0], pixel_offset[1], direction)

        screen.fill(BLACK)
        draw_grid(grid)
        draw_wind_particles(direction)
        if subwindow_visible:
            draw_subwindow(score, next_tetromino, level, pieces_dropped, lines_cleared_total)
        for cy, row in enumerate(tetromino):
            for cx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        screen, COLORS[color_index - 1],
                        (pixel_offset[0] + cx * BLOCK_SIZE, pixel_offset[1] + cy * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                    )

        pygame.display.flip()
        clock.tick(60)

def main():
    while True:  # Main loop to control game flow
        main_menu()  # Display the main menu
        run_game()  # Start the game after leaving the menu

# Start the program
if __name__ == "__main__":
    main()
