# MyPygame: particle
# Calen Cuesta
# ProgLang
# 10/4/24
import pygame
class Particle:
    def __init__(self, game, p_type, pos, velocity=[0,0], frame=0):
        self.game = game
        self.type = p_type
        self.pos = list(pos)
        self.velocity = list(velocity)
        self.animation = self.game.assets['particle/' + p_type].copy()
        self.animation.frame = frame

    def update(self):
        kill = False
        if self.animation.done:
            kill = True

        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        self.animation.update()

        return kill

    def render(self, surf, offset=(0, 0)):
        img  = self.animation.img()
        surf.blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2))
class Projectile(Particle):
    def __init__(self, game, p_type, pos, velocity=[0,0], frame=0):
        super().__init__(game, 'fireball', pos, velocity)
        self.projectileFTD = 175
        self.scaleFactor = 8
        self.scaleSize = (32,16)
    def rect(self):
            return pygame.Rect(self.pos[0], self.pos[1], self.scaleSize[0], self.scaleSize[1])
    def update(self, tilemap):
        kill = [False,None,'']
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        fireball_rect = self.rect()
        for rect in self.game.enemy_rects.values():
            if fireball_rect.colliderect(rect):
                kill = [True, rect,'enemy']
        for rect in tilemap.physics_rects_around((self.pos[0] + self.scaleSize[0] / 2, self.pos[1] + self.scaleSize[1] / 2)):
            if fireball_rect.colliderect(rect):
                kill = [True, rect,'tile']
        if self.projectileFTD == 0 and not kill[0]:
            kill = [True,None,'time']
        self.projectileFTD -= 1
        self.animation.update()
        return kill
    def render(self, surf, offset=(0,0)):
        img  = self.animation.img()
        img = pygame.transform.scale(img, (32,16))
        surf.blit(pygame.transform.flip(img, (True if self.velocity[0] < 0 else False), False), (self.pos[0] - offset[0], self.pos[1] - offset[1]))
