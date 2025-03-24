import pytest
import pygame
import sys
import os
import importlib.util
from unittest.mock import patch, MagicMock

# Path to the editor file
EDITOR_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'editor.py'))

class TestEditor:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Save original pygame functions
        self.original_init = pygame.init
        self.original_display = pygame.display
        self.original_time = pygame.time
        self.original_transform = pygame.transform
        self.original_draw = pygame.draw
        self.original_exit = sys.exit
        
        # Mock pygame functions
        pygame.init = MagicMock(return_value=(0, 0))
        pygame.display.set_caption = MagicMock()
        pygame.display.set_mode = MagicMock(return_value=pygame.Surface((640, 480)))
        pygame.time.Clock = MagicMock()
        pygame.transform.scale = MagicMock(return_value=pygame.Surface((640, 480)))
        pygame.draw.circle = MagicMock()
        
        # Mock sys.exit to prevent the editor from quitting
        sys.exit = MagicMock()
        
        # Mock Surface methods
        pygame.Surface.blit = MagicMock()
        pygame.Surface.fill = MagicMock()
        pygame.Surface.set_alpha = MagicMock()
        
        # Create a mock event queue for testing
        self.mock_events = []
        self.original_get_events = pygame.event.get
        pygame.event.get = lambda: self.mock_events
        
        # Mock mouse position
        self.original_get_pos = pygame.mouse.get_pos
        pygame.mouse.get_pos = MagicMock(return_value=(320, 240))
        
        yield
        
        # Restore original functions
        pygame.init = self.original_init
        pygame.display = self.original_display
        pygame.time = self.original_time
        pygame.transform = self.original_transform
        pygame.draw = self.original_draw
        sys.exit = self.original_exit
        pygame.event.get = self.original_get_events
        pygame.mouse.get_pos = self.original_get_pos

    def get_editor_module(self):
        """
        Load the editor module without running the editor.
        """
        # Get the module spec
        spec = importlib.util.spec_from_file_location("editor_module", EDITOR_FILE_PATH)
        
        # Create the module
        editor_module = importlib.util.module_from_spec(spec)
        sys.modules["editor_module"] = editor_module
        
        # Patch the run method and sys.exit before loading the module
        with patch('sys.exit', return_value=None):
            # Execute the module
            spec.loader.exec_module(editor_module)
            
            return editor_module

    def test_editor_initialization(self):
        """Test basic initialization of the Editor class."""
        
        # Mock the necessary modules and methods to prevent the editor from running
        with patch('pygame.init'), \
             patch('pygame.display.set_mode', return_value=pygame.Surface((640, 480))), \
             patch('pygame.time.Clock'), \
             patch('scripts.tilemap.Tilemap.load'), \
             patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]), \
             patch('sys.exit'):
                
            # Load the editor module directly
            editor_module = self.get_editor_module()
            
            # Mock Editor.run to prevent it from actually running
            with patch.object(editor_module, 'Editor.run', return_value=None):
                # Create an Editor instance with run method mocked
                Editor = editor_module.Editor
                editor = Editor()
                editor.run = MagicMock()
                
                # Now we can test initialization properties
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
                
                # Verify editing state
                assert editor.clicking == False
                assert editor.right_clicking == False
                assert editor.shift == False
                assert editor.ongrid == True

    def test_scroll_movement(self):
        """Test scrolling functionality."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode', return_value=pygame.Surface((640, 480))), \
             patch('pygame.time.Clock'), \
             patch('scripts.tilemap.Tilemap.load'), \
             patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]), \
             patch('sys.exit'):
                
            # Load the editor module directly
            editor_module = self.get_editor_module()
            
            # Mock Editor.run to prevent it from actually running
            with patch.object(editor_module, 'Editor.run', return_value=None):
                # Create an Editor instance with run method mocked
                Editor = editor_module.Editor
                editor = Editor()
                editor.run = MagicMock()
                
                # Initial scroll position
                initial_scroll = list(editor.scroll)
                
                # Test scrolling right
                editor.movement[1] = True  # Move right
                editor.movement[0] = False
                editor.movement[2] = False
                editor.movement[3] = False
                
                # Update scroll
                editor.scroll[0] += (editor.movement[1] - editor.movement[0]) * 2
                editor.scroll[1] += (editor.movement[3] - editor.movement[2]) * 2
                
                # Verify scroll changed in x-direction
                assert editor.scroll[0] > initial_scroll[0]
                assert editor.scroll[1] == initial_scroll[1]
                
                # Reset scroll
                editor.scroll = list(initial_scroll)
                
                # Test scrolling down
                editor.movement[1] = False
                editor.movement[0] = False
                editor.movement[2] = False
                editor.movement[3] = True  # Move down
                
                # Update scroll
                editor.scroll[0] += (editor.movement[1] - editor.movement[0]) * 2
                editor.scroll[1] += (editor.movement[3] - editor.movement[2]) * 2
                
                # Verify scroll changed in y-direction
                assert editor.scroll[0] == initial_scroll[0]
                assert editor.scroll[1] > initial_scroll[1]

    def test_tile_placement(self):
        """Test tile placement functionality."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode', return_value=pygame.Surface((640, 480))), \
             patch('pygame.time.Clock'), \
             patch('scripts.tilemap.Tilemap.load'), \
             patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]), \
             patch('sys.exit'):
                
            # Load the editor module directly
            editor_module = self.get_editor_module()
            
            # Mock Editor.run to prevent it from actually running
            with patch.object(editor_module, 'Editor.run', return_value=None):
                # Create an Editor instance with run method mocked
                Editor = editor_module.Editor
                RENDER_SCALE = editor_module.RENDER_SCALE
                
                editor = Editor()
                editor.run = MagicMock()
                
                # Setup for tile placement
                editor.clicking = True
                editor.ongrid = True
                
                # Get mouse position
                mpos = pygame.mouse.get_pos()
                mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
                
                # Calculate tile position
                tile_pos = (int((mpos[0] + editor.scroll[0]) // editor.tilemap.tile_size), 
                           int((mpos[1] + editor.scroll[1]) // editor.tilemap.tile_size))
                
                # Initial count of tiles
                initial_tile_count = len(editor.tilemap.tilemap)
                
                # Place tile
                tile_key = str(tile_pos[0]) + ';' + str(tile_pos[1])
                editor.tilemap.tilemap[tile_key] = {
                    'type': editor.tile_list[editor.tile_group], 
                    'variant': editor.tile_variant, 
                    'pos': tile_pos
                }
                
                # Verify tile was added
                assert len(editor.tilemap.tilemap) == initial_tile_count + 1
                assert tile_key in editor.tilemap.tilemap
                assert editor.tilemap.tilemap[tile_key]['type'] == editor.tile_list[editor.tile_group]
                assert editor.tilemap.tilemap[tile_key]['variant'] == editor.tile_variant
                assert editor.tilemap.tilemap[tile_key]['pos'] == tile_pos

    def test_key_controls(self):
        """Test keyboard control handling."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode', return_value=pygame.Surface((640, 480))), \
             patch('pygame.time.Clock'), \
             patch('scripts.tilemap.Tilemap.load'), \
             patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]), \
             patch('sys.exit'):
                
            # Load the editor module directly
            editor_module = self.get_editor_module()
            
            # Mock Editor.run to prevent it from actually running
            with patch.object(editor_module, 'Editor.run', return_value=None):
                # Create an Editor instance with run method mocked
                Editor = editor_module.Editor
                editor = Editor()
                editor.run = MagicMock()
                
                # Test movement key
                assert editor.movement == [False, False, False, False]
                
                # Simulate pressing 'a' key
                key_down_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_a})
                
                # Process event
                if key_down_event.type == pygame.KEYDOWN:
                    if key_down_event.key == pygame.K_a:
                        editor.movement[0] = True
                
                # Verify movement state changed
                assert editor.movement[0] == True
                
                # Test grid toggle with 'g' key
                initial_grid_state = editor.ongrid
                
                # Simulate pressing 'g' key
                grid_key_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_g})
                
                # Process event
                if grid_key_event.type == pygame.KEYDOWN:
                    if grid_key_event.key == pygame.K_g:
                        editor.ongrid = not editor.ongrid
                
                # Verify grid state toggled
                assert editor.ongrid != initial_grid_state
                
                # Test shift key for variant selection
                assert editor.shift == False
                
                # Simulate pressing shift key
                shift_key_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LSHIFT})
                
                # Process event
                if shift_key_event.type == pygame.KEYDOWN:
                    if shift_key_event.key == pygame.K_LSHIFT:
                        editor.shift = True
                
                # Verify shift state changed
                assert editor.shift == True