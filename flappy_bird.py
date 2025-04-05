import pygame
import random

# --- Constants ---
WIDTH = 400
HEIGHT = 600
FPS = 60
BIRD_X = 50
GRAVITY = 0.5
JUMP_FORCE = -9
PIPE_WIDTH = 60
PIPE_GAP = 200
PIPE_VELOCITY = -3
GROUND_HEIGHT = 50  # Height of the ground at the bottom

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# --- Game States ---
MENU = 0
PLAYING = 1
GAME_OVER = 2

class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([30, 30])
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = BIRD_X
        self.rect.y = HEIGHT // 2
        self.velocity = 0

    def update(self):
        self.velocity += GRAVITY
        self.rect.y += self.velocity

        # Keep bird within screen bounds (top only; bottom is handled by ground)
        if self.rect.top < 0:
            self.rect.top = 0
            self.velocity = 0

    def jump(self):
        self.velocity = JUMP_FORCE

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, is_top):
        super().__init__()
        self.image = pygame.Surface([PIPE_WIDTH, y])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        if is_top:
            self.rect.bottom = y  # Top pipes are anchored to their bottom edge
        else:
            self.rect.y = y  # Bottom pipes are anchored to their top edge
        self.is_top = is_top

    def update(self):
        self.rect.x += PIPE_VELOCITY
        if self.rect.right < 0:
            self.kill()  # Remove pipes that have moved off-screen

class Ground(pygame.sprite.Sprite):  # New Ground class
    def __init__(self, height):
        super().__init__()
        self.image = pygame.Surface((WIDTH, height))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.bottom = HEIGHT
        self.rect.x = 0
        self.height = height  # Store height for collision detection

    def update(self):
        # Optionally add scrolling ground logic here
        pass


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Flappy Bird")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)  # Use default system font
        self.reset()
        self.state = MENU  # Start in the menu state

    def reset(self):
        self.all_sprites = pygame.sprite.Group()
        self.pipes = pygame.sprite.Group()
        self.bird = Bird()
        self.all_sprites.add(self.bird)
        self.ground = Ground(GROUND_HEIGHT)  # Create the ground
        self.all_sprites.add(self.ground)
        self.score = 0
        self.pipe_timer = 0  # Time since last pipe was created
        self.game_over = False

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == MENU:
                        if event.key == pygame.K_SPACE:
                            self.state = PLAYING
                    elif self.state == PLAYING:
                        if event.key == pygame.K_SPACE:
                            self.bird.jump()
                    elif self.state == GAME_OVER:
                        if event.key == pygame.K_SPACE:
                            self.reset()
                            self.state = PLAYING

            if self.state == PLAYING:
                self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()

    def update(self):
        self.all_sprites.update()
        self.pipe_timer += 1

        # Create new pipes
        if self.pipe_timer >= 100:  # Adjust for pipe spawn rate
            self.pipe_timer = 0
            pipe_height = random.randint(50, HEIGHT - PIPE_GAP - 50 - self.ground.height)  # Adjust for ground
            top_pipe = Pipe(WIDTH, pipe_height, True)
            bottom_pipe = Pipe(WIDTH, pipe_height + PIPE_GAP, False)
            self.pipes.add(top_pipe, bottom_pipe)
            self.all_sprites.add(top_pipe, bottom_pipe)

        # Check for collisions
        if pygame.sprite.spritecollideany(self.bird, self.pipes):
            self.state = GAME_OVER
        # Ground collision
        if self.bird.rect.bottom >= HEIGHT - self.ground.height:
            self.bird.rect.bottom = HEIGHT - self.ground.height
            self.bird.velocity = 0  # Stop vertical movement
            self.state = GAME_OVER  # End the game on ground collision

        # Update score
        for pipe in self.pipes:
            if pipe.rect.right < self.bird.rect.left and pipe.is_top:
                if not pipe.rect.colliderect(pygame.Rect(0,0,0,0)): #very small rect. Makes it so score isn't incremented multiple times per pipe
                    self.score += 0.5 #increment by half, so whole number is shown


    def draw(self):
        self.screen.fill(BLUE)
        self.all_sprites.draw(self.screen)

        if self.state == MENU:
            self.draw_text("Press SPACE to Start", WIDTH // 2, HEIGHT // 2)
        elif self.state == PLAYING:
            self.draw_text(str(int(self.score)), WIDTH // 2, 50)
        elif self.state == GAME_OVER:
            self.draw_text("Game Over", WIDTH // 2, HEIGHT // 2 - 30)
            self.draw_text(f"Score: {int(self.score)}", WIDTH//2, HEIGHT//2)
            self.draw_text("Press SPACE to Restart", WIDTH // 2, HEIGHT // 2 + 30)

        pygame.display.flip()

    def draw_text(self, text, x, y):
        text_surface = self.font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)

  

if __name__ == '__main__':
    game = Game()
    game.run()