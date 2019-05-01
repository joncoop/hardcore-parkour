# Imports
import pygame
import json
import sys

# Initialize game engine
pygame.mixer.pre_init()
pygame.init()

# Window settings
WIDTH = 1024
HEIGHT = 576
SIZE = (WIDTH, HEIGHT)
TITLE = "Hardcore Parkour"
FPS = 60

# Actually make the window
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# Colors
TRANSPARENT = (0, 0, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)

# Fonts
FONT_SM = pygame.font.Font(None, 24)
FONT_MD = pygame.font.Font(None, 32)
FONT_LG = pygame.font.Font("assets/fonts/BreeSerif-Regular.ttf", 64)

# Sounds
CRUNCH_SND = pygame.mixer.Sound('assets/sounds/crunch.ogg')

# Images
''' characters '''
hero_img = pygame.image.load('assets/images/characters/andy.png').convert_alpha()

''' enemies '''
enemy1_img = pygame.image.load('assets/images/characters/michael.png').convert_alpha()
enemy2_img = pygame.image.load('assets/images/characters/dwight.png').convert_alpha()

''' tiles '''
concrete_img = pygame.image.load('assets/images/tiles/platformPack_tile016.png').convert_alpha()
platform_img = pygame.image.load('assets/images/tiles/platformPack_tile041.png').convert_alpha()
car_img = pygame.image.load('assets/images/tiles/car.png').convert_alpha()
dumpster_img = pygame.image.load('assets/images/tiles/dumpster.png').convert_alpha()
truck_img = pygame.image.load('assets/images/tiles/truck.png').convert_alpha()
fridge_img = pygame.image.load('assets/images/tiles/refrigerator_box.png').convert_alpha()

''' items '''
dundy_img = pygame.image.load('assets/images/items/dundy.png').convert_alpha()


# Levels
levels = ["assets/levels/level_1.json",
          "assets/levels/level_1.json",
          "assets/levels/level_1.json"]


# Supporting game classes
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

    def move_and_check_tiles(self, tiles):
        self.rect.x += self.vx
        hit_list = pygame.sprite.spritecollide(self, tiles, False)

        for hit in hit_list:
            if self.vx > 0:
                self.rect.right = hit.rect.left
            elif self.vx < 0:
                self.rect.left = hit.rect.right
                
        self.rect.y += self.vy
        hit_list = pygame.sprite.spritecollide(self, tiles, False)

        for hit in hit_list:
            if self.vy > 0:
                self.rect.bottom = hit.rect.top
            elif self.vy < 0:
                self.rect.top = hit.rect.bottom

            self.vy = 0

    def process_items(self, items):
        hit_list = pygame.sprite.spritecollide(self, items, True)

        points = 0
        
        for hit in hit_list:
            hit.apply(self)
            points += hit.value

        return points
        
    def check_edges(self, world):
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > world.get_width():
            self.rect.right = world.get_width()

    def check_goal(self, goal):
        self.reached_goal = goal.contains(self.rect)
        return 0 # Change this to award points for reaching the goal
        
    def update(self, game):
        self.apply_gravity(game.level)
        self.move_and_check_tiles(game.main_tiles)
        self.check_edges(game.world)

        game.score += self.process_items(game.items)
        game.score += self.check_goal(game.goal)


class Dundy(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.value = 10

    def apply(self, hero):
        pass
        
    def update(self):
        '''
        Items may not do anything. If so, this function can
        be deleted. However if an item is animated, or it moves,
        then here is where you can implement that.
        '''
        pass


class EnemyTypeOne(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        pass


class EnemyTypeTwo(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        pass

        
class Level():
    def __init__(self, file_path):
        with open(file_path, 'r') as f:
            data = f.read()

        self.map_data = json.loads(data)

        self.load_layout()
        self.load_physics()
        self.load_tiles()
        self.load_items()
        self.load_enemies()
        self.load_goal()

    def load_layout(self):
        self.scale =  self.map_data['layout']['scale']
        self.width =  self.map_data['layout']['size'][0] * self.scale
        self.height = self.map_data['layout']['size'][1] * self.scale
        self.start_x = self.map_data['layout']['start'][0] * self.scale
        self.start_y = self.map_data['layout']['start'][1] * self.scale
        
    def load_physics(self):
        self.gravity = self.map_data['physics']['gravity']
        self.terminal_velocity = self.map_data['physics']['terminal_velocity']

    def load_background(self):
        self.bg_color = self.map_data['background']['color']
        self.bg_image = self.map_data['background']['image']
               
    def load_tiles(self):
        tile_images = { "Concrete": concrete_img,
                        "Platform": platform_img,
                        "Car": car_img,
                        "Dumpster": dumpster_img,
                        "Truck": truck_img,
                        "Fridge": fridge_img }
        
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
            
            if kind == "Dundy":
                s = Dundy(x, y, dundy_img)
            elif kind == "Other":
                pass
                
            self.items.add(s)

    def load_enemies(self):
        pass

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

    def get_size(self):
        return self.width, self.height
        
    def get_start(self):
        return self.start_x, self.start_y

    def get_midground_tiles(self):
        return self.midground_tiles

    def get_main_tiles(self):
        return self.main_tiles

    def get_foreground_tiles(self):
        return self.foreground_tiles

    def get_items(self):
        return self.items

    def get_enemies(self):
        return self.enemies

    def get_goal(self):
        return self.goal


# Main game class
class Game():

    START = 0
    PLAYING = 1
    CLEARED = 2
    WIN = 3
    LOSE = 4

    def __init__(self, levels):
        self.running = True
        self.levels = levels
    
    def setup(self):
        self.hero = Hero(hero_img)
        self.player = pygame.sprite.GroupSingle()
        self.player.add(self.hero)

        self.stage = Game.START
        self.current_level = 1
        self.score = 0
        self.load_level()

    def load_level(self):
        level_index = self.current_level - 1
        level_data = self.levels[level_index] 
        self.level = Level(level_data) 
        
        x, y = self.level.get_start()
        self.hero.move_to(x, y)
        self.hero.reached_goal = False
        
        self.midground_tiles = self.level.get_midground_tiles()
        self.main_tiles = self.level.get_main_tiles()
        self.foreground_tiles = self.level.get_foreground_tiles()
        self.items = self.level.get_items()
        self.goal = self.level.get_goal()

        self.world_width, self.world_height = self.level.get_size()

        ''' create surface layers '''
        self.world = pygame.Surface([self.world_width, self.world_height])
        self.background = pygame.Surface([self.world_width, self.world_height])
        self.inactive = pygame.Surface([self.world_width, self.world_height], pygame.SRCALPHA, 32)
        self.active = pygame.Surface([self.world_width, self.world_height], pygame.SRCALPHA, 32)
        self.foreground = pygame.Surface([self.world_width, self.world_height], pygame.SRCALPHA, 32)

        ''' pre-render inactive layers '''
        self.background.fill(GRAY)
        self.midground_tiles.draw(self.inactive)
        self.main_tiles.draw(self.inactive)        
        self.foreground_tiles.draw(self.foreground)
                
    def advance(self):
        if self.current_level < len(self.levels):
            self.current_level += 1
            self.load_level()
            self.stage = Game.PLAYING
        else:
            self.stage = Game.WIN

    def show_title_screen(self):
        text = FONT_LG.render(TITLE, 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.centery = 128
        screen.blit(text, rect)
        
        text = FONT_MD.render("Press space to start.", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.centery = 192
        screen.blit(text, rect)
        
    def show_cleared_screen(self):
        text = FONT_LG.render("Level cleared", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.centery = 144
        screen.blit(text, rect)

    def show_win_screen(self):
        text = FONT_LG.render("You win", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.centery = 144
        screen.blit(text, rect)

    def show_lose_screen(self):
        text = FONT_LG.render("You lose", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.centery = 144
        screen.blit(text, rect)

    def show_stats(self):
        text = FONT_MD.render("L" + str(self.current_level), 1, BLACK)
        rect = text.get_rect()
        rect.left = 24
        rect.top = 24
        screen.blit(text, rect)
    
    def calculate_offset(self):
        x = -1 * self.hero.rect.centerx + WIDTH / 2

        if self.hero.rect.centerx < WIDTH / 2:
            x = 0
        elif self.hero.rect.centerx > self.world.get_width() - WIDTH / 2:
            x = -1 * self.world.get_width() + WIDTH

        return x, 0

    def process_input(self):     
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if self.stage == Game.START:
                    if event.key == pygame.K_SPACE:
                        self.stage = Game.PLAYING
                        
                elif self.stage == Game.PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.hero.jump(self.main_tiles)

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
            self.player.update(self)
            #self.enemies.update(self)

            if self.hero.reached_goal:
                self.stage = Game.CLEARED
                self.cleared_timer = FPS * 2
                
        elif self.stage == Game.CLEARED:
            self.cleared_timer -= 1

            if self.cleared_timer == 0:
                self.advance()
            
    def render(self):
        self.player.draw(self.active)
        self.items.draw(self.active)

        self.world.blit(self.background, [0, 0])
        self.world.blit(self.inactive, [0, 0])
        self.world.blit(self.active, [0, 0])
        self.world.blit(self.foreground, [0, 0])

        offset_x, offset_y = self.calculate_offset()
        self.active.fill(TRANSPARENT, [-offset_x, -offset_y, WIDTH, HEIGHT])
        screen.blit(self.world, [offset_x, offset_y])

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
            clock.tick(FPS)

            
# Let's do this!
if __name__ == "__main__":
    g = Game(levels)
    g.setup()
    g.run()
    
    pygame.quit()
    sys.exit()
