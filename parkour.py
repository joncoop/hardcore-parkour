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

# Stages
START = 0
PLAYING = 1
CLEARED = 2
WIN = 3
LOSE = 4

# Goal type
ITEM = 0
REGION = 1
THRESHOLD = 2
OTHER = 3

goal_type = 1


# Supporting game classes
class Hero(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()

        self.speed = 5
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
        ''' move in horizontal direction and resolve colisions '''
        self.rect.x += self.vx
        hit_list = pygame.sprite.spritecollide(self, tiles, False)

        for hit in hit_list:
            if self.vx > 0:
                self.rect.right = hit.rect.left
            elif self.vx < 0:
                self.rect.left = hit.rect.right
                
        ''' move in vertical direction and resolve colisions '''
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

        #for hit in hit_list:
            #player.score += hit.value
            #hit.apply(self)
        
    def check_edges(self, world):
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > world.get_width():
            self.rect.right = world.get_width()

    def check_goal(self, goal):
        if goal_type == ITEM:
            hit_list = pygame.sprite.spritecollide(self, goal, False)
            self.reached_goal = len(hit_list) > 0
        elif goal_type == REGION:
            self.reached_goal = goal.contains(self.rect)
        elif goal_type == THRESHOLD:
            self.reached_goal = self.rect.left > goal
        elif goal_type == OTHER:
            ''' put your code here '''
            pass
        
    def update(self, game):
        self.apply_gravity(game.level)
        self.move_and_check_tiles(game.tiles)
        self.process_items(game.items)
        self.check_edges(game.world)
        self.check_goal(game.goal)


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


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


class EnemyTypeTwo(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        
class Level():
    def __init__(self, file_path):
        with open(file_path, 'r') as f:
            data = f.read()

        self.map_data = json.loads(data)

        self.load_dimensions()
        self.load_physics()
        self.load_start()
        self.load_main_tiles()
        self.load_items()
        self.load_enemies()
        self.load_goal()

    def load_dimensions(self):
        self.scale =  self.map_data['size']['scale']
        self.width =  self.map_data['size']['width'] * self.scale
        self.height = self.map_data['size']['height'] * self.scale

    def load_physics(self):
        self.gravity = self.map_data['physics']['gravity']
        self.terminal_velocity = self.map_data['physics']['terminal_velocity']
        
    def load_start(self):
        self.start_x = self.map_data['main']['start_x'] * self.scale
        self.start_y = self.map_data['main']['start_y'] * self.scale

    def load_main_tiles(self):
        self.tiles = pygame.sprite.Group()
        for element in self.map_data['main']['tiles']:
            x = element[0] * self.scale
            y = element[1] * self.scale
            kind = element[2]

            if kind == "Concrete":
                s = Tile(x, y, concrete_img)
            elif kind == "Platform":
                s = Tile(x, y, platform_img)
            elif kind == "Car":
                s = Tile(x, y, car_img)
            elif kind == "Dumpster":
                s = Tile(x, y, dumpster_img)
            elif kind == "Truck":
                s = Tile(x, y, truck_img)
            elif kind == "Fridge":
                s = Tile(x, y, fridge_img)
                
            self.tiles.add(s)

    def load_items(self):
        self.items = pygame.sprite.Group()
        for element in self.map_data['main']['items']:
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
        if goal_type == ITEM:
            self.goal = pygame.sprite.Group()
            
            for element in self.map_data['main']['goal']['items']:
                x = element[0] * self.scale
                y = element[1] * self.scale
                kind = element[2]
                
                if kind == "FlagTop":
                    s = Tile(x, y, flag_top_img)
                elif kind == "FlagPole":
                    s = Tile(x, y, flag_pole_img)
                elif kind == "Fridge":
                    s = Tile(x, y, fridge_img)

                self.goal.add(s)
                
        elif goal_type == REGION:
            element = self.map_data['main']['goal']['region']
            x = element[0] * self.scale
            y = element[1] * self.scale
            w = element[2] * self.scale
            h = element[3] * self.scale
            self.goal = pygame.Rect(x, y, w, h)
        
        elif goal_type == THRESHOLD:
            self.goal = self.map_data['main']['goal']['threshold'] * self.scale

        print(self.goal)

    def get_size(self):
        return self.width, self.height
        
    def get_start(self):
        return self.start_x, self.start_y

    def get_tiles(self):
        return self.tiles

    def get_items(self):
        return self.items

    def get_enemies(self):
        return self.enemies

    def get_goal(self):
        return self.goal


# Main game class
class Game():
    def __init__(self, levels):
        self.running = True
        self.levels = levels
    
    def setup(self):
        self.hero = Hero(hero_img)
        self.player = pygame.sprite.GroupSingle()
        self.player.add(self.hero)

        self.stage = START
        self.current_level = 1

    def load_level(self):
        level_index = self.current_level - 1 # -1 because list indices are one less than level number
        level_data = self.levels[level_index] 
        self.level = Level(level_data) 

        world_width, world_height = self.level.get_size()
        self.world = pygame.Surface([world_width, world_height])

        x, y = self.level.get_start()
        self.hero.move_to(x, y)
        self.hero.reached_goal = False
        
        self.tiles = self.level.get_tiles()
        self.items = self.level.get_items()
        self.goal = self.level.get_goal()

    def advance(self):
        if self.current_level < len(self.levels):
            self.current_level += 1
            self.load_level()
            self.stage = PLAYING
        else:
            self.stage = WIN

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
        pass
    
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
                if self.stage == START:
                    if event.key == pygame.K_SPACE:
                        self.stage = PLAYING
                        
                elif self.stage == PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.hero.jump(self.tiles)

                elif self.stage == WIN or self.stage == LOSE:
                    if event.key == pygame.K_SPACE:
                        self.setup()

        pressed = pygame.key.get_pressed()
        
        if self.stage == PLAYING:
            if pressed[pygame.K_LEFT]:
                self.hero.move_left()
            elif pressed[pygame.K_RIGHT]:
                self.hero.move_right()
            else:
                self.hero.stop()
     
    def update(self):
        if self.stage == PLAYING:
            self.player.update(self)
            #self.enemies.update(self)

            if self.hero.reached_goal:
                self.stage = CLEARED
                self.cleared_timer = FPS * 2
                
        elif self.stage == CLEARED:
            self.cleared_timer -= 1

            if self.cleared_timer == 0:
                self.advance()
            
    def render(self):
        self.world.fill(GRAY)
        self.player.draw(self.world)
        self.tiles.draw(self.world)
        self.items.draw(self.world)

        if goal_type == ITEM:
            self.goal.draw(self.world)
        elif goal_type == REGION:
            pygame.draw.rect(self.world, BLACK, self.goal)
        elif goal_type == THRESHOLD:
            pass
        elif goal_type == OTHER:
            pass

        offset_x, offset_y = self.calculate_offset()
        screen.blit(self.world, [offset_x, offset_y])

        if self.stage == START:
            self.show_title_screen()        
        elif self.stage == CLEARED:
            self.show_cleared_screen()
        elif self.stage == WIN:
            self.show_win_screen()
        elif self.stage == LOSE:
            self.show_lose_screen()

        pygame.display.flip()
            
    def run(self):
        self.load_level()
        
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
