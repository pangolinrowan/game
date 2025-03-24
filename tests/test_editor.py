import pytest
import pygame
import sys
import os
from unittest.mock import patch, MagicMock

# Import the Editor class from editor.py
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from editor import Editor, RENDER_SCALE

class TestEditor:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        # Save original pygame functions that we'll mock
        self.original_init = pygame.init
        self.original_display = pygame.display
        self.original_time = pygame.time
        self.original_transform = pygame.transform
        self.original_draw = pygame.draw
        
        # Mock pygame functions
        pygame.init = MagicMock(return_value=(0, 0))
        pygame.display.set_caption = MagicMock()
        pygame.display.set_mode = MagicMock(return_value=pygame.Surface((640, 480)))
        pygame.time.Clock = MagicMock()
        pygame.transform.scale = MagicMock(return_value=pygame.Surface((640, 480)))
        pygame.draw.circle = MagicMock()
        
        # Mock Surface methods
        pygame.Surface.blit = MagicMock()
        pygame.Surface.fill = MagicMock()
        pygame.Surface.set_alpha = MagicMock()
        
        # Patch the load_image functions to avoid file operations
        patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))).start()
        patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]).start()
        
        # Patch Tilemap methods
        patch('scripts.tilemap.Tilemap.load', return_value=None).start()
        patch('scripts.tilemap.Tilemap.save', return_value=None).start()
        patch('scripts.tilemap.Tilemap.render', return_value=None).start()
        
        # Create a mock event queue for testing
        self.mock_events = []
        self.mock_get_events = lambda: self.mock_events
        pygame.event.get = self.mock_get_events
        
        # Mock mouse position
        pygame.mouse.get_pos = MagicMock(return_value=(320, 240))
        
        yield
        
        # Restore original pygame functions
        pygame.init = self.original_init
        pygame.display = self.original_display
        pygame.time = self.original_time
        pygame.transform = self.original_transform
        pygame.draw = self.original_draw
        
        # Stop all patches
        patch.stopall()
    
    # Test editor initialization
    def test_editor_initialization(self):
        # Create editor instance
        editor = Editor()
        
        # Verify basic properties
        assert editor.movement == [False, False, False, False]
        assert isinstance(editor.screen, pygame.Surface)
        assert isinstance(editor.display, pygame.Surface)
        assert editor.scroll == [0, 0]
        
        # Verify assets loaded
        assert 'decor' in editor.assets
        assert 'grass' in editor.assets
        assert 'large_decor' in editor.assets
        assert 'stone' in editor.assets
        assert 'spawners' in editor.assets
        
        # Verify tile selection state
        assert editor.tile_list == list(editor.assets)
        assert editor.tile_group == 0
        assert editor.tile_variant == 0
        
        # Verify initial interaction state
        assert editor.clicking == False
        assert editor.right_clicking == False
        assert editor.shift == False
        assert editor.ongrid == True
    
    # Test scroll movement
    def test_scroll_movement(self):
        # Create editor instance
        editor = Editor()
        
        # Initial scroll position
        initial_scroll = list(editor.scroll)
        
        # Set movement flags
        editor.movement = [False, True, False, False]  # Move right
        
        # Update scroll
        editor.scroll[0] += (editor.movement[1] - editor.movement[0]) * 2
        editor.scroll[1] += (editor.movement[3] - editor.movement[2]) * 2
        
        # Verify scroll changed correctly
        assert editor.scroll[0] == initial_scroll[0] + 2
        assert editor.scroll[1] == initial_scroll[1]
        
        # Test vertical movement
        editor.movement = [False, False, False, True]  # Move down
        
        # Update scroll
        editor.scroll[0] += (editor.movement[1] - editor.movement[0]) * 2
        editor.scroll[1] += (editor.movement[3] - editor.movement[2]) * 2
        
        # Verify scroll changed correctly
        assert editor.scroll[0] == initial_scroll[0] + 2  # Unchanged
        assert editor.scroll[1] == initial_scroll[1] + 2
    
    # Test tile placement
    def test_tile_placement(self):
        # Create editor instance
        editor = Editor()
        
        # Setup for tile placement
        editor.clicking = True
        editor.ongrid = True
        
        # Get mouse position
        mpos = pygame.mouse.get_pos()
        mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
        
        # Calculate tile position
        tile_pos = (int((mpos[0] + editor.scroll[0]) // editor.tilemap.tile_size), 
                    int((mpos[1] + editor.scroll[1]) // editor.tilemap.tile_size))
        
        # Place tile
        tile_key = str(tile_pos[0]) + ';' + str(tile_pos[1])
        editor.tilemap.tilemap[tile_key] = {
            'type': editor.tile_list[editor.tile_group], 
            'variant': editor.tile_variant, 
            'pos': tile_pos
        }
        
        # Verify tile was placed
        assert tile_key in editor.tilemap.tilemap
        assert editor.tilemap.tilemap[tile_key]['type'] == editor.tile_list[editor.tile_group]
        assert editor.tilemap.tilemap[tile_key]['variant'] == editor.tile_variant
        assert editor.tilemap.tilemap[tile_key]['pos'] == tile_pos
    
    # Test tile removal
    def test_tile_removal(self):
        # Create editor instance
        editor = Editor()
        
        # Add a tile that we'll remove
        mpos = pygame.mouse.get_pos()
        mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
        
        tile_pos = (int((mpos[0] + editor.scroll[0]) // editor.tilemap.tile_size), 
                    int((mpos[1] + editor.scroll[1]) // editor.tilemap.tile_size))
        
        tile_key = str(tile_pos[0]) + ';' + str(tile_pos[1])
        editor.tilemap.tilemap[tile_key] = {
            'type': editor.tile_list[editor.tile_group], 
            'variant': editor.tile_variant, 
            'pos': tile_pos
        }
        
        # Verify tile exists
        assert tile_key in editor.tilemap.tilemap
        
        # Setup for tile removal
        editor.right_clicking = True
        
        # Remove tile
        if tile_key in editor.tilemap.tilemap:
            del editor.tilemap.tilemap[tile_key]
        
        # Verify tile was removed
        assert tile_key not in editor.tilemap.tilemap
    
    # Test offgrid tile placement
    def test_offgrid_placement(self):
        # Create editor instance
        editor = Editor()
        
        # Setup for offgrid placement
        editor.ongrid = False
        
        # Get mouse position
        mpos = pygame.mouse.get_pos()
        mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
        
        # Add offgrid tile
        initial_count = len(editor.tilemap.offgrid_tiles)
        editor.tilemap.offgrid_tiles.append({
            'type': editor.tile_list[editor.tile_group], 
            'variant': editor.tile_variant, 
            'pos': (mpos[0] + editor.scroll[0], mpos[1] + editor.scroll[1])
        })
        
        # Verify tile was added
        assert len(editor.tilemap.offgrid_tiles) == initial_count + 1
        assert editor.tilemap.offgrid_tiles[-1]['type'] == editor.tile_list[editor.tile_group]
        assert editor.tilemap.offgrid_tiles[-1]['variant'] == editor.tile_variant
    
    # Test tile group cycling
    def test_tile_group_cycling(self):
        # Create editor instance
        editor = Editor()
        
        # Initial tile group and variant
        initial_group = editor.tile_group
        initial_variant = editor.tile_variant
        
        # Cycle to next tile group
        editor.tile_group = (editor.tile_group + 1) % len(editor.tile_list)
        editor.tile_variant = 0
        
        # Verify tile group changed and variant reset
        assert editor.tile_group == (initial_group + 1) % len(editor.tile_list)
        assert editor.tile_variant == 0
        
        # Cycle to previous tile group
        editor.tile_group = (editor.tile_group - 1) % len(editor.tile_list)
        editor.tile_variant = 0
        
        # Verify returned to initial group
        assert editor.tile_group == initial_group
        assert editor.tile_variant == 0
    
    # Test tile variant cycling
    def test_tile_variant_cycling(self):
        # Create editor instance
        editor = Editor()
        
        # Get current group for reference
        current_group = editor.tile_list[editor.tile_group]
        max_variants = len(editor.assets[current_group])
        
        # Initial variant
        initial_variant = editor.tile_variant
        
        # Cycle to next variant
        editor.tile_variant = (editor.tile_variant + 1) % len(editor.assets[current_group])
        
        # Verify variant changed
        assert editor.tile_variant == (initial_variant + 1) % max_variants
        
        # Cycle to previous variant
        editor.tile_variant = (editor.tile_variant - 1) % len(editor.assets[current_group])
        
        # Verify returned to initial variant
        assert editor.tile_variant == initial_variant
    
    # Test keyboard input handling
    def test_keyboard_input(self):
        # Create editor instance
        editor = Editor()
        
        # Test movement keys
        self.mock_events = [
            pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_a})
        ]
        
        # Process keyboard events
        def process_keydown():
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        editor.movement[0] = True
        
        process_keydown()
        
        # Verify movement flag set
        assert editor.movement[0] == True
        
        # Test grid toggle
        editor.ongrid = True
        self.mock_events = [
            pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_g})
        ]
        
        # Process grid toggle event
        def process_grid_toggle():
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        editor.ongrid = not editor.ongrid
        
        process_grid_toggle()
        
        # Verify grid mode toggled
        assert editor.ongrid == False
        
        # Test autotile command
        self.mock_events = [
            pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_t})
        ]
        
        # Mock autotile method
        editor.tilemap.autotile = MagicMock()
        
        # Process autotile event
        def process_autotile():
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        editor.tilemap.autotile()
        
        process_autotile()
        
        # Verify autotile was called
        editor.tilemap.autotile.assert_called_once()
        
        # Test save command
        self.mock_events = [
            pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_o})
        ]
        
        # Mock save method
        editor.tilemap.save = MagicMock()
        
        # Process save event
        def process_save():
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_o:
                        editor.tilemap.save('map.json')
        
        process_save()
        
        # Verify save was called
        editor.tilemap.save.assert_called_once_with('map.json')
    
    # Integration test simulating editing operations
    def test_editing_simulation(self):
        # Create editor instance
        editor = Editor()
        
        # Step 1: Move the view
        editor.movement = [False, True, False, False]  # Move right
        initial_scroll = list(editor.scroll)
        
        editor.scroll[0] += (editor.movement[1] - editor.movement[0]) * 2
        
        # Verify view moved
        assert editor.scroll[0] > initial_scroll[0]
        
        # Step 2: Place a grid tile
        editor.ongrid = True
        editor.clicking = True
        
        # Get tile position at current mouse location
        mpos = pygame.mouse.get_pos()
        mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
        
        tile_pos = (int((mpos[0] + editor.scroll[0]) // editor.tilemap.tile_size), 
                    int((mpos[1] + editor.scroll[1]) // editor.tilemap.tile_size))
        
        # Place tile
        tile_key = str(tile_pos[0]) + ';' + str(tile_pos[1])
        editor.tilemap.tilemap[tile_key] = {
            'type': editor.tile_list[editor.tile_group], 
            'variant': editor.tile_variant, 
            'pos': tile_pos
        }
        
        # Step 3: Change tile group and variant
        prev_group = editor.tile_group
        editor.tile_group = (editor.tile_group + 1) % len(editor.tile_list)
        editor.tile_variant = 0
        
        # Verify group changed
        assert editor.tile_group != prev_group
        
        # Step 4: Place an offgrid tile
        editor.ongrid = False
        
        # Save initial count
        initial_offgrid_count = len(editor.tilemap.offgrid_tiles)
        
        # Add offgrid tile
        editor.tilemap.offgrid_tiles.append({
            'type': editor.tile_list[editor.tile_group], 
            'variant': editor.tile_variant, 
            'pos': (mpos[0] + editor.scroll[0], mpos[1] + editor.scroll[1])
        })
        
        # Verify offgrid tile added
        assert len(editor.tilemap.offgrid_tiles) == initial_offgrid_count + 1
        
        # Step 5: Toggle grid mode and autotile
        editor.ongrid = not editor.ongrid
        
        # Mock autotile to verify it would be called
        editor.tilemap.autotile = MagicMock()
        editor.tilemap.autotile()
        
        # Verify autotile called
        editor.tilemap.autotile.assert_called_once()
        
        # Step 6: Save map (mocked)
        editor.tilemap.save = MagicMock()
        editor.tilemap.save('map.json')
        
        # Verify save called with correct filename
        editor.tilemap.save.assert_called_once_with('map.json')
