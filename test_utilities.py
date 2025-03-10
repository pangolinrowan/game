import pytest
import pygame
from scripts.utilities import load_image, load_images, Animation

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