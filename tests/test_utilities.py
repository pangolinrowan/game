import pytest
import pygame
from scripts.utilities import load_image, load_image2, load_images, load_images2, Animation

class TestUtilities:
    @pytest.fixture
    def setup(self):
        pygame.init()
        
        pygame.display.set_caption("Unit Test")
        self.movement = [False, False, False, False]
        scr_res = (640,480)
        self.screen = pygame.display.set_mode(scr_res)
        self.display = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()
        
        yield self
        
        pygame.quit()
    
    def test_load_image(self, setup):
        # Test image loading
        img = load_image('tiles/grass/0.png')
        assert isinstance(img, pygame.Surface)
        assert img.get_colorkey() == (0, 0, 0, 255)
    
    def test_load_image2(self, setup):
        # Test image2 loading with white colorkey
        img = load_image2('Bow.png')
        assert isinstance(img, pygame.Surface)
        assert img.get_colorkey() == (255, 255, 255, 255)
    
    def test_load_images(self, setup):
        # Test loading multiple images from a directory
        images = load_images('tiles/grass')
        assert isinstance(images, list)
        assert len(images) > 0  # Make sure it found at least one image
        assert all(isinstance(img, pygame.Surface) for img in images)
        assert all(img.get_colorkey() == (0, 0, 0, 255) for img in images)
    
    def test_load_images2(self, setup):
        # Test loading multiple images with white colorkey
        images = load_images2('particles/fireball')
        assert isinstance(images, list)
        assert len(images) > 0  # Make sure it found at least one image
        assert all(isinstance(img, pygame.Surface) for img in images)
        assert all(img.get_colorkey() == (255, 255, 255, 255) for img in images)
    
    def test_animation(self, setup):
        # Create dummy images for testing
        images = [pygame.Surface((10, 10)) for _ in range(3)]
        
        # Test animation initialization
        anim = Animation(images, img_dur=5, loop=True)
        assert len(anim.images) == 3
        assert anim.img_duration == 5
        assert anim.loop == True
        assert anim.frame == 0
        
        # Test animation update
        anim.update()
        assert anim.frame == 1
        
        # Test animation loop
        for _ in range(20):
            anim.update()
        assert anim.frame < (5 * len(images))
    
    def test_animation_copy(self, setup):
        # Create an animation
        images = [pygame.Surface((10, 10)) for _ in range(3)]
        original = Animation(images, img_dur=7, loop=False)
        
        # Test copy method
        copied = original.copy()
        
        # Verify it's a new instance with same properties
        assert copied is not original
        assert copied.images == original.images
        assert copied.img_duration == original.img_duration
        assert copied.loop == original.loop
        assert copied.frame == 0  # Frame should be reset in the copy
        
        # Make sure changes to original don't affect copy
        original.frame = 10
        assert copied.frame == 0
    
    def test_animation_img(self, setup):
        # Create an animation with distinct images
        images = []
        for i in range(3):
            surf = pygame.Surface((10, 10))
            surf.fill((i*50, i*50, i*50))  # Different color for each image
            images.append(surf)
        
        anim = Animation(images, img_dur=5, loop=True)
        
        # Test img() method at different frames
        assert anim.img() == images[0]  # Frame 0 should return first image
        
        anim.frame = 7  # This should be in the second image (7/5 = 1.4 -> int(1.4) = 1)
        assert anim.img() == images[1]
        
        anim.frame = 12  # This should be in the third image (12/5 = 2.4 -> int(2.4) = 2)
        assert anim.img() == images[2]
    
    def test_animation_update_noloop(self, setup):
        # Test non-looping animation
        images = [pygame.Surface((10, 10)) for _ in range(3)]
        anim = Animation(images, img_dur=5, loop=False)
        
        # Run animation to completion
        max_frames = anim.img_duration * len(images) - 1
        for _ in range(max_frames):
            anim.update()
            
        # Verify we're at the last frame
        assert anim.frame == max_frames
        assert anim.done == True
        
        # Verify update doesn't increase frame beyond max
        anim.update()
        assert anim.frame == max_frames  # Should still be at max