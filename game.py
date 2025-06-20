import pygame, random, sys
pygame.init()

# === Game Constants ===
SIZE = 5              # Grid is SIZE x SIZE
TILE = 64              # Pixel size of each tile
W, H = SIZE * TILE, SIZE * TILE
FPS = 30

# === Colors (RGB) ===
BG         = (200, 200, 200)
UNREVEALED = (150, 150, 150)
REVEALED   = (230, 230, 230)
PLAYER     = (50, 150, 250)
ENEMY      = (250, 50, 50)
BOMB       = (0, 0, 0)
FLAG       = (250, 250, 0)
GOAL       = (50, 250, 50)
TEXT       = (20, 20, 20)

# === Pygame Setup ===
screen = pygame.display.set_mode((W, H + 40))
pygame.display.set_caption("Minesneak")
font = pygame.font.SysFont(None, 36)
clock = pygame.time.Clock()

# === Game State Variables ===
grid = []
player = [0, 0]          # Player position (x, y)
enemy = [SIZE - 1, 0, 1] # Enemy position (x, y, direction)
goal = [SIZE - 1, SIZE - 1]
game_over = False
win = False
enemy_alert = False


# === Helper Functions ===

# Get valid neighboring cell coordinates
def neighbors(x, y):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < SIZE and 0 <= ny < SIZE and (dx != 0 or dy != 0):
                yield nx, ny

# Recursively reveal cells
def reveal(x, y):
    cell = grid[y][x]
    if cell['revealed'] or cell['flagged']:
        return
    cell['revealed'] = True
    if cell['adj'] == 0 and not cell['bomb']:
        for nx, ny in neighbors(x, y):
            reveal(nx, ny)

# Move the enemy left/right like a patrol
def enemy_move():
    global enemy_alert

    px, py = player
    ex, ey, _ = enemy

    # Check for proximity to activate alert mode
    if abs(px - ex) + abs(py - ey) <= 1:
        enemy_alert = True

    if not enemy_alert:
        # Patrol horizontally on top row
        if enemy[0] == SIZE - 1:
            enemy[2] = -1
        elif enemy[0] == 0:
            enemy[2] = 1
        enemy[0] += enemy[2]
    else:
        # Chase player: move toward them 1 step at a time (greedy)
        dx = 1 if px > ex else -1 if px < ex else 0
        dy = 1 if py > ey else -1 if py < ey else 0

        # Prefer horizontal movement first
        if dx != 0 and 0 <= ex + dx < SIZE:
            enemy[0] += dx
        elif dy != 0 and 0 <= ey + dy < SIZE:
            enemy[1] += dy


# Check if the player loses
def check_loss():
    if grid[player[1]][player[0]]['bomb']:
        return True
    if player == enemy[:2]:
        return True
    return False

# Check if the player wins
def check_win():
    return player == goal

# Create a new random game board
def build_grid():
    global grid
    grid = [[{'bomb': False, 'revealed': False, 'flagged': False, 'adj': 0}
             for _ in range(SIZE)] for _ in range(SIZE)]
    
    # Pick 3 random bomb positions that aren’t the player or goal
    positions = [(x, y) for y in range(SIZE) for x in range(SIZE)
                 if [x, y] != player and [x, y] != goal]
    for x, y in random.sample(positions, 5):
        grid[y][x]['bomb'] = True

    # Set adjacent bomb counts
    for y in range(SIZE):
        for x in range(SIZE):
            if not grid[y][x]['bomb']:
                grid[y][x]['adj'] = sum(grid[ny][nx]['bomb'] for nx, ny in neighbors(x, y))

# Redraw the entire game screen
def draw():
    screen.fill(BG)

    # Draw tiles
    for y in range(SIZE):
        for x in range(SIZE):
            rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
            cell = grid[y][x]
            color = REVEALED if cell['revealed'] else UNREVEALED
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)

            # Revealed number or bomb
            if cell['revealed']:
                if cell['bomb']:
                    pygame.draw.circle(screen, BOMB, rect.center, TILE // 4)
                elif cell['adj'] > 0:
                    text = font.render(str(cell['adj']), True, TEXT)
                    screen.blit(text, (x * TILE + 20, y * TILE + 15))

    # Draw goal tile
    gx, gy = goal
    pygame.draw.rect(screen, GOAL, (gx * TILE + 8, gy * TILE + 8, TILE - 16, TILE - 16))

    # Draw enemy
    ex, ey = enemy[:2]
    color = (255, 200, 0) if enemy_alert else ENEMY
    pygame.draw.rect(screen, color, (ex * TILE + 8, ey * TILE + 8, TILE - 16, TILE - 16))


    # Draw player
    px, py = player
    pygame.draw.rect(screen, PLAYER, (px * TILE + 8, py * TILE + 8, TILE - 16, TILE - 16))

    # Draw number on top of player (if cell is revealed and has adjacent bombs)
    player_cell = grid[py][px]
    if player_cell['revealed'] and player_cell['adj'] > 0 and not player_cell['bomb']:
        text = font.render(str(player_cell['adj']), True, TEXT)
        screen.blit(text, (px * TILE + 20, py * TILE + 15))

    # Show message if game is over
    if game_over:
        msg = font.render("Game Over! Press R", True, (255, 0, 0))
        screen.blit(msg, (10, H + 5))
    elif win:
        msg = font.render("You Win! Press R", True, (0, 150, 0))
        screen.blit(msg, (10, H + 5))

    pygame.display.flip()

# Start a new game
def reset():
    global player, enemy, game_over, win, enemy_alert
    player = [0, 0]
    enemy = [SIZE - 1, 0, 1]
    enemy_alert = False
    game_over = False
    win = False
    build_grid()
    reveal(player[0], player[1])

# === Main Game Loop ===
def main():
    global game_over, win, player, enemy
    reset()
    running = True
    while running:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            # Handle movement
            elif e.type == pygame.KEYDOWN:
                if not game_over and not win:
                    dx, dy = 0, 0
                    if e.key == pygame.K_LEFT:  dx = -1
                    if e.key == pygame.K_RIGHT: dx = 1
                    if e.key == pygame.K_UP:    dy = -1
                    if e.key == pygame.K_DOWN:  dy = 1
                    nx, ny = player[0] + dx, player[1] + dy
                    if 0 <= nx < SIZE and 0 <= ny < SIZE:
                        enemy_move()
                        player[0], player[1] = nx, ny
                        reveal(nx, ny)
                        if check_loss():
                            game_over = True
                        if check_win():
                            win = True
                else:
                     if e.key == pygame.K_r:
                        reset()



        draw()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
