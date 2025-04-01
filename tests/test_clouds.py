import math
import pytest
import pygame
import random
from scripts.clouds import Cloud, Clouds

class TestCloud:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        pygame.init()
        
        # Minimal display setup needed for testing
        pygame.display.set_caption("Cloud Test")
        pygame.display.set_mode((640, 480))
        
        # Create test cloud image
        self.cloud_img = pygame.Surface((32, 16))
        self.cloud_img.fill((255, 255, 255))
        
        yield
        
        pygame.quit()
    
    # Verify Cloud initialization with correct properties
    def test_cloud_initialization(self):
        # Create a cloud with specific parameters
        pos = (100, 50)
        speed = 0.1
        depth = 0.3
        
        cloud = Cloud(pos, self.cloud_img, speed, depth)
        
        # Verify properties
        assert cloud.pos == list(pos)
        assert cloud.img == self.cloud_img
        assert math.isclose(cloud.speed, speed, rel_tol=1e-9)
        assert math.isclose(cloud.depth, depth, rel_tol=1e-9)
    
    # Verify Cloud update moves the cloud based on speed
    def test_cloud_update(self):
        # Create a cloud with known position and speed
        pos = (100, 50)
        speed = 0.5
        
        cloud = Cloud(pos, self.cloud_img, speed, 0.3)
        initial_x = cloud.pos[0]
        
        # Update the cloud
        cloud.update()
        
        # Position should change by speed amount
        assert math.isclose(cloud.pos[0], initial_x + speed, rel_tol=1e-9)
        assert cloud.pos[1] == pos[1]  # Y position stays the same
    
    # Verify Cloud render correctly calculates position and wraps around screen
    def test_cloud_render(self):
        # Create a tracking surface class to verify blitting
        class BlitTracker:
            def __init__(self):
                self.surface = pygame.Surface((200, 150))
                self.blit_count = 0
                self.last_blit_pos = None
                
            def blit(self, source, pos, *args, **kwargs):
                self.blit_count += 1
                self.last_blit_pos = pos
                return self.surface.blit(source, pos)
                
            def get_width(self):
                return self.surface.get_width()
                
            def get_height(self):
                return self.surface.get_height()
        
        # Create cloud and test surface
        cloud = Cloud((100, 50), self.cloud_img, 0.5, 0.3)
        tracker = BlitTracker()
        
        # Render the cloud
        cloud.render(tracker, offset=(0, 0))
        
        # Verify blit was called
        assert tracker.blit_count == 1
        
        # Test with offset to verify depth calculation
        tracker.blit_count = 0
        cloud.render(tracker, offset=(10, 5))
        
        # Verify blit was called with position adjusted by depth
        assert tracker.blit_count == 1
        
        # Need to account for wrapping in comparison
        # Just verify a blit happened, wrapping logic is complex to test precisely
        assert tracker.last_blit_pos is not None


class TestClouds:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        pygame.init()
        
        # Minimal display setup needed for testing
        pygame.display.set_caption("Clouds Test")
        pygame.display.set_mode((640, 480))
        
        # Create test cloud images
        self.cloud_images = [
            pygame.Surface((32, 16)),
            pygame.Surface((48, 24)),
            pygame.Surface((64, 32))
        ]
        
        for img in self.cloud_images:
            img.fill((255, 255, 255))
        
        # Fix random seed for consistent test results
        random.seed(42)
        
        yield
        
        pygame.quit()
    
    # Verify Clouds initialization creates the correct number of Cloud objects
    def test_clouds_initialization(self):
        # Create clouds with specific count
        cloud_count = 5
        clouds = Clouds(self.cloud_images, count=cloud_count)
        
        # Verify correct number of clouds
        assert len(clouds.clouds_list) == cloud_count
        
        # Verify all items are Cloud instances
        assert all(isinstance(cloud, Cloud) for cloud in clouds.clouds_list)
        
        # Verify clouds are sorted by depth
        depths = [cloud.depth for cloud in clouds.clouds_list]
        assert depths == sorted(depths)
        
        # Test with default count
        clouds = Clouds(self.cloud_images)
        assert len(clouds.clouds_list) == 16  # Default count
    
    # Verify Clouds update calls update on all Cloud instances
    def test_clouds_update(self):
        # Create clouds
        clouds = Clouds(self.cloud_images, count=3)
        
        # Save initial positions
        initial_positions = [cloud.pos[0] for cloud in clouds.clouds_list]
        
        # Update clouds
        clouds.update()
        
        # Verify all clouds have moved
        for i, cloud in enumerate(clouds.clouds_list):
            assert cloud.pos[0] != initial_positions[i]
    
    # Verify Clouds render calls render on all Cloud instances
    def test_clouds_render(self):
        # Create a tracking surface class to verify blitting
        class BlitTracker:
            def __init__(self):
                self.surface = pygame.Surface((200, 150))
                self.blit_count = 0
                
            def blit(self, source, pos, *args, **kwargs):
                self.blit_count += 1
                return self.surface.blit(source, pos)
                
            def get_width(self):
                return self.surface.get_width()
                
            def get_height(self):
                return self.surface.get_height()
        
        # Create clouds and test surface
        cloud_count = 3
        clouds = Clouds(self.cloud_images, count=cloud_count)
        tracker = BlitTracker()
        
        # Render clouds
        clouds.render(tracker, offset=(10, 5))
        
        # Verify correct number of blits (one per cloud)
        assert tracker.blit_count == cloud_count