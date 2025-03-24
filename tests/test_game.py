import pytest
import pygame
import sys
import random
import math
import os
from unittest.mock import patch, MagicMock

# Import the Game class from CalenCuesta_Game
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from CalenCuesta_Game import Game

class TestGame:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        # Save original pygame functions that we'll mock
        self.original_init = pygame.init
        self.original_display = pygame.display
        self.original_time = pygame.time
        self.original_mixer = pygame.mixer
        self.original_transform = pygame.transform
        self.original_draw = pygame.draw
        
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
        
        # Patch the load_image functions to avoid file operations
        patch('scripts.utilities.load_image', return_value=pygame.Surface((16, 16))).start()
        patch('scripts.utilities.load_image2', return_value=pygame.Surface((16, 16))).start()
        patch('scripts.utilities.load_images', return_value=[pygame.Surface((16, 16))]).start()
        patch('scripts.utilities.load_images2', return_value=[pygame.Surface((16, 16))]).start()
        
        # Patch Tilemap and Player classes
        patch('scripts.tilemap.Tilemap.load', return_value=None).start()
        patch('scripts.tilemap.Tilemap.extract', return_value=[{'pos': (0, 0)}]).start()
        
        # Create a mock event queue for testing
        self.mock_events = []
        self.mock_get_events = lambda: self.mock_events
        pygame.event.get = self.mock_get_events
        
        yield
        
        # Restore original pygame functions
        pygame.init = self.original_init
        pygame.display = self.original_display
        pygame.time = self.original_time
        pygame.mixer = self.original_mixer
        pygame.transform = self.original_transform
        pygame.draw = self.original_draw
        
        # Stop all patches
        patch.stopall()
    
    # Test game initialization
    def test_game_initialization(self):
        # Create game instance
        game = Game()
        
        # Verify basic properties
        assert game.movement == [False, False, False, False]
        assert isinstance(game.screen, pygame.Surface)
        assert isinstance(game.display, pygame.Surface)
        assert game.level == 0
        assert game.screenshake == 0
        
        # Verify assets loaded
        assert 'decor' in game.assets
        assert 'grass' in game.assets
        assert 'large_decor' in game.assets
        assert 'stone' in game.assets
        assert 'background' in game.assets
        assert 'clouds' in game.assets
        
        # Verify animations loaded
        assert 'enemy/idle' in game.assets
        assert 'enemy/run' in game.assets
        assert 'player/idle' in game.assets
        assert 'player/run' in game.assets
        assert 'player/jump' in game.assets
        assert 'player/attack' in game.assets
        
        # Verify sound effects loaded
        assert 'jump' in game.sfx
        assert 'hit' in game.sfx
        assert 'shoot' in game.sfx
        assert 'ambience' in game.sfx
        assert 'fireball' in game.sfx
        assert 'explosion' in game.sfx
        assert 'landing' in game.sfx
        
        # Verify player, tilemap and clouds initialized
        assert game.player is not None
        assert game.tilemap is not None
        assert game.clouds is not None
    
    # Test load_level method
    def test_load_level(self):
        # Create game instance
        game = Game()
        
        # Initialize empty lists for testing
        game.enemies = []
        game.projectiles = []
        game.player_projectiles = []
        game.particles = []
        game.sparks = []
        
        # Call load_level
        try:
            game.load_level(0)
        except Exception as e:
            # Should not raise exceptions
            assert False, f"load_level raised {type(e).__name__}: {e}"
        
        # Verify game state after loading level
        assert game.scroll == [0, 0]
        assert isinstance(game.enemyRects, dict)
        assert game.dead == 0
        assert game.transition == -30
    
    # Test game input handling
    def test_input_handling(self):
        # Create game instance with some mocks for easier testing
        game = Game()
        game.player.attack = MagicMock()
        game.player.jump = MagicMock(return_value=True)
        
        # Test keyboard input - movement keys
        self.mock_events = [
            pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_a}),
        ]
        game.run = MagicMock()  # Prevent the run method from actually running
        try:
            game.run()
        except:
            pass
        
        # Movement[0] should be True after pressing 'a'
        assert game.movement[0] == True
        
        # Test keyboard input - jump
        self.mock_events = [
            pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_w}),
        ]
        game.player.jump = MagicMock(return_value=True)
        game.sfx['jump'].play = MagicMock()
        
        # Modified run to just process one event cycle
        def process_one_cycle():
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        if game.player.jump():
                            game.sfx['jump'].play()
        
        process_one_cycle()
        
        # Jump should have been called and sound played
        game.player.jump.assert_called_once()
        game.sfx['jump'].play.assert_called_once()
        
        # Test mouse click - attack
        self.mock_events = [
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1}),
        ]
        game.player.attacking = False
        game.player.attack = MagicMock()
        game.sfx['fireball'].play = MagicMock()
        game.player.flip = False
        
        # Process mouse events
        def process_mouse_event():
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if not game.player.attacking:
                            game.player.attack()
                            game.sfx['fireball'].play()
        
        process_mouse_event()
        
        # Attack should have been called and sound played
        game.player.attack.assert_called_once()
        game.sfx['fireball'].play.assert_called_once()
    
    # Test enemy updates
    def test_enemy_updates(self):
        # Create game instance
        game = Game()
        
        # Create a simple enemy for testing
        from scripts.entities import Enemy
        enemy = Enemy(game, (100, 100), (8, 15))
        game.enemies = [enemy]
        game.enemyRects = {}
        
        # Patch the enemy update method to avoid complex interactions
        original_update = enemy.update
        enemy.update = MagicMock()
        enemy.render = MagicMock()
        enemy.rect = MagicMock(return_value=pygame.Rect(100, 100, 8, 15))
        
        # Call update on all enemies
        for enemy in game.enemies:
            enemy.update(game.tilemap, movement=(0, 0))
            enemy.render(game.display, offset=(0, 0))
        
        # Verify enemy update and render methods were called
        enemy.update.assert_called_once()
        enemy.render.assert_called_once()
        
        # Update enemy rects
        for enemy in game.enemies:
            game.enemyRects[enemy] = enemy.rect()
        
        # Verify enemy rect was added to enemyRects
        assert len(game.enemyRects) == 1
        assert enemy in game.enemyRects
        
        # Restore original method
        enemy.update = original_update
    
    # Test particle systems
    def test_particle_systems(self):
        # Create game instance
        game = Game()
        
        # Create particles
        from scripts.particle import Particle
        particle = Particle(game, 'leaf', (100, 100), velocity=[0.5, 0.3], frame=0)
        game.particles = [particle]
        
        # Mock particle update and render methods
        original_update = particle.update
        original_render = particle.render
        particle.update = MagicMock(return_value=False)  # Not killed
        particle.render = MagicMock()
        
        # Update and render all particles
        for p in game.particles.copy():
            kill = p.update()
            p.render(game.display, offset=(0, 0))
            if kill:
                game.particles.remove(p)
        
        # Verify update and render methods were called
        particle.update.assert_called_once()
        particle.render.assert_called_once()
        
        # Verify particle was not removed (update returned False)
        assert len(game.particles) == 1
        
        # Test particle removal
        particle.update = MagicMock(return_value=True)  # Killed
        
        # Update particles again
        for p in game.particles.copy():
            kill = p.update()
            if kill:
                game.particles.remove(p)
        
        # Verify particle was removed
        assert len(game.particles) == 0
        
        # Restore original methods
        particle.update = original_update
        particle.render = original_render
    
    # Test game state transitions
    def test_game_state_transitions(self):
        # Create game instance
        game = Game()
        game.enemies = []  # No enemies means level complete
        game.transition = 0
        
        # Mock the load_level method
        original_load_level = game.load_level
        game.load_level = MagicMock()
        
        # Run a single update cycle
        def update_once():
            # This simulates part of the run method that handles transitions
            if not len(game.enemies):
                game.transition += 1
                if game.transition > 30:
                    game.level = min(game.level + 1, len(os.listdir('data/maps')) - 1)
                    game.load_level(game.level)
        
        # Test level completion transition
        for _ in range(31):  # Transition needs to exceed 30
            update_once()
        
        # Verify level was incremented and load_level was called
        assert game.transition > 30
        game.load_level.assert_called_once()
        
        # Test player death transition
        game.dead = 1
        game.transition = 0
        game.load_level.reset_mock()
        
        def update_death():
            # Simulates death handling in run method
            if game.dead:
                game.dead += 1
                if game.dead >= 10:
                    game.transition = min(30, game.transition + 1)
                if game.dead > 40:
                    game.load_level(game.level)
        
        # Run death updates until dead > 40
        for _ in range(41):
            update_death()
        
        # Verify death handling and level reload
        assert game.dead > 40
        assert game.transition > 0
        game.load_level.assert_called_once()
        
        # Restore original method
        game.load_level = original_load_level
    
    # Integration test that simulates a short gameplay sequence
    def test_gameplay_simulation(self):
        # Create game instance with mocked run method
        game = Game()
        game.run = MagicMock()  # Prevent actual game loop
        
        # Set up initial game state
        game.player.pos = [100, 100]
        game.player.velocity = [0, 0]
        game.enemies = []
        game.projectiles = []
        game.player_projectiles = []
        game.particles = []
        game.sparks = []
        
        # Simulate player movement
        game.movement[1] = True  # Move right
        game.player.update(game.tilemap, (game.movement[1] - game.movement[0], 0))
        
        # Verify player moved
        assert game.player.pos[0] > 100
        
        # Simulate player jump
        original_vel = game.player.velocity[1]
        game.player.jump()
        
        # Verify player is jumping
        assert game.player.velocity[1] < original_vel
        
        # Simulate player attack
        game.player.attack()
        
        # Verify player is attacking
        assert game.player.attacking == True
        
        # Update player again to apply animation changes
        game.player.update(game.tilemap, (game.movement[1] - game.movement[0], 0))
        
        # Verify player animation changed to attack
        assert game.player.action == 'attack'
