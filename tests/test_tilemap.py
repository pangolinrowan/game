import pytest
import pygame
import os
import json
import tempfile
from scripts.tilemap import Tilemap

class TestTilemap:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        pygame.init()
        
        # Minimal display setup needed for testing
        pygame.display.set_caption("Tilemap Test")
        pygame.display.set_mode((640, 480))
        
        # Create a simple mock game class with an assets dictionary
        class GameMock:
            def __init__(self):
                self.assets = {
                    'grass': [pygame.Surface((16, 16)) for _ in range(9)],
                    'stone': [pygame.Surface((16, 16)) for _ in range(9)],
                    'decor': [pygame.Surface((16, 16)) for _ in range(3)]
                }
        
        self.game_mock = GameMock()
        
        yield
        
        pygame.quit()
    
    # Verify tilemap initialization with default and custom tile sizes
    def test_tilemap_initialization(self):
        # Test default initialization
        tilemap = Tilemap(self.game_mock)
        assert tilemap.game == self.game_mock
        assert tilemap.tile_size == 16
        assert tilemap.tilemap_dict == {}
        assert tilemap.offgrid_tiles == []
        
        # Test custom tile size
        tilemap = Tilemap(self.game_mock, tile_size=32)
        assert tilemap.tile_size == 32
    
    # Verify extract method correctly identifies and removes tiles
    def test_extract(self):
        tilemap = Tilemap(self.game_mock)
        
        # Add some grid tiles
        tilemap.tilemap_dict['0;0'] = {'type': 'grass', 'variant': 0, 'pos': [0, 0]}
        tilemap.tilemap_dict['1;0'] = {'type': 'stone', 'variant': 1, 'pos': [1, 0]}
        
        # Add some offgrid tiles
        tilemap.offgrid_tiles.append({'type': 'decor', 'variant': 0, 'pos': [25, 25]})
        tilemap.offgrid_tiles.append({'type': 'grass', 'variant': 2, 'pos': [50, 50]})
        
        # Test extraction with removal
        extracted = tilemap.extract([('grass', 0), ('decor', 0)], keep=False)
        
        # Verify correct extraction
        assert len(extracted) == 2
        assert any(tile['type'] == 'grass' and tile['variant'] == 0 for tile in extracted)
        assert any(tile['type'] == 'decor' and tile['variant'] == 0 for tile in extracted)
        
        # Verify tiles were removed
        assert '0;0' not in tilemap.tilemap_dict
        assert len(tilemap.offgrid_tiles) == 1
        assert tilemap.offgrid_tiles[0]['type'] == 'grass' and tilemap.offgrid_tiles[0]['variant'] == 2
        
        # Test extraction with keeping
        tilemap = Tilemap(self.game_mock)
        tilemap.tilemap_dict['0;0'] = {'type': 'grass', 'variant': 0, 'pos': [0, 0]}
        tilemap.offgrid_tiles.append({'type': 'decor', 'variant': 0, 'pos': [25, 25]})
        
        extracted = tilemap.extract([('grass', 0)], keep=True)
        
        # Verify correct extraction while keeping originals
        assert len(extracted) == 1
        assert extracted[0]['type'] == 'grass'
        assert '0;0' in tilemap.tilemap_dict  # Should still be in the tilemap
    
    # Verify tiles_around correctly identifies neighboring tiles
    def test_tiles_around(self):
        tilemap = Tilemap(self.game_mock)
        
        # Create a 3x3 grid of tiles
        for x in range(3):
            for y in range(3):
                tilemap.tilemap_dict[f'{x};{y}'] = {'type': 'grass', 'variant': 0, 'pos': [x, y]}
        
        # Test center position
        center_pos = (16 + 8, 16 + 8)  # Position in the middle of tile 1,1
        surrounding_tiles = tilemap.tiles_around(center_pos)
        
        # Should find all 9 tiles (3x3 grid including the center)
        assert len(surrounding_tiles) == 9
        
        # Test edge position
        edge_pos = (0, 0)  # Top-left corner
        surrounding_tiles = tilemap.tiles_around(edge_pos)
        
        # Should find fewer tiles (depends on the NEIGHBOR_OFFSETS)
        assert len(surrounding_tiles) > 0
    
    # Verify save and load functionality with JSON files
    def test_save_load(self):
        tilemap = Tilemap(self.game_mock)
        
        # Add some test data
        tilemap.tilemap_dict['0;0'] = {'type': 'grass', 'variant': 0, 'pos': [0, 0]}
        tilemap.tilemap_dict['1;0'] = {'type': 'stone', 'variant': 1, 'pos': [1, 0]}
        tilemap.offgrid_tiles.append({'type': 'decor', 'variant': 0, 'pos': [25, 25]})
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Test save
            tilemap.save(temp_path)
            
            # Verify the file exists and has content
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                data = json.load(f)
                assert 'tilemap' in data
                assert 'tile_size' in data
                assert 'offgrid' in data
            
            # Test load
            new_tilemap = Tilemap(self.game_mock)
            new_tilemap.load(temp_path)
            
            # Verify correct loading
            assert len(new_tilemap.tilemap_dict) == 2
            assert '0;0' in new_tilemap.tilemap_dict
            assert '1;0' in new_tilemap.tilemap_dict
            assert len(new_tilemap.offgrid_tiles) == 1
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    # Verify solid_check correctly identifies solid tiles
    def test_solid_check(self):
        tilemap = Tilemap(self.game_mock)
        
        # Add a physics tile and a non-physics tile
        tilemap.tilemap_dict['0;0'] = {'type': 'grass', 'variant': 0, 'pos': [0, 0]}
        tilemap.tilemap_dict['1;0'] = {'type': 'decor', 'variant': 0, 'pos': [1, 0]}
        
        # Check position inside the physics tile
        result = tilemap.solid_check((8, 8))
        assert result is not None
        assert result['type'] == 'grass'
        
        # Check position inside the non-physics tile
        result = tilemap.solid_check((16 + 8, 8))
        assert result is None
        
        # Check position outside any tile
        result = tilemap.solid_check((100, 100))
        assert result is None
    
    # Verify physics_rects_around returns correct collision rectangles
    def test_physics_rects_around(self):
        tilemap = Tilemap(self.game_mock)
        
        # Add a physics tile and a non-physics tile
        tilemap.tilemap_dict['0;0'] = {'type': 'grass', 'variant': 0, 'pos': [0, 0]}
        tilemap.tilemap_dict['1;0'] = {'type': 'decor', 'variant': 0, 'pos': [1, 0]}
        
        # Check rects around physics tile
        rects = tilemap.physics_rects_around((8, 8))
        assert len(rects) == 1
        assert isinstance(rects[0], pygame.Rect)
        assert rects[0].x == 0
        assert rects[0].y == 0
        assert rects[0].width == 16
        assert rects[0].height == 16
        
        # Check rects around non-physics tile
        rects = tilemap.physics_rects_around((16 + 8, 8))
        assert len(rects) == 1  # Should still find the nearby physics tile
    
    # Verify autotile correctly assigns variants based on neighbors
    def test_autotile(self):
        tilemap = Tilemap(self.game_mock)
        
        # Create a specific pattern for autotiling
        # A single grass tile with grass tile to the right and below
        # This should match the pattern for variant 0 in AUTOTILE_MAP
        tilemap.tilemap_dict['0;0'] = {'type': 'grass', 'variant': 0, 'pos': [0, 0]}
        tilemap.tilemap_dict['1;0'] = {'type': 'grass', 'variant': 0, 'pos': [1, 0]}
        tilemap.tilemap_dict['0;1'] = {'type': 'grass', 'variant': 0, 'pos': [0, 1]}
        
        # Run autotile
        tilemap.autotile()
        
        # The tile at 0,0 should have neighbors at (1,0) and (0,1)
        # This corresponds to the pattern tuple(sorted([(1, 0), (0, 1)])) which should map to variant 0
        assert tilemap.tilemap_dict['0;0']['variant'] == 0
        
        # Create a different test case - a tile with neighbors on all sides
        tilemap = Tilemap(self.game_mock)
        tilemap.tilemap_dict['1;1'] = {'type': 'grass', 'variant': 0, 'pos': [1, 1]}
        tilemap.tilemap_dict['0;1'] = {'type': 'grass', 'variant': 0, 'pos': [0, 1]}
        tilemap.tilemap_dict['2;1'] = {'type': 'grass', 'variant': 0, 'pos': [2, 1]}
        tilemap.tilemap_dict['1;0'] = {'type': 'grass', 'variant': 0, 'pos': [1, 0]}
        tilemap.tilemap_dict['1;2'] = {'type': 'grass', 'variant': 0, 'pos': [1, 2]}
        
        tilemap.autotile()
        
        # The center tile should have neighbors in all four directions
        # This corresponds to tuple(sorted([(1, 0), (-1,0), (0, 1), (0, -1)])) which maps to variant 8
        assert tilemap.tilemap_dict['1;1']['variant'] == 8
    
    # Verify render method calls the expected surface blits
    def test_render(self):
        tilemap = Tilemap(self.game_mock)
        
        # Add grid and offgrid tiles
        tilemap.tilemap_dict['0;0'] = {'type': 'grass', 'variant': 0, 'pos': [0, 0]}
        tilemap.offgrid_tiles.append({'type': 'decor', 'variant': 0, 'pos': [25, 25]})
        
        # Create a tracking surface class instead of monkeypatching
        class BlitTracker:
            def __init__(self):
                self.surface = pygame.Surface((100, 100))
                self.blit_count = 0
                
            def blit(self, *args, **kwargs):
                self.blit_count += 1
                return self.surface.blit(*args, **kwargs)
                
            def get_width(self):
                return self.surface.get_width()
                
            def get_height(self):
                return self.surface.get_height()
        
        tracker = BlitTracker()
        
        # Call render
        tilemap.render(tracker, offset=(0, 0))
        
        # Verify expected number of blits (one for each tile)
        assert tracker.blit_count > 0  # At least one blit should happen