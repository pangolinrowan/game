# Pygame
# Calen Cuesta
# ProgLang
# 9.14.2024

import pygame
import sys
import random
import math
import os

from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.utilities import load_image, load_images, Animation, load_images2, load_image2
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle, Projectile
from scripts.spark import Spark
class Game:
    def __init__(self):
        pygame.init()
        
        pygame.display.set_caption("Calen's Game")
        self.movement = [False, False, False, False]
        scr_res = (640,480)
        
        self.screen = pygame.display.set_mode(scr_res)
        self.display = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()
        self.assets = {
                'decor': load_images('tiles/decor'),
                'grass': load_images('tiles/grass'),
                'large_decor': load_images('tiles/large_decor'),
                'stone': load_images('tiles/stone'),
                # 'player' : load_image('entities/player.png'),
                'background' : load_image('background.png'),
                'clouds' : load_images('clouds'),
                'enemy/idle' : Animation(load_images2('entities/goblin/idle'), img_dur=6),
                'enemy/run' : Animation(load_images2('entities/goblin/walk'), img_dur=6),
                'player/idle' : Animation(load_images('entities/player3/idle'), img_dur=6),
                'player/run' : Animation(load_images('entities/player3/run'), img_dur=6),
                'player/jump' : Animation(load_images('entities/player3/jump'), img_dur=6),
                'player/attack' : Animation(load_images('entities/player3/attack/StaffMighty'), img_dur=4, loop=False),
                'player/weapon' : load_image('entities/player3/weapon/staff_mighty.png'),
                'particle/leaf' : Animation(load_images('particles/leaf'), img_dur=20, loop=False),
                'particle/particle' : Animation(load_images('particles/particle'), img_dur=20, loop=False),
                'bow': load_image2('Bow.png'),
                'projectile': load_image2('Arrow.png'),
                'particle/fireball' : Animation(load_images2('particles/fireball'), img_dur=4, loop=True)                
        }

        self.sfx = {
            'jump' : pygame.mixer.Sound('data/sfx/jump2.wav'),
            'hit' : pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot' : pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience' : pygame.mixer.Sound('data/sfx/ambience.wav'),
            'fireball' : pygame.mixer.Sound('data/sfx/wind.wav'),
            'explosion' : pygame.mixer.Sound('data/sfx/fire.wav'),
            'landing' : pygame.mixer.Sound('data/sfx/landing.wav'),
        }

        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.2)
        self.sfx['hit'].set_volume(0.7)
        self.sfx['jump'].set_volume(0.3)
        self.sfx['explosion'].set_volume(0.9)
        self.sfx['fireball'].set_volume(0.4)
        self.sfx['landing'].set_volume(0.4)

        
        self.player = Player(self,(50,50), (10,13))
        self.tilemap = Tilemap(self, tile_size=16)
        self.level = 0
        try:
            self.load_level(self.level)
        except FileNotFoundError:
            pass
        self.clouds = Clouds(self.assets['clouds'], count=16)
        self.screenshake = 0
        self.scroll_inc = 30
        self.render_scroll = 0
    
    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor',2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        self.enemies = []
        for spawner in self.tilemap.extract( [('spawners', 0), ('spawners', 1)], keep=False ):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8,15)))
                
        self.projectiles = []
        self.player_projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0,0]
        self.enemy_rects = {}
        self.dead = 0
        self.transition = -30

    def handle_enemies(self):
        for enemy in self.enemies.copy():
            enemy.update(self.tilemap, movement=(0,0))
            enemy.render(self.display, offset=self.render_scroll)
        for enemy in self.enemies:
            self.enemy_rects[enemy] = enemy.rect()
        
    def initial_sound(self):
        pygame.mixer.music.load('data/goblino_music.wav')
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)
    def handle_scroll(self):
        self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / self.scroll_inc
        self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / self.scroll_inc
        self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

    def handle_kill_particles(self):
        for spark in self.sparks.copy():
            kill = spark.update()
            spark.render(self.display, offset=self.render_scroll)
            if kill:
                self.sparks.remove(spark)
        for particle in self.particles.copy():
            kill = particle.update()
            particle.render(self.display, offset=self.render_scroll)
            if particle.type == 'leaf':
                particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
            if kill:
                self.particles.remove(particle)
    
    def handle_player_projectiles(self):
        for projectile in self.player_projectiles.copy():
            kill = projectile.update()
            projectile.render(self.display, offset=self.render_scroll)
            if kill[0]:
                for _ in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.sparks.append(Spark( ((projectile.rect().right if projectile.velocity[0] > 0 else projectile.rect().left), projectile.rect().center[1]) , angle, speed, (255,119,0)))
                if kill[2] == 'enemy':
                    del self.enemy_rects[self.enemies.pop(self.enemies.index(kill[1]))]
                    self.screenshake = max(16, self.screenshake)
                self.sfx['explosion'].play()
                self.player_projectiles.remove(projectile)
    
    def handle_enemy_projectiles(self):
        for projectile in self.projectiles.copy():
            projectile[0][0] += projectile[1]
            projectile[2] += 1
            img = self.assets['projectile']
            img = pygame.transform.flip(img, projectile[3], False)
            img = pygame.transform.scale_by(img, .9)
            self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - self.render_scroll[0], projectile[0][1] - img.get_height() / 2 - self.render_scroll[1]))
            if self.tilemap.solid_check(projectile[0]):
                self.projectiles.remove(projectile)
                for _ in range(4):
                    self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random(),(255,255,255)))
            elif projectile[2] > 360:
                self.projectiles.remove(projectile)
            elif self.player.rect().collidepoint(projectile[0]):
                self.projectiles.remove(projectile)
                self.dead += 1
                self.sfx['hit'].play()
                self.screenshake = max(16, self.screenshake)
                for _ in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.sparks.append(Spark(self.player.rect().center, angle, speed,(255,255,255)))
                    self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0, 7)))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.handle_quit_event()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_event(event)
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                self.handle_keyboard_event(event)

    def handle_quit_event(self):
        pygame.quit()
        sys.exit()

    def handle_mouse_event(self, event):
        if event.button == 1 and not self.player.attacking:
            self.player.attack()
            self.sfx['fireball'].play()
            direction = -1.5 if self.player.flip else 1.5
            offset_x = -16 if self.player.flip else 0
            self.player_projectiles.append(
                Projectile(self, self.tilemap, 'fireball', [self.player.pos[0] + offset_x, self.player.pos[1] - 3], [direction, 0])
            )

    def handle_keyboard_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.handle_keydown(event.key)
        elif event.type == pygame.KEYUP:
            self.handle_keyup(event.key)

    def handle_keydown(self, key):
        if key == pygame.K_a:
            self.movement[0] = True
        elif key == pygame.K_d:
            self.movement[1] = True
        elif key == pygame.K_w and self.player.jump():
            self.sfx['jump'].play()

    def handle_keyup(self, key):
        if key == pygame.K_a:
            self.movement[0] = False
        elif key == pygame.K_d:
            self.movement[1] = False
    
    def handle_level_transition(self):
        if not len(self.enemies):
            self.transition += 1
            if self.transition > 30:
                self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                self.load_level(self.level)
        if self.transition < 0:
            self.transition += 1
            
        if self.dead:
            self.dead += 1
            if self.dead >= 10:
                self.transition = min(30, self.transition + 1)
            if self.dead > 40:
                self.load_level(self.level)
    
    def handle_leaf_spawners(self):
        for rect in self.leaf_spawners:
            if random.random() * 49999 < rect.width * rect.height:
                pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, .3], frame=random.randint(0,20)))

    def handle_transition(self):
        if self.transition:
            transition_surf = pygame.Surface(self.display.get_size())
            pygame.draw.circle(transition_surf, (255,255,255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
            transition_surf.set_colorkey((255, 255, 255))
            self.display.blit(transition_surf, (0,0))

    
    def run(self):
        self.initial_sound()

        while True:
            self.display.blit(self.assets['background'], (0,0))
            
            self.screenshake = max(0, self.screenshake - 1)

            self.handle_level_transition()
            
            self.handle_scroll()
            
            self.handle_leaf_spawners()
            
            self.clouds.update()
            self.clouds.render(self.display, offset=self.render_scroll)
            self.tilemap.render(self.display, offset=self.render_scroll)
            
            self.handle_enemies()
            
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=self.render_scroll)               

            self.handle_enemy_projectiles()
            
            self.handle_player_projectiles()

            self.handle_kill_particles()

            self.handle_input()

            self.handle_transition()
            
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)
            
        
Game().run()

