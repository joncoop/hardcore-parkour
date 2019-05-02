# Imports
import pygame
import json
import os
import sys

# Initialize game engine
pygame.mixer.pre_init()
pygame.init()

# Window
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
TITLE = "Hardcore Parkour"
FPS = 60

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
pygame.display.set_caption(TITLE)

# Helper functions for loading assets
def load_font(font_face, font_size):
    return pygame.font.Font(font_face, font_size)

def load_image(path):
    return pygame.image.load(path).convert_alpha()

def load_sound(path):
    return pygame.mixer.Sound(path)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Fonts
FONT_SM = load_font(None, 24)
FONT_MD = load_font(None, 32)
FONT_LG = load_font("assets/fonts/BreeSerif-Regular.ttf", 64)

# Sounds
CRUNCH_SND = load_sound('assets/sounds/crunch.ogg')

# Images
hero_img = load_image('assets/images/characters/andy.png')

tile_images = { "Concrete": load_image('assets/images/tiles/platformPack_tile016.png'),
                "Platform": load_image('assets/images/tiles/platformPack_tile041.png'),
                "Car": load_image('assets/images/tiles/car.png'),
                "Dumpster": load_image('assets/images/tiles/dumpster.png'),
                "Truck": load_image('assets/images/tiles/truck.png'),
                "Fridge": load_image('assets/images/tiles/refrigerator_box.png') }
        
enemy_images = { "Michael": load_image('assets/images/characters/michael.png'),
                 "Dwight": load_image('assets/images/characters/dwight.png')} 

item_images = { "Dundy": load_image('assets/images/items/dundy.png') }

# Levels
levels = ["assets/levels/level_1.json",
          "assets/levels/level_1.json",
          "assets/levels/level_1.json"]
    
# Sprite classes
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Hero(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()

        self.speed = 8
        self.jump_power = 24
        self.vx = 0
        self.vy = 0

        self.reached_goal = False
        self.score = 0
        
    def move_to(self, x, y):
        self.rect.x = x
        self.rect.y = y
        
    def move_left(self):
        self.vx = -self.speed
    
    def move_right(self):
        self.vx = self.speed

    def stop(self):
        self.vx = 0

    def can_jump(self, tiles):
        self.rect.y += 2
        hit_list = pygame.sprite.spritecollide(self, tiles, False)
        self.rect.y -= 2

        return len(hit_list) > 0
        
    def jump(self, tiles):
        if self.can_jump(tiles):
            self.vy = -self.jump_power

    def apply_gravity(self, level):
        self.vy += level.gravity

        if self.vy > level.terminal_velocity:
            self.vy = level.terminal_velocity

    def move_and_check_tiles(self, level):
        self.rect.x += self.vx
        hit_list = pygame.sprite.spritecollide(self, level.main_tiles, False)

        for hit in hit_list:
            if self.vx > 0:
                self.rect.right = hit.rect.left
            elif self.vx < 0:
                self.rect.left = hit.rect.right
            self.vx = 0
                
        self.rect.y += self.vy
        hit_list = pygame.sprite.spritecollide(self, level.main_tiles, False)

        for hit in hit_list:
            if self.vy > 0:
                self.rect.bottom = hit.rect.top
            elif self.vy < 0:
                self.rect.top = hit.rect.bottom
            self.vy = 0

    def process_items(self, level):
        hit_list = pygame.sprite.spritecollide(self, level.items, True)

        for hit in hit_list:
            self.score += hit.value
            hit.apply(self)

    def check_world_edges(self, level):
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > level.width:
            self.rect.right = level.width

    def check_goal(self, level):
        self.reached_goal = level.goal.contains(self.rect)
        
    def update(self, level):
        self.apply_gravity(level)
        self.move_and_check_tiles(level)
        self.check_world_edges(level)
        self.process_items(level)
        self.check_goal(level)

class Dundy(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.value = 10

    def apply(self, hero):
        hero.score += self.value
        
    def update(self, level):
        '''
        Items may not do anything. If so, this function can
        be deleted. However if an item is animated or it moves,
        then here is where you can implement that.
        '''
        pass

class BasicEnemy(pygame.sprite.Sprite):
    '''
    BasicEnemies move back and forth, turning around whenever
    they hit a block or the edge of the world. Gravity affects
    BasicEnemies, so they will walk off platforms.
    '''
    
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vx = -4
        self.vy = 0

    def reverse(self):
        self.vx = -1 * self.vx
        
    def apply_gravity(self, level):
        self.vy += level.gravity

        if self.vy > level.terminal_velocity:
            self.vy = level.terminal_velocity

    def move_and_check_tiles(self, level):
        self.rect.x += self.vx
        hit_list = pygame.sprite.spritecollide(self, level.main_tiles, False)

        for hit in hit_list:
            if self.vx > 0:
                self.rect.right = hit.rect.left
                self.reverse()
            elif self.vx < 0:
                self.rect.left = hit.rect.right
                self.reverse()
                
        self.rect.y += self.vy
        hit_list = pygame.sprite.spritecollide(self, level.main_tiles, False)

        for hit in hit_list:
            if self.vy > 0:
                self.rect.bottom = hit.rect.top
            elif self.vy < 0:
                self.rect.top = hit.rect.bottom

            self.vy = 0
            
    def check_world_edges(self, level):
        if self.rect.left < 0:
            self.rect.left = 0
            self.reverse()
        elif self.rect.right > level.width:
            self.rect.right = level.width
            self.reverse()
            
    def update(self, level):
        self.apply_gravity(level)
        self.move_and_check_tiles(level)
        self.check_world_edges(level)

class PlatformEnemy(BasicEnemy):
    '''
    PlatformEnemies behave the same as BasicEnemies, except
    that they are aware of platform edges and will turn around
    when the edge is reached. Only init and the overridden
    function move_and_check_walls needs to be included.
    '''
    
    def __init__(self, x, y, image):
        super().__init__(x, y, image)

    def move_and_check_tiles(self, level):
        reverse = False

        self.rect.x += self.vx
        hit_list = pygame.sprite.spritecollide(self, level.main_tiles, False)

        for hit in hit_list:
            if self.vx > 0:
                self.rect.right = hit.rect.left
                reverse = True
            elif self.vx < 0:
                self.rect.left = hit.rect.right
                reverse = True

        self.rect.y += 2
        hit_list = pygame.sprite.spritecollide(self, level.main_tiles, False)
        
        reverse = True

        for hit in hit_list:
            if self.vy >= 0:
                self.rect.bottom = hit.rect.top
                self.vy = 0

                if self.vx > 0 and self.rect.right <= hit.rect.right:
                    reverse = False
                elif self.vx < 0 and self.rect.left >= hit.rect.left:
                    reverse = False

            elif self.vy < 0:
                self.rect.top = hit.rect.bottom
                self.vy = 0

        if reverse:
            self.reverse()

# Level class
class Level():
    def __init__(self, file_path):
        with open(file_path, 'r') as f:
            data = f.read()

        self.map_data = json.loads(data)

        self.load_layout()
        self.load_music()
        self.load_background()
        self.load_physics()
        self.load_tiles()
        self.load_items()
        self.load_enemies()
        self.load_goal()
        
        self.generate_layers()
        self.pre_render_inactive_layers()

    def load_layout(self):
        self.scale =  self.map_data['layout']['scale']
        self.width =  self.map_data['layout']['size'][0] * self.scale
        self.height = self.map_data['layout']['size'][1] * self.scale
        self.start_x = self.map_data['layout']['start'][0] * self.scale
        self.start_y = self.map_data['layout']['start'][1] * self.scale

    def load_music(self):
        pygame.mixer.music.load(self.map_data['music'])
        
    def load_physics(self):
        self.gravity = self.map_data['physics']['gravity']
        self.terminal_velocity = self.map_data['physics']['terminal_velocity']

    def load_background(self):
        self.bg_color = self.map_data['background']['color']
        bg_image_path = self.map_data['background']['image']

        if os.path.isfile(bg_image_path):
            self.bg_image = pygame.image.load(bg_image_path).convert()
        else:
            self.bg_image = None

        self.parallax_speed = self.map_data['background']['parallax_speed']
        
    def load_tiles(self):
        self.midground_tiles = pygame.sprite.Group()
        self.main_tiles = pygame.sprite.Group()
        self.foreground_tiles = pygame.sprite.Group()

        for group_name in self.map_data['tiles']:
            tile_group = self.map_data['tiles'][group_name]
            
            for element in tile_group:
                x = element[0] * self.scale
                y = element[1] * self.scale
                kind = element[2]

                img = tile_images[kind]
                t = Tile(x, y, img)

                if group_name == 'midground':
                    self.midground_tiles.add(t)
                elif group_name == 'main':
                    self.main_tiles.add(t)
                elif group_name == 'foreground':
                    self.foreground_tiles.add(t)
            
    def load_items(self):
        self.items = pygame.sprite.Group()
        
        for element in self.map_data['items']:
            x = element[0] * self.scale
            y = element[1] * self.scale
            kind = element[2]
            img = item_images[kind]
            
            if kind == "Dundy":
                s = Dundy(x, y, img)
                
            self.items.add(s)

    def load_enemies(self):
        self.enemies = pygame.sprite.Group()
        
        for element in self.map_data['enemies']:
            x = element[0] * self.scale
            y = element[1] * self.scale
            kind = element[2]
            img = enemy_images[kind]
            
            if kind == "Michael":
                s = BasicEnemy(x, y, img)
            elif kind == "Dwight":
                s = PlatformEnemy(x, y, img)
                
            self.enemies.add(s)

    def load_goal(self):
        g = self.map_data['layout']['goal']

        if isinstance(g, int):
            x = g * self.scale
            y = 0
            w = self.width - x
            h = self.height
        elif isinstance(g, list):
            x = g[0] * self.scale
            y = g[1] * self.scale
            w = g[2] * self.scale
            h = g[3] * self.scale

        self.goal = pygame.Rect([x, y, w, h])

    def generate_layers(self):
        self.world = pygame.Surface([self.width, self.height])
        self.background = pygame.Surface([self.width, self.height])
        self.inactive = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)
        self.active = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)
        self.foreground = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)

    def pre_render_inactive_layers(self):
        self.background.fill(self.bg_color)
        
        if self.bg_image != None:
            bg_width = self.bg_image.get_width()
            bg_height = self.bg_image.get_height()
            
            for x in range(0, self.width, bg_width):
                for y in range(0, self.height, bg_height):
                    self.background.blit(self.bg_image, [x, y])
                    
        self.midground_tiles.draw(self.inactive)
        self.main_tiles.draw(self.inactive)        
        self.foreground_tiles.draw(self.foreground)

# Main game class
class Game():

    START = 0
    PLAYING = 1
    CLEARED = 2
    WIN = 3
    LOSE = 4

    def __init__(self, levels):
        self.clock = pygame.time.Clock()
        self.running = True
        self.levels = levels
    
    def setup(self):
        self.hero = Hero(hero_img)
        self.player = pygame.sprite.GroupSingle()
        self.player.add(self.hero)

        self.stage = Game.START
        self.current_level = 1
        self.load_level()

    def start_music(self):
        pygame.mixer.music.play(-1)

    def stop_music(self):
        pygame.mixer.music.stop()
    
    def load_level(self):
        level_index = self.current_level - 1
        level_data = self.levels[level_index] 
        self.level = Level(level_data) 

        self.hero.move_to(self.level.start_x, self.level.start_y)
        self.hero.reached_goal = False

        self.active_sprites = pygame.sprite.Group()
        self.active_sprites.add(self.hero, self.level.items, self.level.enemies)

    def start_level(self):
        self.start_music()
        self.stage = Game.PLAYING
            
    def advance(self):
        if self.current_level < len(self.levels):
            self.current_level += 1
            self.load_level()
            self.start_level()
        else:
            self.stage = Game.WIN

    def show_title_screen(self):
        text = FONT_LG.render(TITLE, 1, BLACK)
        rect = text.get_rect()
        rect.centerx = SCREEN_WIDTH // 2
        rect.centery = 128
        screen.blit(text, rect)
        
        text = FONT_MD.render("Press space to start.", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = SCREEN_WIDTH // 2
        rect.centery = 192
        screen.blit(text, rect)
        
    def show_cleared_screen(self):
        text = FONT_LG.render("Level cleared", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = SCREEN_WIDTH // 2
        rect.centery = 144
        screen.blit(text, rect)

    def show_win_screen(self):
        text = FONT_LG.render("You win", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = SCREEN_WIDTH // 2
        rect.centery = 144
        screen.blit(text, rect)

    def show_lose_screen(self):
        text = FONT_LG.render("You lose", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = SCREEN_WIDTH // 2
        rect.centery = 144
        screen.blit(text, rect)

    def show_stats(self):
        level_str = "L: " + str(self.current_level)
        
        text = FONT_MD.render(level_str, 1, BLACK)
        rect = text.get_rect()
        rect.left = 24
        rect.top = 24
        screen.blit(text, rect)
    
        score_str = "S: " + str(self.hero.score)
        
        text = FONT_MD.render(score_str, 1, BLACK)
        rect = text.get_rect()
        rect.right = SCREEN_WIDTH - 24
        rect.top = 24
        screen.blit(text, rect)
    
    def calculate_offset(self):
        x = -1 * self.hero.rect.centerx + SCREEN_WIDTH / 2

        if self.hero.rect.centerx < SCREEN_WIDTH / 2:
            x = 0
        elif self.hero.rect.centerx > self.level.width - SCREEN_WIDTH / 2:
            x = -1 * self.level.width + SCREEN_WIDTH

        return x, 0

    def process_input(self):     
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if self.stage == Game.START:
                    if event.key == pygame.K_SPACE:
                        self.start_level()
                        
                elif self.stage == Game.PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.hero.jump(self.level.main_tiles)

                elif self.stage == Game.WIN or self.stage == Game.LOSE:
                    if event.key == pygame.K_SPACE:
                        self.setup()

        pressed = pygame.key.get_pressed()
        
        if self.stage == Game.PLAYING:
            if pressed[pygame.K_LEFT]:
                self.hero.move_left()
            elif pressed[pygame.K_RIGHT]:
                self.hero.move_right()
            else:
                self.hero.stop()
     
    def update(self):
        if self.stage == Game.PLAYING:
            self.active_sprites.update(self.level)

            if self.hero.reached_goal:
                self.stop_music()
                CRUNCH_SND.play()
                
                self.stage = Game.CLEARED
                self.cleared_timer = 90 # delay (in frames) before advancing to next level
                   
        elif self.stage == Game.CLEARED:
            self.cleared_timer -= 1

            if self.cleared_timer == 0:
                self.advance()
            
    def render(self):
        self.level.active.fill([0, 0, 0, 0]) # Transparent so background shows through
        self.active_sprites.draw(self.level.active)

        offset_x, offset_y = self.calculate_offset()
        bg_offset_x = -1 * offset_x * self.level.parallax_speed
        bg_offset_y = -1 * offset_y * self.level.parallax_speed
        
        self.level.world.blit(self.level.background, [bg_offset_x, bg_offset_y])
        self.level.world.blit(self.level.inactive, [0, 0])
        self.level.world.blit(self.level.active, [0, 0])
        self.level.world.blit(self.level.foreground, [0, 0])
        
        screen.blit(self.level.world, [offset_x, offset_y])

        self.show_stats()
        
        if self.stage == Game.START:
            self.show_title_screen()        
        elif self.stage == Game.CLEARED:
            self.show_cleared_screen()
        elif self.stage == Game.WIN:
            self.show_win_screen()
        elif self.stage == Game.LOSE:
            self.show_lose_screen()

        pygame.display.flip()
            
    def run(self):        
        while self.running:
            self.process_input()
            self.update()
            self.render()
            self.clock.tick(FPS)

            
# Let's do this!
if __name__ == "__main__":
    g = Game(levels)
    g.setup()
    g.run()
    
    pygame.quit()
    sys.exit()
