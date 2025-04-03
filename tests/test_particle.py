import pytest
import pygame
from scripts.utilities import Animation
from scripts.particle import Particle, Projectile

class TestParticle:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        pygame.init()
        
        # Minimal display setup needed for testing
        pygame.display.set_caption("Particle Test")
        pygame.display.set_mode((640, 480))
        
        # Create a mock game class for testing
        class GameMock:
            def __init__(self):
                self.assets = {
                    'particle/leaf': Animation([pygame.Surface((16, 16))], img_dur=5, loop=False),
                    'particle/particle': Animation([pygame.Surface((16, 16))], img_dur=5, loop=False),
                    'particle/fireball': Animation([pygame.Surface((16, 16))], img_dur=4, loop=True)
                }
                self.enemy_rects = {}
        
        self.game_mock = GameMock()
        
        # Create a mock tilemap for collision testing
        class MockTilemap:
            def __init__(self):
                self.collision_rects = []
            
            def physics_rects_around(self, pos):
                return self.collision_rects
        
        self.tilemap_mock = MockTilemap()
        
        yield
        
        pygame.quit()
    
    # Verify Particle initialization with correct properties
    def test_particle_initialization(self):
        # Test with default values
        particle = Particle(self.game_mock, 'leaf', (100, 100))
        
        assert particle.game == self.game_mock
        assert particle.type == 'leaf'
        assert particle.pos == [100, 100]
        assert particle.velocity == [0, 0]
        assert particle.animation.images == self.game_mock.assets['particle/leaf'].images
        assert particle.animation.frame == 0
        
        # Test with custom velocity and frame
        particle = Particle(self.game_mock, 'particle', (150, 200), velocity=[1, -0.5], frame=3)
        
        assert particle.pos == [150, 200]
        assert particle.velocity == [1, -0.5]
        assert particle.animation.frame == 3
    
    # Verify Particle update method correctly updates position and returns kill state
    def test_particle_update(self):
        # Test normal update (not done)
        particle = Particle(self.game_mock, 'leaf', (100, 100), velocity=[2, 1])
        
        # Make sure animation is not done
        particle.animation.done = False
        
        kill = particle.update()
        
        assert particle.pos == [102, 101]  # Position updated by velocity
        assert not kill  # Shouldn't be killed
        
        # Test animation done -> particle killed
        particle.animation.done = True
        
        kill = particle.update()
        
        assert kill  # Should be killed when animation is done
    
    # Verify Particle render method correctly positions and blits the image
    def test_particle_render(self):
        particle = Particle(self.game_mock, 'leaf', (100, 100))
        
        # Create a tracking surface class
        class BlitTracker:
            def __init__(self):
                self.surface = pygame.Surface((640, 480))
                self.blit_count = 0
                self.last_blit_pos = None
                
            def blit(self, source, pos, *args, **kwargs):
                self.blit_count += 1
                self.last_blit_pos = pos
                return self.surface.blit(source, pos)
        
        tracker = BlitTracker()
        
        # Give the animation image a specific size
        img = pygame.Surface((20, 10))
        
        # Mock the animation.img method
        original_img = particle.animation.img
        particle.animation.img = lambda: img
        
        # Render with no offset
        particle.render(tracker)
        
        # Verify blit was called once
        assert tracker.blit_count == 1
        
        # Position should be centered by subtracting half width/height
        expected_x = particle.pos[0] - img.get_width() // 2
        expected_y = particle.pos[1] - img.get_height() // 2
        assert tracker.last_blit_pos == (expected_x, expected_y)
        
        # Test with offset
        tracker.blit_count = 0
        particle.render(tracker, offset=(10, 20))
        
        # Position should be adjusted by offset
        expected_x = particle.pos[0] - 10 - img.get_width() // 2
        expected_y = particle.pos[1] - 20 - img.get_height() // 2
        assert tracker.last_blit_pos == (expected_x, expected_y)
        
        # Restore original method
        particle.animation.img = original_img


class TestProjectile:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        pygame.init()
        
        # Minimal display setup needed for testing
        pygame.display.set_caption("Projectile Test")
        pygame.display.set_mode((640, 480))
        
        # Create a mock game class for testing
        class GameMock:
            def __init__(self):
                self.assets = {
                    'particle/fireball': Animation([pygame.Surface((16, 16))], img_dur=4, loop=True)
                }
                self.enemy_rects = {}
        
        self.game_mock = GameMock()
        
        # Create a mock tilemap for collision testing
        class MockTilemap:
            def __init__(self):
                self.collision_rects = []
            
            def physics_rects_around(self, pos):
                return self.collision_rects
        
        self.tilemap_mock = MockTilemap()
        
        yield
        
        pygame.quit()
    
    # Verify Projectile initialization with correct properties
    def test_projectile_initialization(self):
        projectile = Projectile(self.game_mock, self.tilemap_mock, 'fireball', (100, 100), velocity=[2, 0])
        
        # Verify base particle properties
        assert projectile.game == self.game_mock
        assert projectile.type == 'fireball'
        assert projectile.pos == [100, 100]
        assert projectile.velocity == [2, 0]
        
        # Verify projectile-specific properties
        assert projectile.projectileFTD == 175
        assert projectile.scaleFactor == 8
        assert projectile.scaleSize == (32, 16)
    
    # Verify Projectile rect method returns correct rectangle
    def test_projectile_rect(self):
        # Test with positive velocity (moving right)
        projectile = Projectile(self.game_mock, self.tilemap_mock, 'fireball', (100, 100), velocity=[2, 0])
        
        rect = projectile.rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.x == 100
        assert rect.y == 100
        assert rect.width == 32
        assert rect.height == 16
        
        # Test with negative velocity (moving left)
        projectile = Projectile(self.game_mock, self.tilemap_mock, 'fireball', (100, 100), velocity=[-2, 0])
        
        rect = projectile.rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.x == 100
        assert rect.y == 100
        assert rect.width == 32
        assert rect.height == 16
    
    # Verify Projectile update method handles movement, collisions, and lifespan
    def test_projectile_update(self):
        projectile = Projectile(self.game_mock, self.tilemap_mock, 'fireball', (100, 100), velocity=[2, 1])
        
        # Normal update with no collisions
        kill = projectile.update()
        
        assert projectile.pos == [102, 101]  # Position updated by velocity
        assert not kill[0]  # Shouldn't be killed
        assert projectile.projectileFTD == 174  # Lifespan decreased
        
        # Test collision with enemy
        enemy_rect = pygame.Rect(120, 100, 20, 20)
        self.game_mock.enemy_rects = {'enemy1': enemy_rect}
        
        # Move projectile to collision position
        projectile.pos = [110, 100]
        
        kill = projectile.update()
        
        assert kill[0]  # Should be killed on enemy collision
        assert kill[1] == enemy_rect  # Should return collided object
        assert kill[2] == 'enemy'  # Should identify collision type
        
        # Test collision with tile
        self.game_mock.enemy_rects = {}  # Clear enemy rects
        tile_rect = pygame.Rect(120, 100, 20, 20)
        self.tilemap_mock.collision_rects = [tile_rect]
        
        # Move projectile to collision position
        projectile.pos = [110, 100]
        
        kill = projectile.update()
        
        assert kill[0]  # Should be killed on tile collision
        assert kill[1] == tile_rect  # Should return collided object
        assert kill[2] == 'tile'  # Should identify collision type
        
        # Test death by timeout
        self.tilemap_mock.collision_rects = []  # Clear collision rects
        projectile.projectileFTD = 0
        
        kill = projectile.update()
        
        assert kill[0]  # Should be killed when timer expires
        assert kill[1] is None  # No collision object
        assert kill[2] == 'time'  # Should identify timeout as cause
    
    # Verify Projectile render method correctly positions, flips, and blits the image
    def test_projectile_render(self):
        # Test with positive velocity (moving right)
        projectile = Projectile(self.game_mock, self.tilemap_mock, 'fireball', (100, 100), velocity=[2, 0])
        
        # Create a tracking surface class
        class BlitTracker:
            def __init__(self):
                self.surface = pygame.Surface((640, 480))
                self.blit_count = 0
                self.last_blit_source = None
                self.last_blit_pos = None
                self.last_transform_flip = None
                
            def blit(self, source, pos, *args, **kwargs):
                self.blit_count += 1
                self.last_blit_source = source
                self.last_blit_pos = pos
                return self.surface.blit(source, pos)
        
        tracker = BlitTracker()
        
        # Mock the transform.flip and transform.scale methods to track calls
        original_flip = pygame.transform.flip
        
        def mock_flip(surface, x_flip, y_flip):
            tracker.last_transform_flip = (x_flip, y_flip)
            return original_flip(surface, x_flip, y_flip)

        
        pygame.transform.flip = mock_flip
        
        # Render with no offset
        projectile.render(tracker)
        
        # Verify blit was called once
        assert tracker.blit_count == 1
        
        # Should not be flipped when moving right
        assert tracker.last_transform_flip == (False, False)
        
        # Test with negative velocity (moving left)
        projectile.velocity = [-2, 0]
        tracker.blit_count = 0
        
        projectile.render(tracker)
        
        # Verify blit was called once
        assert tracker.blit_count == 1
        
        # Should be flipped when moving left
        assert tracker.last_transform_flip == (True, False)
        
        # Test with offset
        tracker.blit_count = 0
        projectile.render(tracker, offset=(10, 20))
        
        # Position should be adjusted by offset
        expected_x = projectile.pos[0] - 10
        expected_y = projectile.pos[1] - 20
        assert tracker.last_blit_pos == (expected_x, expected_y)
        
        # Restore original methods
        pygame.transform.flip = original_flip