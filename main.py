import numpy as np
import pygame
import sys


class GameOfLifePygame:
    def __init__(self, width=100, height=100, cell_size=8, random_density=0.3):
        """
        Interactive Game of Life with Pygame.

        Args:
            width: Grid width in cells
            height: Grid height in cells
            cell_size: Size of each cell in pixels
            random_density: Initial density of alive cells
        """
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = np.random.choice(
            [0, 1], size=(height, width), p=[1 - random_density, random_density]
        )

        # Pygame setup
        pygame.init()
        self.screen_width = width * cell_size
        self.screen_height = height * cell_size + 50  # Extra space for controls
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )
        pygame.display.set_caption("Conway's Game of Life")

        # Colors
        self.ALIVE = (255, 255, 255)
        self.DEAD = (0, 0, 0)
        self.GRID_COLOR = (40, 40, 40)
        self.TEXT_COLOR = (200, 200, 200)

        # Control state
        self.running = True
        self.paused = True
        self.generation = 0
        self.fps = 10
        self.clock = pygame.time.Clock()

        # Viewport / interaction
        self.offset_x = 0
        self.offset_y = 0
        self.pan_speed = 32
        self.min_cell_size = 1
        self.max_cell_size = 32

        # Font
        self.font = pygame.font.Font(None, 24)

    def count_neighbors(self, grid):
        """Count living neighbors for each cell."""
        padded = np.pad(grid, pad_width=1, mode="constant", constant_values=0)
        neighbors = np.zeros_like(grid)

        for i in range(3):
            for j in range(3):
                if i == 1 and j == 1:
                    continue
                neighbors += padded[i : i + self.height, j : j + self.width]

        return neighbors

    def step(self):
        """Apply one generation of the Game of Life."""
        neighbors = self.count_neighbors(self.grid)
        new_grid = np.zeros_like(self.grid)

        new_grid[(self.grid == 1) & ((neighbors == 2) | (neighbors == 3))] = 1
        new_grid[(self.grid == 0) & (neighbors == 3)] = 1

        self.grid = new_grid
        self.generation += 1

    def draw_grid(self):
        """Draw the grid and cells."""
        self.screen.fill(self.DEAD)

        # Visible area (exclude UI area at bottom)
        grid_area_height = self.screen_height - 50

        # Determine visible cell ranges to reduce drawing
        left = max(0, self.offset_x // self.cell_size)
        top = max(0, self.offset_y // self.cell_size)
        right = min(
            self.width, (self.offset_x + self.screen_width) // self.cell_size + 1
        )
        bottom = min(
            self.height, (self.offset_y + grid_area_height) // self.cell_size + 1
        )

        for y in range(top, bottom):
            for x in range(left, right):
                if self.grid[y, x] == 1:
                    screen_x = x * self.cell_size - self.offset_x
                    screen_y = y * self.cell_size - self.offset_y
                    pygame.draw.rect(
                        self.screen,
                        self.ALIVE,
                        (
                            screen_x,
                            screen_y,
                            self.cell_size - 1,
                            self.cell_size - 1,
                        ),
                    )

    def draw_ui(self):
        """Draw UI elements."""
        ui_y = self.screen_height - 50
        pygame.draw.rect(self.screen, (30, 30, 30), (0, ui_y, self.screen_width, 50))

        status = "PAUSED" if self.paused else "RUNNING"
        text = self.font.render(
            f"Gen: {self.generation} | {status} | FPS: {self.fps} | "
            f"[SPACE] Play/Pause | [R] Reset | [+/-] Speed | [C] Clear",
            True,
            self.TEXT_COLOR,
        )
        self.screen.blit(text, (10, ui_y + 15))

    def reset(self, random_density=0.3):
        """Reset the grid with new random state."""
        self.grid = np.random.choice(
            [0, 1],
            size=(self.height, self.width),
            p=[1 - random_density, random_density],
        )
        self.generation = 0
        self.paused = True

    def clear(self):
        """Clear the grid."""
        self.grid = np.zeros((self.height, self.width), dtype=int)
        self.generation = 0
        self.paused = True

    def clamp_offsets(self):
        """Ensure offsets stay within valid bounds."""
        total_w = self.width * self.cell_size
        total_h = self.height * self.cell_size
        max_x = max(0, total_w - self.screen_width)
        max_y = max(0, total_h - (self.screen_height - 50))
        self.offset_x = max(0, min(self.offset_x, max_x))
        self.offset_y = max(0, min(self.offset_y, max_y))

    def zoom_at(self, focus_x, focus_y, new_cell_size):
        """Zoom while keeping focus (screen) point approximately stable."""
        old = self.cell_size
        if new_cell_size == old:
            return

        # Compute grid position under focus
        grid_x = (focus_x + self.offset_x) / old
        grid_y = (focus_y + self.offset_y) / old

        # Apply new cell size
        self.cell_size = new_cell_size

        # Recompute offsets so that the same grid point remains under the focus
        self.offset_x = int(grid_x * self.cell_size - focus_x)
        self.offset_y = int(grid_y * self.cell_size - focus_y)
        self.clamp_offsets()

    def handle_mouse(self, pos):
        """Toggle cell state on mouse click."""
        x, y = pos
        if y < self.screen_height - 50:  # Only if clicking on grid area (not UI)
            grid_x = (x + self.offset_x) // self.cell_size
            grid_y = (y + self.offset_y) // self.cell_size
            if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
                self.grid[grid_y, grid_x] = 1 - self.grid[grid_y, grid_x]

    def run(self):
        """Main game loop."""
        mouse_pressed = False

        while self.running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_c:
                        self.clear()
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.fps = min(60, self.fps + 5)
                    elif event.key == pygame.K_MINUS:
                        self.fps = max(1, self.fps - 5)
                    elif event.key == pygame.K_LEFT:
                        self.offset_x = max(0, self.offset_x - self.pan_speed)
                    elif event.key == pygame.K_RIGHT:
                        self.offset_x = self.offset_x + self.pan_speed
                        self.clamp_offsets()
                    elif event.key == pygame.K_UP:
                        self.offset_y = max(0, self.offset_y - self.pan_speed)
                    elif event.key == pygame.K_DOWN:
                        self.offset_y = self.offset_y + self.pan_speed
                        self.clamp_offsets()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pressed = True
                    self.handle_mouse(event.pos)

                elif event.type == pygame.MOUSEWHEEL:
                    # Zoom at mouse position
                    mx, my = pygame.mouse.get_pos()
                    if event.y > 0:
                        new_size = min(self.max_cell_size, self.cell_size + 1)
                    else:
                        new_size = max(self.min_cell_size, self.cell_size - 1)
                    self.zoom_at(mx, my, new_size)

                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resize
                    self.screen_width = event.w
                    self.screen_height = event.h
                    self.screen = pygame.display.set_mode(
                        (self.screen_width, self.screen_height), pygame.RESIZABLE
                    )
                    self.clamp_offsets()

                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse_pressed = False

                elif event.type == pygame.MOUSEMOTION and mouse_pressed:
                    self.handle_mouse(event.pos)

            # Update simulation
            if not self.paused:
                self.step()

            # Draw everything
            self.draw_grid()
            self.draw_ui()
            pygame.display.flip()

            # Control frame rate
            self.clock.tick(self.fps)

        pygame.quit()
        sys.exit()


def main():
    """Run the interactive Game of Life."""
    game = GameOfLifePygame(width=1000, height=1000, cell_size=1, random_density=0.3)
    game.run()


if __name__ == "__main__":
    main()
