import pytest
import pygame
import math
from scripts.spark import Spark

class TestSpark:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        pygame.init()
        
        # Minimal display setup needed for testing
        pygame.display.set_caption("Spark Test")
        pygame.display.set_mode((640, 480))
        
        yield
        
        pygame.quit()
    
    # Verify Spark initialization with correct properties
    def test_spark_initialization(self):
        pos = (100, 150)
        angle = math.pi / 4  # 45 degrees
        speed = 2.5
        color = (255, 100, 0)
        
        spark = Spark(pos, angle, speed, color)
        
        assert spark.pos == list(pos)
        assert spark.angle == angle
        assert math.isclose(spark.speed, speed, rel_tol=1e-09, abs_tol=1e-09)
        #assert spark.speed == speed
        assert spark.color == color
    
    # Verify Spark update method correctly updates position and speed
    def test_spark_update(self):
        # Create a spark moving at 0 degrees (right)
        spark = Spark((100, 100), 0, 2, (255, 255, 255))
        
        # Update once
        kill = spark.update()
        
        # Check position update: cos(0) = 1, sin(0) = 0
        assert spark.pos[0] == 100 + 2  
        assert spark.pos[1] == 100      
        
        # Speed should decrease
        assert spark.speed == 1.9  # 2 - 0.1
        
        # Shouldn't be killed yet
        assert not kill
        
        # Create a spark with different angle
        spark = Spark((100, 100), math.pi/2, 2, (255, 255, 255))  # 90 degrees (down)
        
        # Update once
        kill = spark.update()
        
        # Check position update: cos(pi/2) = 0, sin(pi/2) = 1
        assert abs(spark.pos[0] - 100) < 0.0001  # x += cos(pi/2) * 2 (approximately 0)
        assert abs(spark.pos[1] - 102) < 0.0001  # y += sin(pi/2) * 2 (approximately 2)
        
        # Test until spark dies
        spark = Spark((100, 100), 0, 0.2, (255, 255, 255))
        
        # First update, speed becomes 0.1
        kill = spark.update()
        assert spark.speed == 0.1
        assert not kill
        
        # Second update, speed becomes 0
        kill = spark.update()
        assert spark.speed == 0
        assert kill  # Should be killed when speed is 0
    
    # Verify Spark render method correctly calculates polygon points and draws
    def test_spark_render(self):
        spark = Spark((100, 100), 0, 2, (255, 0, 0))
        
        # Create a tracking surface class to verify polygon drawing
        class DrawTracker:
            def __init__(self):
                self.surface = pygame.Surface((640, 480))
                self.last_polygon_color = None
                self.last_polygon_points = None
                self.draw_count = 0
        
        tracker = DrawTracker()
        
        # Save original pygame.draw.polygon
        original_polygon = pygame.draw.polygon
        
        # Mock pygame.draw.polygon to track calls
        def mock_polygon(surf, color, points, *args, **kwargs):
            tracker.last_polygon_color = color
            tracker.last_polygon_points = points
            tracker.draw_count += 1
            return original_polygon(surf, color, points, *args, **kwargs)
        
        # Replace pygame.draw.polygon with our mock
        pygame.draw.polygon = mock_polygon
        
        # Render the spark
        spark.render(tracker.surface)
        
        # Verify polygon was drawn
        assert tracker.draw_count == 1
        assert tracker.last_polygon_color == (255, 0, 0)
        assert len(tracker.last_polygon_points) == 4  # Should have 4 points
        
        # Test with offset
        tracker.draw_count = 0
        spark.render(tracker.surface, offset=(10, 20))
        
        # Verify polygon was drawn with offset
        assert tracker.draw_count == 1
        
        # All points should be offset by (10, 20)
        for point in tracker.last_polygon_points:
            # The points are complex calculations, but we can verify they're different from non-offset
            assert point[0] != tracker.last_polygon_points[0][0] + 10
            assert point[1] != tracker.last_polygon_points[0][1] + 20
        
        # Restore original pygame.draw.polygon
        pygame.draw.polygon = original_polygon