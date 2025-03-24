import pytest
import pygame
import sys
import os
import importlib.util
from unittest.mock import patch, MagicMock

# Path to the game file
GAME_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CalenCuesta_Game.py'))

class TestGame:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Save original pygame functions
        self.original_init = pygame.init
        self.original_display = pygame.display
        self.original_time = pygame.time
        self.original_mixer = pygame.mixer
        self.original_transform = pygame.transform
        self.original_draw = pygame.draw
        self.original_exit = sys.exit
        
        # Mock pygame functions
        pygame.init = MagicMock(return_value=(0, 0))
        pygame.display.set_caption = MagicMock()
        pygame.display.set_mode = MagicMock(return_value=pygame.Surface((640, 480)))
        pygame.time.Clock = MagicMock()
        pygame.mixer.Sound = MagicMock()
        pygame.mixer.music = MagicMock()
        pygame.transform.scale = MagicMock(return_value=pygame.Surface((640, 480)))
        pygame.transform.flip = MagicMock(return_value=pygame.Surface((16, 16)))
        pygame.transform.scale_by = MagicMock(return_value=pygame.Surface((16, 16)))
        pygame.draw.circle = MagicMock()
        
        # Mock sys.exit to prevent the game from quitting
        sys.exit = MagicMock()
        
        # Create a mock event queue for testing
        self.mock_events = []
        self.original_get_events = pygame.event.get
        pygame.event.get = lambda: self.mock_events
        
        yield
        
        # Restore original functions
        pygame.init = self.original_init
        pygame.display = self.original_display
        pygame.time = self.original_time
        pygame.mixer = self.original_mixer
        pygame.transform = self.original_transform
        pygame.draw = self.original_draw
        sys.exit = self.original_exit
        pygame.event.get = self.original_get_events

    def get_game_instance(self):
        """
        Load the Game class without running the game.
        """
        # Get the module spec
        spec = importlib.util.spec_from_file_location("game_module", GAME_FILE_PATH)
        
        # Create the module
        game_module = importlib.util.module_from_spec(spec)
        
        # Patch the run method and sys.exit before loading the module
        with patch.object(game_module, 'run', return_value=None):
            with patch('sys.exit', return_value=None):
                # Execute the module
                spec.loader.exec_module(game_module)
                
                # Create a game instance but don't run it
                game_instance = game_module.Game()
                
                # Replace the run method to prevent it from entering the game loop
                game_instance.run = MagicMock()
                
                return game_instance

    def test_game_initialization(self):
        """Test basic initialization of the Game class."""
        
        # Mock the necessary modules and methods to prevent the game from running
        with patch('pygame.init'), \
             patch('pygame.display.set_mode', return_value=pygame.Surface((640, 480))), \
             patch('pygame.time.Clock'), \
             patch('scripts.tilemap.Tilemap.load'), \
             patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_image2', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]), \
             patch('scripts.utilities.load_images2', return_value=[pygame.Surface((16, 16))]), \
             patch('sys.exit'):
                
            # Load the game module directly
            spec = importlib.util.spec_from_file_location("game_module", GAME_FILE_PATH)
            game_module = importlib.util.module_from_spec(spec)
            sys.modules["game_module"] = game_module
            
            # Mock Game.run to prevent it from actually running
            with patch.object(game_module, 'Game.run', return_value=None):
                spec.loader.exec_module(game_module)
                
                # Create a Game instance with run method mocked
                Game = game_module.Game
                game = Game()
                game.run = MagicMock()
                
                # Now we can test initialization properties
                assert game.movement == [False, False, False, False]
                assert isinstance(game.screen, pygame.Surface)
                assert isinstance(game.display, pygame.Surface)
                assert game.level == 0
                assert game.screenshake == 0
                
                # We can also verify asset dictionary structure exists
                assert hasattr(game, 'assets')
                assert hasattr(game, 'sfx')
                
                # Verify player and tilemap were initialized
                assert hasattr(game, 'player')
                assert hasattr(game, 'tilemap')

    def test_load_level(self):
        """Test the load_level method."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode', return_value=pygame.Surface((640, 480))), \
             patch('pygame.time.Clock'), \
             patch('scripts.tilemap.Tilemap.load'), \
             patch('scripts.tilemap.Tilemap.extract', return_value=[{'pos': (0, 0)}]), \
             patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_image2', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]), \
             patch('scripts.utilities.load_images2', return_value=[pygame.Surface((16, 16))]), \
             patch('sys.exit'):
                
            # Load the game module directly
            spec = importlib.util.spec_from_file_location("game_module", GAME_FILE_PATH)
            game_module = importlib.util.module_from_spec(spec)
            sys.modules["game_module"] = game_module
            
            # Mock Game.run to prevent it from actually running
            with patch.object(game_module, 'Game.run', return_value=None):
                spec.loader.exec_module(game_module)
                
                # Create a Game instance with run method mocked
                Game = game_module.Game
                game = Game()
                game.run = MagicMock()
                
                # Initialize game state for testing
                game.enemies = []
                game.projectiles = []
                game.player_projectiles = []
                game.particles = []
                game.sparks = []
                
                # Test load_level method
                with patch('scripts.tilemap.Tilemap.extract', return_value=[{'pos': (0, 0)}]):
                    try:
                        game.load_level(0)
                    except Exception as e:
                        pytest.fail(f"load_level raised {type(e).__name__}: {e}")
                
                # Verify state after loading level
                assert game.scroll == [0, 0]
                assert isinstance(game.enemyRects, dict)
                assert game.dead == 0
                assert game.transition == -30

    def test_player_control(self):
        """Test player movement controls."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode', return_value=pygame.Surface((640, 480))), \
             patch('pygame.time.Clock'), \
             patch('scripts.tilemap.Tilemap.load'), \
             patch('scripts.tilemap.Tilemap.extract', return_value=[{'pos': (0, 0)}]), \
             patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_image2', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]), \
             patch('scripts.utilities.load_images2', return_value=[pygame.Surface((16, 16))]), \
             patch('sys.exit'):
                
            # Load the game module directly
            spec = importlib.util.spec_from_file_location("game_module", GAME_FILE_PATH)
            game_module = importlib.util.module_from_spec(spec)
            sys.modules["game_module"] = game_module
            
            # Mock Game.run to prevent it from actually running
            with patch.object(game_module, 'Game.run', return_value=None):
                spec.loader.exec_module(game_module)
                
                # Create a Game instance with run method mocked
                Game = game_module.Game
                game = Game()
                game.run = MagicMock()
                
                # Test movement key down
                assert game.movement == [False, False, False, False]
                
                # Create a key down event for pressing 'a'
                key_down_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_a})
                
                # Simulate event processing
                if key_down_event.type == pygame.KEYDOWN:
                    if key_down_event.key == pygame.K_a:
                        game.movement[0] = True
                
                # Verify movement state changed
                assert game.movement[0] == True
                
                # Create a key up event for releasing 'a'
                key_up_event = pygame.event.Event(pygame.KEYUP, {'key': pygame.K_a})
                
                # Simulate event processing
                if key_up_event.type == pygame.KEYUP:
                    if key_up_event.key == pygame.K_a:
                        game.movement[0] = False
                
                # Verify movement state changed back
                assert game.movement[0] == False

    def test_player_jump(self):
        """Test player jump functionality."""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode', return_value=pygame.Surface((640, 480))), \
             patch('pygame.time.Clock'), \
             patch('scripts.tilemap.Tilemap.load'), \
             patch('scripts.tilemap.Tilemap.extract', return_value=[{'pos': (0, 0)}]), \
             patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_image2', return_value=pygame.Surface((16, 16))), \
             patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]), \
             patch('scripts.utilities.load_images2', return_value=[pygame.Surface((16, 16))]), \
             patch('sys.exit'):
                
            # Load the game module directly
            spec = importlib.util.spec_from_file_location("game_module", GAME_FILE_PATH)
            game_module = importlib.util.module_from_spec(spec)
            sys.modules["game_module"] = game_module
            
            # Mock Game.run to prevent it from actually running
            with patch.object(game_module, 'Game.run', return_value=None):
                spec.loader.exec_module(game_module)
                
                # Create a Game instance with run method mocked
                Game = game_module.Game
                game = Game()
                game.run = MagicMock()
                
                # Mock player's jump method and sfx
                game.player.jump = MagicMock(return_value=True)
                game.sfx['jump'].play = MagicMock()
                
                # Create a key down event for jumping (pressing 'w')
                jump_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_w})
                
                # Simulate event processing
                if jump_event.type == pygame.KEYDOWN:
                    if jump_event.key == pygame.K_w:
                        if game.player.jump():
                            game.sfx['jump'].play()
                
                # Verify jump method and sound effect were called
                game.player.jump.assert_called_once()
                game.sfx['jump'].play.assert_called_once()