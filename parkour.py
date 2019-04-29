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
hero_img = pygame.image.load('assets/images/andy.png').convert_alpha()

''' tiles '''
concrete_img = pygame.image.load('assets/images/platformPack_tile016.png').convert_alpha()
platform_img = pygame.image.load('assets/images/platformPack_tile041.png').convert_alpha()
car_img = pygame.image.load('assets/images/car.png').convert_alpha()
dumpster_img = pygame.image.load('assets/images/dumpster.png').convert_alpha()
truck_img = pygame.image.load('assets/images/truck.png').convert_alpha()
fridge_img = pygame.image.load('assets/images/refrigerator_box.png').convert_alpha()

''' items '''
dundy_img = pygame.image.load('assets/images/dundy.png').convert_alpha()

# Levels
levels = ["assets/levels/level_1.json",
          "assets/levels/level_2.json"]

# Stages
START = 0
PLAYING = 1
CLEARED = 3
WIN = 4
LOSE = 5

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

        self.speed = 5
        self.jump_power = 24
        self.vx = 0
        self.vy = 0

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
    
    def update(self, game):
        self.apply_gravity(game.level)
        self.move_and_check_tiles(game.tiles)
        self.process_items(game.items)
        self.check_edges(game.world)


class Dundy(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def apply(self):
        pass
        
    def update(self):
        pass


class Level():
    def __init__(self, file_path):
        with open(file_path, 'r') as f:
            data = f.read()

        self.map_data = json.loads(data)
        self.goal_reached = False
        self.load()

    def load(self):
        ''' set dimensions '''
        self.scale =  self.map_data['size']['scale']
        self.width =  self.map_data['size']['width'] * self.scale
        self.height = self.map_data['size']['height'] * self.scale

        ''' set physics '''
        self.gravity = self.map_data['physics']['gravity']
        self.terminal_velocity = self.map_data['physics']['terminal_velocity']
        
        ''' set starting location '''
        self.start_x = self.map_data['main']['start_x'] * self.scale
        self.start_y = self.map_data['main']['start_y'] * self.scale

        ''' load tiles '''
        self.tiles = pygame.sprite.Group()
        for element in self.map_data['main']['tiles']:
            x, y, kind = element[0] * self.scale, element[1] * self.scale, element[2]

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

        ''' load items '''
        self.items = pygame.sprite.Group()
        for element in self.map_data['main']['items']:
            x, y, kind = element[0] * self.scale, element[1] * self.scale, element[2]
            
            if kind == "Dundy":
                s = Dundy(x, y, dundy_img)
            elif kind == "Other":
                pass
                
            self.items.add(s)

        ''' load goal tiles '''
        self.goal = pygame.sprite.Group()
        for element in self.map_data['main']['goal']:
            x, y, kind = element[0] * self.scale, element[1] * self.scale, element[2]
            
            if kind == "Fridge":
                s = Tile(x, y, fridge_img)
            elif kind == "Other":
                pass
                
            self.goal.add(s)

    def get_size(self):
        return self.width, self.height
        
    def get_start(self):
        return self.start_x, self.start_y

    def get_tiles(self):
        return self.tiles

    def get_items(self):
        return self.items

    def get_goal(self):
        return self.goal


# Main game class
class Game():
    def __init__(self):
        self.screen = pygame.display.set_mode(SIZE)
        self.pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
    
    def setup(self):
        self.hero = Hero(hero_img)
        self.player = pygame.sprite.GroupSingle()
        self.player.add(self.hero)

        self.stage = START
        self.current_level = 1

    def load_level(self):
        level_data = levels[self.current_level - 1] # -1 because list indices are one less than level number
        self.level = Level(level_data) 

        world_width, world_height = self.level.get_size()
        self.world = pygame.Surface([world_width, world_height])

        x, y = self.level.get_start()
        self.hero.move_to(x, y)
        
        self.tiles = self.level.get_tiles()
        self.items = self.level.get_items()
        self.goal = self.level.get_goal()

    def advance(self):
        pass

    def show_title_screen(self):
        text = FONT_LG.render(TITLE, 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.bottom = 128
        screen.blit(text, rect)
        
        text = FONT_MD.render("Press space to start.", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.bottom = 156
        screen.blit(text, rect)
        
    def show_clear_screen():
        text = FONT_LG.render("Level cleared", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.bottom = 144
        screen.blit(text, rect)

    def show_win_screen(self):
        text = FONT_LG.render("You win", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.bottom = 144
        screen.blit(text, rect)

    def show_lose_screen(self):
        text = FONT_LG.render("You lose", 1, BLACK)
        rect = text.get_rect()
        rect.centerx = WIDTH // 2
        rect.bottom = 144
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
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if self.stage == START:
                    if event.key == pygame.K_SPACE:
                        self.stage = PLAYING
                        
                elif self.stage == PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.hero.jump(self.tiles)

                elif self.stage == CLEARED:
                    if event.key == pygame.K_SPACE:
                        self.stage = PLAYING

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
            
    def render(self):
        self.world.fill(GRAY)
        self.player.draw(self.world)
        self.tiles.draw(self.world)
        self.items.draw(self.world)
        self.goal.draw(self.world)

        offset_x, offset_y = self.calculate_offset()
        self.screen.blit(self.world, [offset_x, offset_y])
        
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
            self.clock.tick(FPS)

            
# Let's do this!
if __name__ == "__main__":
    g = Game()
    g.setup()
    g.run()
    
    pygame.quit()
    sys.exit()
