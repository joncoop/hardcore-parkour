# Imports
import pygame


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
                  
''' obstacles '''
car_img = pygame.image.load('assets/images/car.png').convert_alpha()
dumpster_img = pygame.image.load('assets/images/dumpster.png').convert_alpha()
fridge_img = pygame.image.load('assets/images/refrigerator-box.png').convert_alpha()


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
        
    def check_edges(self):
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
    
    def update(self):
        self.apply_gravity()
        self.move_and_check_tiles()
        self.check_edges()


# Game helper functions
def show_title_screen():
    text = FONT_LG.render(TITLE, 1, BLACK)
    rect = text.get_rect()
    rect.centerx = WIDTH // 2
    rect.bottom = 128
    screen.blit(text, rect)
    
    text = FONT_MD.render("Jump on the refridgerator box", 1, BLACK)
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

def setup():
    global hero, player, tiles, goal, stage
    
    ''' Make sprites '''
    hero = Hero(1, 6, hero_img)

    t1 = Tile(0, 8, concrete_img)
    t2 = Tile(1, 8, concrete_img)
    t3 = Tile(2, 8, concrete_img)
    t4 = Tile(3, 8, concrete_img)
    t5 = Tile(4, 8, concrete_img)
    t6 = Tile(5, 8, concrete_img)
    t7 = Tile(6, 8, concrete_img)
    t8 = Tile(7, 8, concrete_img)
    t9 = Tile(8, 8, concrete_img)
    t10 = Tile(9, 8, concrete_img)
    t11 = Tile(10, 8, concrete_img)
    t12 = Tile(11, 8, concrete_img)
    t13 = Tile(12, 8, concrete_img)
    t14 = Tile(13, 8, concrete_img)
    t15 = Tile(14, 8, concrete_img)
    t16 = Tile(15, 8, concrete_img)

    t17 = Tile(12, 3, platform_img)
    t18 = Tile(12, 4, platform_img)
    t19 = Tile(12, 5, platform_img)
    t20 = Tile(12, 6, platform_img)
    t21 = Tile(12, 7, platform_img)
    
    o1 = Tile(3, 6, car_img)
    o2 = Tile(7, 5, dumpster_img)
    
    g = Tile(13.5, 5, fridge_img)
    
    ''' Make sprite groups '''
    player = pygame.sprite.GroupSingle()
    tiles = pygame.sprite.Group()
    goal = pygame.sprite.Group()

    ''' Add sprites to groups '''
    player.add(hero)

    tiles.add(t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16)
    tiles.add(t17, t18, t19, t20, t21)
    tiles.add(o1, o2)

    goal.add(g)
        
    ''' set stage '''
    stage = START

    
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

            
    # Drawing code
    screen.fill(GRAY)
    player.draw(screen)
    tiles.draw(screen)
    goal.draw(screen)
        
    if stage == START:
        show_title_screen()        
    elif stage == END:
        show_end_screen()

    
    # Update screen
    pygame.display.flip()
    clock.tick(refresh_rate)


# Close window and quit
pygame.quit()
