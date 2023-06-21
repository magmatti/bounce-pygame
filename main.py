import os
import random
import math
import time
import sys
import pygame
from os import listdir
from os.path import isfile, join


pygame.init()
pygame.display.set_caption("Bounce!")

WIDTH, HEIGHT = 1366, 760
FPS = 60
PLAYER_VEL = 6

window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]
    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []

        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
    
    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(272, 64, size, size)
    surface.blit(image, (0, 0), rect)

    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 2

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.lives = 3
        self.hit = False
        self.hit_count = 0
        super().__init__()

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        
        if self.jump_count == 1:
            self.fall_count = 0
    
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    # def reset_pos(self, dx, dy):
    #     self.rect.x = dx
    #     self.rect.y = dy

    def make_hit(self):
        self.lives -= 1
        self.hit = True
        self.hit_head = 0

    def move_left(self, vel):
        self.x_vel = -vel

        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"

        if self.hit:
            sprite_sheet = "hit"

        if self.y_vel != 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel  > 0:
            sprite_sheet = "fall"
        
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def loop(self, fps):
        # gravity acceleration, picks up the pace depending on how long player is falling
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    # drawing player as a circle
    def draw(self, win, offset_x):
        pygame.draw.circle(win, self.COLOR, (self.rect.x + 36 - offset_x, self.rect.y + 40), 26)
        # win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))
        
 

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        # setting animation count to 0 so it does't lag the game
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    # adding 1 to make sure there are no gaps
    # for loops to get expected numbers of pixels to fill the screen
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

# update screen with background and player
def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)
    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            # if moving down -> colliding with top of object
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            # collision with bottom of object
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()

    collided_object = None

    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    
    player.move(-dx, 0)
    player.update()

    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()
    player.x_vel = 0

    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()


class Menu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.menu_font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 60)
        self.selected_option = 0
        self.options = ["Start Game", "Quit"]
        self.running = False

    def draw_menu(self, screen):
        title_text = self.title_font.render("Bounce!", True, (255, 255, 255))
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 100))

        for i, option in enumerate(self.options):
            text = self.menu_font.render(option, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2 + i * 50))
            if i == self.selected_option:
                pygame.draw.rect(screen, (255, 0, 0), (text_rect.x - 10, text_rect.y - 10, text_rect.width + 20, text_rect.height + 20))
            screen.blit(text, text_rect)

    def process_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    if self.selected_option == 0:
                        self.running = True
                    elif self.selected_option == 1:
                        pygame.quit()
                        sys.exit()

    def run_menu(self, window):
        while not self.running:
            window.fill((0, 0, 0))

            self.draw_menu(window)
            self.process_input()

            pygame.display.flip()


class GameOver:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 36)
        self.text_color = (255, 255, 255)
        self.text = self.font.render("Game Finished!", True, self.text_color)
        self.text_rect = self.text.get_rect(center=(width // 2, height // 2 + 50))
        self.exit_text = self.font.render("Press 'Enter' to exit", True, self.text_color)
        self.exit_text_rect = self.exit_text.get_rect(center=(width // 2, height // 2 + 90))

    def display(self, window):
        window.blit(self.text, self.text_rect)
        window.blit(self.exit_text, self.exit_text_rect)

    def run(self, window):
        clock = pygame.time.Clock()
        running = True

        while running:
            clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        running = False

            window.fill((0, 0, 0))
            self.display(window)
            pygame.display.flip()


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    
    fire = Fire(100, HEIGHT - block_size - 64, 16, 32)
    fire2 = Fire(1670, HEIGHT - block_size - 64, 16, 32)
    fire3 = Fire(2060, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH // block_size, WIDTH * 6 // block_size)]

    # Level objects (level design)
    objects = [*floor, 
               Block(0, HEIGHT - block_size * 2, block_size), 
               Block(0, HEIGHT - block_size * 3, block_size),
               Block(0, HEIGHT - block_size * 4, block_size),
               Block(0, HEIGHT - block_size * 5, block_size),
               Block(0, HEIGHT - block_size * 6, block_size),
               Block(0, HEIGHT - block_size * 7, block_size),
               Block(0, HEIGHT - block_size * 8, block_size),
               Block(block_size * 3, HEIGHT - block_size * 3, block_size), 
               Block(block_size * 3, HEIGHT - block_size * 4, block_size),
               Block(block_size * 3, HEIGHT - block_size * 5, block_size),
               Block(block_size * 3, HEIGHT - block_size * 6, block_size),
               Block(block_size * 3, HEIGHT - block_size * 7, block_size),
               Block(block_size * 3, HEIGHT - block_size * 8, block_size),
               Block(block_size * 4, HEIGHT - block_size * 3, block_size),
               Block(block_size * 5, HEIGHT - block_size * 3, block_size),
               Block(block_size * 6, HEIGHT - block_size * 3, block_size),
               Block(block_size * 6, HEIGHT - block_size * 4, block_size),
               Block(block_size * 6, HEIGHT - block_size * 5, block_size),
               Block(block_size * 6, HEIGHT - block_size * 6, block_size),
               Block(block_size * 6, HEIGHT - block_size * 7, block_size),
               Block(block_size * 6, HEIGHT - block_size * 8, block_size),
               Block(block_size * 8, HEIGHT - block_size * 2, block_size),
               Block(block_size * 8, HEIGHT - block_size * 3, block_size),
               Block(block_size * 9, HEIGHT - block_size * 2, block_size),
               Block(block_size * 9, HEIGHT - block_size * 3, block_size),
               Block(block_size * 14, HEIGHT - block_size * 2, block_size),
               Block(block_size * 14, HEIGHT - block_size * 3, block_size),
               Block(block_size * 15, HEIGHT - block_size * 3, block_size),
               Block(block_size * 16, HEIGHT - block_size * 3, block_size),
               Block(block_size * 18, HEIGHT - block_size * 3, block_size),
               Block(block_size * 19, HEIGHT - block_size * 3, block_size),
               Block(block_size * 19, HEIGHT - block_size * 2, block_size),
               Block(block_size * 20, HEIGHT - block_size * 3, block_size),
               Block(block_size * 22, HEIGHT - block_size * 3, block_size),
               Block(block_size * 23, HEIGHT - block_size * 3, block_size),
               Block(block_size * 24, HEIGHT - block_size * 3, block_size),
               Block(block_size * 24, HEIGHT - block_size * 2, block_size),
               Block(block_size * 26, HEIGHT - block_size * 3, block_size),
               Block(block_size * 26, HEIGHT - block_size * 4, block_size),
               Block(block_size * 26, HEIGHT - block_size * 5, block_size),
               Block(block_size * 26, HEIGHT - block_size * 6, block_size),
               Block(block_size * 26, HEIGHT - block_size * 7, block_size),
               Block(block_size * 26, HEIGHT - block_size * 8, block_size),
               Block(block_size * 27, HEIGHT - block_size * 3, block_size),
               Block(block_size * 27, HEIGHT - block_size * 4, block_size),
               Block(block_size * 27, HEIGHT - block_size * 5, block_size),
               Block(block_size * 27, HEIGHT - block_size * 6, block_size),
               Block(block_size * 27, HEIGHT - block_size * 7, block_size),
               Block(block_size * 27, HEIGHT - block_size * 8, block_size),
               Fire(2800, HEIGHT - block_size - 64, 16, 32),
               Fire(2930, HEIGHT - block_size - 64, 16, 32),
               Fire(3060, HEIGHT - block_size - 64, 16, 32),
               Fire(3180, HEIGHT - block_size - 64, 16, 32),
               Fire(3310, HEIGHT - block_size - 64, 16, 32),
               Fire(3440, HEIGHT - block_size - 64, 16, 32),
               Fire(4200, HEIGHT - block_size - 64, 16, 32),
               Fire(4770, HEIGHT - block_size - 64, 16, 32),
               Fire(4820, HEIGHT - block_size - 64, 16, 32),
               Fire(5500, HEIGHT - block_size - 64, 16, 32),
               Fire(5700, HEIGHT - block_size - 64, 16, 32),
               Fire(5900, HEIGHT - block_size - 64, 16, 32),
               Fire(5950, HEIGHT - block_size - 64, 16, 32),
               Fire(6000, HEIGHT - block_size - 64, 16, 32),
               Fire(6390, HEIGHT - block_size - 160, 16, 32),
               Fire(6350, HEIGHT - block_size - 160, 16, 32),
               Fire(6600, HEIGHT - block_size - 64, 16, 32),
               Block(block_size * 37, HEIGHT - block_size * 3, block_size),
               Block(block_size * 37, HEIGHT - block_size * 4, block_size),
               Block(block_size * 37, HEIGHT - block_size * 5, block_size),
               Block(block_size * 37, HEIGHT - block_size * 6, block_size),
               Block(block_size * 37, HEIGHT - block_size * 7, block_size),
               Block(block_size * 37, HEIGHT - block_size * 8, block_size),  
               Block(block_size * 38, HEIGHT - block_size * 3, block_size),
               Block(block_size * 38, HEIGHT - block_size * 4, block_size),
               Block(block_size * 38, HEIGHT - block_size * 5, block_size),
               Block(block_size * 38, HEIGHT - block_size * 6, block_size),
               Block(block_size * 38, HEIGHT - block_size * 7, block_size),
               Block(block_size * 38, HEIGHT - block_size * 8, block_size),  
               Block(block_size * 40, HEIGHT - block_size * 2, block_size),
               Block(block_size * 40, HEIGHT - block_size * 3, block_size),
               Block(block_size * 41, HEIGHT - block_size * 2, block_size),
               Block(block_size * 41, HEIGHT - block_size * 3, block_size),
               Block(block_size * 43, HEIGHT - block_size * 4, block_size),
               Block(block_size * 43, HEIGHT - block_size * 5, block_size), 
               Block(block_size * 43, HEIGHT - block_size * 6, block_size),
               Block(block_size * 43, HEIGHT - block_size * 7, block_size),
               Block(block_size * 43, HEIGHT - block_size * 8, block_size),
               Block(block_size * 44, HEIGHT - block_size * 4, block_size),
               Block(block_size * 44, HEIGHT - block_size * 5, block_size),
               Block(block_size * 44, HEIGHT - block_size * 6, block_size),
               Block(block_size * 44, HEIGHT - block_size * 7, block_size), 
               Block(block_size * 44, HEIGHT - block_size * 8, block_size), 
               Block(block_size * 46, HEIGHT - block_size * 2, block_size),
               Block(block_size * 46, HEIGHT - block_size * 3, block_size),
               Block(block_size * 47, HEIGHT - block_size * 2, block_size),
               Block(block_size * 47, HEIGHT - block_size * 3, block_size),  
               Block(block_size * 49, HEIGHT - block_size * 4, block_size),
               Block(block_size * 49, HEIGHT - block_size * 5, block_size),
               Block(block_size * 49, HEIGHT - block_size * 6, block_size),
               Block(block_size * 49, HEIGHT - block_size * 7, block_size),
               Block(block_size * 49, HEIGHT - block_size * 8, block_size),
               Block(block_size * 50, HEIGHT - block_size * 4, block_size),
               Block(block_size * 50, HEIGHT - block_size * 5, block_size),
               Block(block_size * 50, HEIGHT - block_size * 6, block_size),
               Block(block_size * 50, HEIGHT - block_size * 7, block_size),
               Block(block_size * 50, HEIGHT - block_size * 8, block_size),
               Block(block_size * 52, HEIGHT - block_size * 2, block_size),
               Block(block_size * 52, HEIGHT - block_size * 3, block_size),
               Block(block_size * 55, HEIGHT - block_size * 2, block_size),
               Block(block_size * 56, HEIGHT - block_size * 2, block_size),
               Block(block_size * 56, HEIGHT - block_size * 3, block_size),
               Block(block_size * 58, HEIGHT - block_size * 2, block_size),
               Block(block_size * 58, HEIGHT - block_size * 3, block_size),
               Block(block_size * 58, HEIGHT - block_size * 4, block_size),
               Block(block_size * 60, HEIGHT - block_size * 2, block_size),
               Block(block_size * 60, HEIGHT - block_size * 3, block_size),
               Block(block_size * 60, HEIGHT - block_size * 4, block_size),
               Block(block_size * 60, HEIGHT - block_size * 5, block_size),
               Block(block_size * 64, HEIGHT - block_size * 2, block_size),
               Block(block_size * 65, HEIGHT - block_size * 2, block_size),
               Block(block_size * 65, HEIGHT - block_size * 3, block_size),
               Block(block_size * 66, HEIGHT - block_size * 2, block_size),
               Block(block_size * 67, HEIGHT - block_size * 2, block_size),
               Block(block_size * 67, HEIGHT - block_size * 3, block_size),
               Block(block_size * 67, HEIGHT - block_size * 4, block_size),
               Block(block_size * 69, HEIGHT - block_size * 4, block_size),
               Block(block_size * 69, HEIGHT - block_size * 5, block_size),
               Block(block_size * 69, HEIGHT - block_size * 6, block_size),
               Block(block_size * 69, HEIGHT - block_size * 7, block_size),
               Block(block_size * 69, HEIGHT - block_size * 8, block_size),
               Block(block_size * 70, HEIGHT - block_size * 4, block_size),
               Block(block_size * 70, HEIGHT - block_size * 5, block_size),
               Block(block_size * 70, HEIGHT - block_size * 6, block_size),
               Block(block_size * 70, HEIGHT - block_size * 7, block_size),
               Block(block_size * 70, HEIGHT - block_size * 8, block_size),
               Block(block_size * 71, HEIGHT - block_size * 4, block_size),
               Block(block_size * 71, HEIGHT - block_size * 6, block_size),
               Block(block_size * 73, HEIGHT - block_size * 3, block_size),
               Block(block_size * 73, HEIGHT - block_size * 5, block_size),
               Block(block_size * 73, HEIGHT - block_size * 7, block_size),
               Block(block_size * 74, HEIGHT - block_size * 2, block_size),
               Block(block_size * 74, HEIGHT - block_size * 3, block_size),
               Block(block_size * 74, HEIGHT - block_size * 4, block_size),
               Block(block_size * 74, HEIGHT - block_size * 5, block_size),
               Block(block_size * 74, HEIGHT - block_size * 6, block_size),
               Block(block_size * 74, HEIGHT - block_size * 7, block_size),
               Block(block_size * 76, HEIGHT - block_size * 8, block_size),
               Block(block_size * 76, HEIGHT - block_size * 7, block_size),
               Block(block_size * 76, HEIGHT - block_size * 6, block_size),
               Block(block_size * 76, HEIGHT - block_size * 5, block_size),
               Block(block_size * 76, HEIGHT - block_size * 4, block_size),
               Block(block_size * 77, HEIGHT - block_size * 4, block_size),
               Block(block_size * 78, HEIGHT - block_size * 4, block_size),
               Block(block_size * 79, HEIGHT - block_size * 4, block_size),
               Block(block_size * 80, HEIGHT - block_size * 4, block_size),
               Block(block_size * 81, HEIGHT - block_size * 4, block_size),
               Block(block_size * 82, HEIGHT - block_size * 4, block_size),
               Block(block_size * 83, HEIGHT - block_size * 4, block_size),
               Block(block_size * 84, HEIGHT - block_size * 4, block_size),
               fire,
               fire2, 
               fire3]

    offset_x = 0
    scroll_area_width = 200

    menu = Menu(WIDTH, HEIGHT)
    menu.run_menu(window)

    run = True

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            # handling jump in main loop so player can't hold space for jumping
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)        
        draw(window, background, bg_image, player, objects, offset_x)

        game_over = GameOver(WIDTH, HEIGHT)
        game_over_condition = False

        if player.rect.bottom > HEIGHT or player.lives == 0:
            game_over_condition = True

        if game_over_condition:
            game_over.run(window)
            break

        # scrolling background
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
            (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel


    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
