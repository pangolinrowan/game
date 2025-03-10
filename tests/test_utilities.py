import pytest
import pygame
import os
from scripts.utilities import load_image, load_image2, load_images, load_images2, Animation

class TestUtilities:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        pygame.init()
        
        pygame.display.set_caption("Unit Test")
        scr_res = (640,480)
        pygame.display.set_mode(scr_res)
        
        yield
        
        pygame.quit()
    
    # Verify load_image loads images with black colorkey
    def test_load_image(self):
        img = load_image('tiles/grass/0.png')
        assert isinstance(img, pygame.Surface)
        assert img.get_colorkey() == (0, 0, 0, 255)
    
    # Verify load_image2 loads images with white colorkey
    def test_load_image2(self):
        img = load_image2('Bow.png')
        assert isinstance(img, pygame.Surface)
        assert img.get_colorkey() == (255, 255, 255, 255)
    
    # Verify load_images loads multiple images with black colorkey
    def test_load_images(self):
        images = load_images('tiles/grass')
        assert isinstance(images, list)
        assert len(images) > 0
        assert all(isinstance(img, pygame.Surface) for img in images)
        assert all(img.get_colorkey() == (0, 0, 0, 255) for img in images)
    
    # Verify load_images2 loads multiple images with white colorkey
    def test_load_images2(self):
        images = load_images2('particles/fireball')
        assert isinstance(images, list)
        assert len(images) > 0
        assert all(isinstance(img, pygame.Surface) for img in images)
        assert all(img.get_colorkey() == (255, 255, 255, 255) for img in images)
    
    # Verify Animation initialization and update functions
    def test_animation(self):
        images = [pygame.Surface((10, 10)) for _ in range(3)]
        
        anim = Animation(images, img_dur=5, loop=True)
        assert len(anim.images) == 3
        assert anim.img_duration == 5
        assert anim.loop == True
        assert anim.frame == 0
        
        anim.update()
        assert anim.frame == 1
        
        for _ in range(20):
            anim.update()
        assert anim.frame < (5 * len(images))
    
    # Verify Animation.copy() creates independent instance with same properties
    def test_animation_copy(self):
        images = [pygame.Surface((10, 10)) for _ in range(3)]
        original = Animation(images, img_dur=7, loop=False)
        
        copied = original.copy()
        
        assert copied is not original
        assert copied.images == original.images
        assert copied.img_duration == original.img_duration
        assert copied.loop == original.loop
        assert copied.frame == 0
        
        original.frame = 10
        assert copied.frame == 0
    
    # Verify Animation.img() returns correct image based on frame
    def test_animation_img(self):
        images = []
        for i in range(3):
            surf = pygame.Surface((10, 10))
            surf.fill((i*50, i*50, i*50))
            images.append(surf)
        
        anim = Animation(images, img_dur=5, loop=True)
        
        assert anim.img() == images[0]
        
        anim.frame = 7
        assert anim.img() == images[1]
        
        anim.frame = 12
        assert anim.img() == images[2]
    
    # Verify non-looping Animation stops at final frame
    def test_animation_update_noloop(self):
        images = [pygame.Surface((10, 10)) for _ in range(3)]
        anim = Animation(images, img_dur=5, loop=False)
        
        max_frames = anim.img_duration * len(images) - 1
        for _ in range(max_frames):
            anim.update()
            
        assert anim.frame == max_frames
        assert anim.done == True
        
        anim.update()
        assert anim.frame == max_frames