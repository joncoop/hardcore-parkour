# Imports
import pygame
import json

# Initialize game engine
pygame.init()


# Window
SCALE = 64
WIDTH = 16 * SCALE
HEIGHT = 9 * SCALE
SIZE = (WIDTH, HEIGHT)
TITLE = "Hardcore Parkour"
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption(TITLE)


# Timer
clock = pygame.time.Clock()
refresh_rate = 60


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)


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
fridge_img = pygame.image.load('assets/images/refrigerator-box.png').convert_alpha()

''' items '''
dundy_img = pygame.image.load('assets/images/dundy.png').convert_alpha()


# Game physics
GRAVITY = 1
TERMINAL_VELOCITY = 24

# Stages
START = 0
PLAYING = 1
GOAL = 3
END = 4


# Game classes
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x * SCALE
        self.rect.y = y * SCALE
        
    
class Hero(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x * SCALE
        self.rect.y = y * SCALE

        self.speed = 5
        self.jump_power = 24
        self.vx = 0
        self.vy = 0

    def move_left(self):
        self.vx = -self.speed
    
    def move_right(self):
        self.vx = self.speed

    def stop(self):
        self.vx = 0

    def can_jump(self):
        self.rect.y += 2
        hit_list = pygame.sprite.spritecollide(self, tiles, False)
        self.rect.y -= 2

        return len(hit_list) > 0
        
    def jump(self):
        if self.can_jump():
            self.vy = -self.jump_power

    def apply_gravity(self):
        self.vy += GRAVITY

        if self.vy > TERMINAL_VELOCITY:
            self.vy = TERMINAL_VELOCITY

    def move_and_check_tiles(self):
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

    def process_items(self):
        hit_list = pygame.sprite.spritecollide(self, items, True)
        
    def check_edges(self):
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > world_width:
            self.rect.right = world_width
    
    def update(self):
        self.apply_gravity()
        self.move_and_check_tiles()
        self.process_items()
        self.check_edges()


class Dundy(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x * SCALE
        self.rect.y = y * SCALE

    def apply(self, player):
        pass
        
    def update(self):
        pass


class Level():
    def __init__(self, file):
        with open(file, 'r') as f:
            data = f.read()

        self.map_data = json.loads(data)

    def get_size(self):
        w = self.map_data['width'] * SCALE
        h = self.map_data['height'] * SCALE

        return w, h
        
    def get_start(self):
        x = self.map_data['start_x']
        y = self.map_data['start_y']

        return x, y
    
    def get_tiles(self):
        sprites = pygame.sprite.Group()
        
        for item in self.map_data['tiles']:
            x, y, kind = item[0], item[1], item[2]

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
                
            sprites.add(s)

        return sprites

    def get_items(self):
        sprites = pygame.sprite.Group()

        for item in self.map_data['items']:
            x, y, kind = item[0], item[1], item[2]
            
            if kind == "Dundy":
                s = Dundy(x, y, dundy_img)
            elif kind == "Other":
                pass
                
            sprites.add(s)

        return sprites
    
    def get_goal(self):
        sprites = pygame.sprite.Group()

        for item in self.map_data['goal']:
            x, y, kind = item[0], item[1], item[2]

            if kind == "Fridge":
                s = Tile(x, y, fridge_img)

            sprites.add(s)
            
        return sprites

   
# Game helper functions
def show_title_screen():
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
    
def show_end_screen():
    text = FONT_LG.render("You lose", 1, BLACK)
    rect = text.get_rect()
    rect.centerx = WIDTH // 2
    rect.bottom = 144
    screen.blit(text, rect)

def calculate_offset():
    x = -1 * hero.rect.centerx + WIDTH / 2

    if hero.rect.centerx < WIDTH / 2:
        x = 0
    elif hero.rect.centerx > world_width - WIDTH / 2:
        x = -1 * world_width + WIDTH

    return x, 0

def setup():
    global hero, player, tiles, items, goal
    global world, world_x, world_y, world_width, world_height
    global stage

    level = Level("assets/levels/level_1.json")

    world_width, world_height = level.get_size()
    world = pygame.Surface([world_width, world_height])
    world_x = 0
    world_y = 0

    x, y = level.get_start()
    hero = Hero(x, y, hero_img)
    player = pygame.sprite.GroupSingle()
    player.add(hero)
    
    tiles = level.get_tiles()
    items = level.get_items()
    goal = level.get_goal()
    
    print(str(len(tiles)) + " tiles loaded")
    print(str(len(items)) + " items loaded")
    print(str(len(goal)) + " goals loaded")

    stage = START

def advance(level_file):
    pass

# Game loop
setup()

running = True
while running:
    # Input handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if stage == START:
                if event.key == pygame.K_SPACE:
                    stage = PLAYING
                    
            elif stage == PLAYING:
                if event.key == pygame.K_SPACE:
                    hero.jump()

            elif stage == END:
                if event.key == pygame.K_SPACE:
                    setup()

    pressed = pygame.key.get_pressed()

    if stage == PLAYING:
        if pressed[pygame.K_LEFT]:
            hero.move_left()
        elif pressed[pygame.K_RIGHT]:
            hero.move_right()
        else:
            hero.stop()
        
    
    # Game logic
    if stage == PLAYING or stage == GOAL:
        player.update()

        if stage != GOAL:
            hit_list = pygame.sprite.spritecollide(hero, goal, False)
            
            if len(hit_list) > 0:
                CRUNCH_SND.play()
                stage = GOAL
        else:
            if hero.rect.bottom > 475:
                stage = END

    world_x, world_y = calculate_offset()
        
    # Drawing code
    world.fill(GRAY)
    player.draw(world)
    tiles.draw(world)
    items.draw(world)
    goal.draw(world)

    screen.blit(world, [world_x, world_y])
    
    if stage == START:
        show_title_screen()        
    elif stage == END:
        show_end_screen()

    
    # Update screen
    pygame.display.flip()
    clock.tick(refresh_rate)


# Close window and quit
pygame.quit()
