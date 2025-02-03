# MyPygame: Utilities
# Calen Cuesta
# ProgLang
# 9.13.24
import pygame
import os
BASE_IMG_PATH = 'data/images/'

def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0,0,0))
    return img

def load_image2(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((255,255,255))
    return img

def load_images(path):
    images = []
    for img_name in os.listdir(BASE_IMG_PATH + path):
        images.append(load_image(path + '/' + img_name))
    return images
def load_images2(path):
    images = []
    for img_name in os.listdir(BASE_IMG_PATH + path):
        img = load_image2(path + '/' + img_name)
        images.append(img)
    return images

class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
            return Animation(self.images, self.img_duration, self.loop)

    def img(self):
            return self.images[int(self.frame / self.img_duration)]

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
