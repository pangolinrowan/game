# MyPygame: entities
# Calen Cuesta
# ProgLang
# 9.14.24

import pygame
import random
import math
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0,0]
        self.collisions = {'up' : False, 'down' : False, 'right' : False, 'left' : False}
        self.flip = False
        self.action = ''
        self.set_action('idle')
        self.anim_offset = (-3, -3)
        self.attack_offset = (-8 , -19)
        self.attacking = False
        self.attackingFrames = 0
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def update(self, tilemap, movement=(0,0)):
        self.collisions = {'up' : False, 'down' : False, 'right' : False, 'left' : False}
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()

        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
        
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        self.animation.update()
    def render(self, surf, offset=(0,0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        #surf.blit(self.game.assets['player'], (self.pos[0] - offset[0], self.pos[1] - offset[1]))



class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0

    def update(self, tilemap, movement=(0,0)):
        enemy_rect = self.rect()
        if self.walking:
            if tilemap.solid_check((enemy_rect.centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip =  not self.flip 
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1] < 16)):
                    if (self.flip and dis[0] < 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[enemy_rect.centerx - 7, enemy_rect.centery], -1.5, 0, self.flip])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random(),(255,255,255)))
                    if (not self.flip and dis[0] > 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[enemy_rect.centerx + 7, enemy_rect.centery], 1.5, 0, self.flip])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random(),(255,255,255)))
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        super().update(tilemap, movement=movement)
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
        #for rect in self.game.player_projectiles:
            #if enemy_rect.colliderect(rect):
                #print("enemy projectile collision!")
                #return True
            
    def render(self, surf, offset=(0,0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1] + 1))
        img = pygame.transform.scale(self.game.assets['bow'], (4,8))
        img = pygame.transform.rotate(img, -15)
        if self.flip:
            surf.blit(pygame.transform.flip(img, self.flip, False ), ( self.rect().centerx - 5 - img.get_width() - offset[0], self.rect().centery - offset[1] - img.get_height() / 2) )
        else:
            surf.blit(img, (self.rect().centerx + 5 - offset[0], self.rect().centery - offset[1] - img.get_height() / 2))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 2
    def update(self, tilemap, movement=(0,0)):
        super().update(tilemap, movement=movement)
        
        self.air_time += 1
        if self.air_time >= 120:
            self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        if self.attackingFrames >= 36:
            self.attacking = False
        if self.collisions['down']:
            if self.action == 'jump':
                self.game.sfx['landing'].play()
            self.air_time = 0
            self.jumps = 2
        if self.attacking == True:
            self.set_action('attack')
            self.attackingFrames += 1
        elif self.air_time > 4:
            self.set_action('jump')
            self.attackingFrames = 0
        elif movement[0] != 0:
            self.set_action('run')
            self.attackingFrames = 0
        else:
            self.set_action('idle')
            self.attackingFrames = 0
    def jump(self):
        if self.jumps:
            self.velocity[1] = -2.5
            self.jumps -= 1
            self.air_time = 5
            return True
    def attack(self):
        self.attacking = True

    def render(self, surf, offset=(0,0)):
        #surf.blit
        if self.attacking and self.flip:
            surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.attack_offset[0], self.pos[1] - offset[1] + self.attack_offset[1]))
        elif self.attacking:
            surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.attack_offset[0] - 5, self.pos[1] - offset[1] + self.attack_offset[1]))
        else:
            surf.blit(pygame.transform.flip(self.game.assets['player/weapon'], self.flip, False) , (self.rect().centerx - offset[0] - (self.rect().width + 4 if self.flip else 2), self.rect().centery - offset[1] - 8))
            super().render(surf, offset=offset)
