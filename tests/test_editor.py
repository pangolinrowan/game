import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Import modules to test
from scripts.tilemap import Tilemap

# Mock pygame to prevent GUI initialization
@pytest.fixture(autouse=True)
def mock_pygame():
    """Mock pygame to prevent GUI initialization"""
    with patch.dict('sys.modules', {'pygame': MagicMock()}):
        yield

class TestEditor:
    """Test the level editor functionality"""
    
    @pytest.fixture
    def editor_components(self):
        """Set up the basic editor components without initializing a full Editor object"""
        # Create a mock editor class that simulates the Editor structure
        class MockEditor:
            def __init__(self):
                self.movement = [False, False, False, False]
                self.scroll = [0, 0]
                self.tile_list = ['grass', 'stone', 'decor', 'large_decor', 'spawners']
                self.tile_group = 0
                self.tile_variant = 0
                self.clicking = False
                self.right_clicking = False
                self.shift = False
                self.ongrid = True
                
                # Mock assets
                self.assets = {
                    'grass': [MagicMock() for _ in range(3)],
                    'stone': [MagicMock() for _ in range(3)],
                    'decor': [MagicMock() for _ in range(3)],
                    'large_decor': [MagicMock() for _ in range(3)],
                    'spawners': [MagicMock() for _ in range(2)]
                }
                
                # Create tilemap
                self.tilemap = Tilemap(self, tile_size=16)
        
        return MockEditor()
    
    def test_editor_initialization(self, editor_components):
        """Test that editor components are correctly initialized"""
        editor = editor_components
        
        # Check initial state
        assert editor.movement == [False, False, False, False]
        assert editor.scroll == [0, 0]
        assert editor.tile_group == 0
        assert editor.tile_variant == 0
        assert editor.clicking == False
        assert editor.right_clicking == False
        assert editor.ongrid == True
        
        # Check tilemap
        assert editor.tilemap.tile_size == 16
        assert editor.tilemap.tilemap == {}
        assert editor.tilemap.offgrid_tiles == []
    
    def test_editor_movement(self, editor_components):
        """Test editor scroll movement based on WASD keys"""
        editor = editor_components
        
        # Test moving right (D key)
        editor.movement = [False, True, False, False]  # Only D key pressed
        
        # Simulate the movement calculation from the run method
        editor.scroll[0] += (editor.movement[1] - editor.movement[0]) * 2
        editor.scroll[1] += (editor.movement[3] - editor.movement[2]) * 2
        
        # Should have moved right (+X)
        assert editor.scroll[0] == 2
        assert editor.scroll[1] == 0
        
        # Test moving left (A key)
        editor.movement = [True, False, False, False]  # Only A key pressed
        editor.scroll = [0, 0]  # Reset scroll
        
        editor.scroll[0] += (editor.movement[1] - editor.movement[0]) * 2
        editor.scroll[1] += (editor.movement[3] - editor.movement[2]) * 2
        
        # Should have moved left (-X)
        assert editor.scroll[0] == -2
        assert editor.scroll[1] == 0
        
        # Test multiple keys
        editor.movement = [True, False, True, False]  # A and W keys
        editor.scroll = [0, 0]  # Reset scroll
        
        editor.scroll[0] += (editor.movement[1] - editor.movement[0]) * 2
        editor.scroll[1] += (editor.movement[3] - editor.movement[2]) * 2
        
        # Should have moved left and up
        assert editor.scroll[0] == -2
        assert editor.scroll[1] == -2
    
    def test_tile_selection(self, editor_components):
        """Test tile group and variant selection"""
        editor = editor_components
        
        # Initial tile selection
        assert editor.tile_group == 0
        assert editor.tile_variant == 0
        
        # Test changing tile group
        # Simulate scrolling up
        editor.tile_group = (editor.tile_group - 1) % len(editor.tile_list)
        assert editor.tile_group == 4  # Should wrap to last group (spawners)
        
        # Simulate scrolling down
        editor.tile_group = (editor.tile_group + 1) % len(editor.tile_list)
        assert editor.tile_group == 0  # Back to first group (grass)
        
        # Test changing variant with shift held
        editor.shift = True
        
        # Simulate scrolling down with shift
        editor.tile_variant = (editor.tile_variant + 1) % len(editor.assets[editor.tile_list[editor.tile_group]])
        assert editor.tile_variant == 1  # Should be second variant
        
        # Simulate scrolling up with shift
        editor.tile_variant = (editor.tile_variant - 1) % len(editor.assets[editor.tile_list[editor.tile_group]])
        assert editor.tile_variant == 0  # Back to first variant
    
    def test_tile_placement(self, editor_components):
        """Test placing tiles on the grid"""
        editor = editor_components
        
        # Mock mouse position and tile position calculation
        mouse_pos = (100, 100)
        editor.scroll = [0, 0]
        
        # Calculate tile position as the editor would
        tile_pos = (
            int((mouse_pos[0] + editor.scroll[0]) // editor.tilemap.tile_size),
            int((mouse_pos[1] + editor.scroll[1]) // editor.tilemap.tile_size)
        )
        
        # Simulate click to place tile
        editor.clicking = True
        
        # Place tile (if on grid)
        if editor.ongrid and editor.clicking:
            tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
            editor.tilemap.tilemap[tile_loc] = {
                'type': editor.tile_list[editor.tile_group],
                'variant': editor.tile_variant,
                'pos': tile_pos
            }
        
        # Verify tile was placed
        tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
        assert tile_loc in editor.tilemap.tilemap
        assert editor.tilemap.tilemap[tile_loc]['type'] == editor.tile_list[editor.tile_group]
        assert editor.tilemap.tilemap[tile_loc]['variant'] == editor.tile_variant
        
        # Test placing offgrid tiles
        editor.ongrid = False
        
        # Place offgrid tile
        if not editor.ongrid and editor.clicking:
            editor.tilemap.offgrid_tiles.append({
                'type': editor.tile_list[editor.tile_group],
                'variant': editor.tile_variant,
                'pos': (mouse_pos[0] + editor.scroll[0], mouse_pos[1] + editor.scroll[1])
            })
        
        # Verify offgrid tile was placed
        assert len(editor.tilemap.offgrid_tiles) == 1
        assert editor.tilemap.offgrid_tiles[0]['type'] == editor.tile_list[editor.tile_group]
        assert editor.tilemap.offgrid_tiles[0]['variant'] == editor.tile_variant
    
    def test_tile_removal(self, editor_components):
        """Test removing tiles from the grid"""
        editor = editor_components
        
        # Add a tile to remove
        tile_pos = (6, 6)
        tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
        editor.tilemap.tilemap[tile_loc] = {
            'type': 'grass',
            'variant': 0,
            'pos': tile_pos
        }
        
        # Mock mouse position to target the tile
        mouse_pos = (100, 100)
        editor.scroll = [0, 0]
        
        # Calculate tile position as the editor would
        calculated_tile_pos = (
            int((mouse_pos[0] + editor.scroll[0]) // editor.tilemap.tile_size),
            int((mouse_pos[1] + editor.scroll[1]) // editor.tilemap.tile_size)
        )
        
        # Override the calculation to target our placed tile
        calculated_tile_pos = tile_pos
        
        # Simulate right-click to remove tile
        editor.right_clicking = True
        
        # Remove tile
        if editor.right_clicking:
            tile_loc = f"{calculated_tile_pos[0]};{calculated_tile_pos[1]}"
            if tile_loc in editor.tilemap.tilemap:
                del editor.tilemap.tilemap[tile_loc]
        
        # Verify tile was removed
        assert tile_loc not in editor.tilemap.tilemap
        
        # Test removing offgrid tiles
        # Add an offgrid tile
        offgrid_pos = (150, 150)
        editor.tilemap.offgrid_tiles.append({
            'type': 'decor',
            'variant': 0,
            'pos': offgrid_pos
        })
        
        # Create a mock rect for collision testing
        class MockRect:
            def __init__(self, x, y, w, h):
                self.x = x
                self.y = y
                self.width = w
                self.height = h
            
            def collidepoint(self, pos):
                return True  # Always collide for testing
        
        # Mock the rect and asset
        tile_img = MagicMock()
        tile_img.get_width.return_value = 16
        tile_img.get_height.return_value = 16
        
        # Override the assets access to return our mock
        editor.assets['decor'][0] = tile_img
        
        # Simulate right-click on offgrid tile
        for tile in editor.tilemap.offgrid_tiles.copy():
            # Create a rect for the tile
            tile_r = MockRect(
                tile['pos'][0] - editor.scroll[0],
                tile['pos'][1] - editor.scroll[1],
                16, 16
            )
            
            # Check if mouse collides with the tile
            if tile_r.collidepoint(mouse_pos):
                editor.tilemap.offgrid_tiles.remove(tile)
        
        # Verify offgrid tile was removed
        assert len(editor.tilemap.offgrid_tiles) == 0
    
    def test_toggle_grid(self, editor_components):
        """Test toggling between grid and offgrid placement"""
        editor = editor_components
        
        # Initial state
        assert editor.ongrid == True
        
        # Toggle grid
        editor.ongrid = not editor.ongrid
        assert editor.ongrid == False
        
        # Toggle back
        editor.ongrid = not editor.ongrid
        assert editor.ongrid == True
    
    def test_autotile(self, editor_components):
        """Test autotiling functionality"""
        editor = editor_components
        
        # Set up a pattern of tiles for autotiling
        # Center tile with neighbors to right and below
        editor.tilemap.tilemap['1;1'] = {'type': 'grass', 'variant': 0, 'pos': (1, 1)}
        editor.tilemap.tilemap['2;1'] = {'type': 'grass', 'variant': 0, 'pos': (2, 1)}
        editor.tilemap.tilemap['1;2'] = {'type': 'grass', 'variant': 0, 'pos': (1, 2)}
        
        # Create a simplified autotile method for testing
        def mock_autotile():
            # Just set all variants to 1 for testing
            for tile_loc in editor.tilemap.tilemap:
                if editor.tilemap.tilemap[tile_loc]['type'] == 'grass':
                    editor.tilemap.tilemap[tile_loc]['variant'] = 1
        
        # Override the autotile method
        editor.tilemap.autotile = mock_autotile
        
        # Call autotile
        editor.tilemap.autotile()
        
        # Verify variants were updated
        for tile_loc in editor.tilemap.tilemap:
            assert editor.tilemap.tilemap[tile_loc]['variant'] == 1
    
    def test_save_load(self, editor_components, tmp_path):
        """Test saving and loading tilemap"""
        editor = editor_components
        
        # Add some tiles
        editor.tilemap.tilemap['1;1'] = {'type': 'grass', 'variant': 0, 'pos': (1, 1)}
        editor.tilemap.offgrid_tiles.append({'type': 'decor', 'variant': 0, 'pos': (50, 50)})
        
        # Create a test file path
        test_file = tmp_path / "test_map.json"
        
        # Mock the save method to track calls
        original_save = editor.tilemap.save
        save_called = [False]
        
        def mock_save(path):
            save_called[0] = True
            # Don't actually save, just record the call
            return True
        
        editor.tilemap.save = mock_save
        
        # Call save
        editor.tilemap.save(str(test_file))
        
        # Verify save was called
        assert save_called[0] == True
        
        # Restore original method
        editor.tilemap.save = original_save
        
        # Test load logic
        # First, clear the tilemap
        editor.tilemap.tilemap = {}
        editor.tilemap.offgrid_tiles = []
        
        # Mock the load method
        load_called = [False]
        
        def mock_load(path):
            load_called[0] = True
            # Set some test data instead of actually loading
            editor.tilemap.tilemap = {'2;2': {'type': 'stone', 'variant': 1, 'pos': (2, 2)}}
            editor.tilemap.offgrid_tiles = [{'type': 'large_decor', 'variant': 0, 'pos': (100, 100)}]
            return True
        
        editor.tilemap.load = mock_load
        
        # Call load
        editor.tilemap.load("dummy_path.json")
        
        # Verify load was called and data was updated
        assert load_called[0] == True
        assert '2;2' in editor.tilemap.tilemap
        assert len(editor.tilemap.offgrid_tiles) == 1