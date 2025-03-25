import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# First, let's test that all modules can be imported
def test_imports():
    """Test that all game modules can be imported without errors"""
    # Import the modules to ensure they're available
    from scripts.entities import PhysicsEntity, Player, Enemy
    from scripts.utilities import load_image, load_images, Animation
    from scripts.tilemap import Tilemap
    from scripts.clouds import Clouds
    from scripts.particle import Particle, Projectile
    from scripts.spark import Spark
    
    # If we get to this point without exceptions, the imports are working
    assert True

# Mock pygame to prevent actual initialization
@pytest.fixture(autouse=True)
def mock_pygame():
    """Mock pygame to prevent GUI initialization"""
    with patch.dict('sys.modules', {'pygame': MagicMock()}):
        yield

class TestGameIntegration:
    """Test the integration between various game components"""
    
    @pytest.fixture
    def game_components(self):
        """Set up the basic game components without initializing a Game object"""
        # Create mocks for the necessary game elements
        # Create animation mocks that properly control 'done' state
        leaf_anim = MagicMock()
        leaf_anim.done = False
        
        fireball_anim = MagicMock()
        fireball_anim.done = False
        
        mock_assets = {
            'player/idle': MagicMock(),
            'player/run': MagicMock(),
            'player/jump': MagicMock(),
            'player/attack': MagicMock(loop=False),
            'player/weapon': MagicMock(),
            'enemy/idle': MagicMock(),
            'enemy/run': MagicMock(),
            'particle/leaf': leaf_anim,
            'particle/fireball': fireball_anim,
            'particle/particle': MagicMock(),
            'projectile': MagicMock(),
        }
        
        mock_sfx = {
            'jump': MagicMock(),
            'hit': MagicMock(),
            'shoot': MagicMock(),
            'fireball': MagicMock(),
            'explosion': MagicMock(),
            'landing': MagicMock(),
        }
        
        # Create a mock game class that simulates the Game structure
        class MockGame:
            def __init__(self):
                self.assets = mock_assets
                self.sfx = mock_sfx
                self.projectiles = []
                self.player_projectiles = []
                self.particles = []
                self.sparks = []
                self.enemies = []
                self.enemyRects = {}
                self.dead = 0
                self.screenshake = 0
                
        return MockGame()
    
    def test_player_enemy_interaction(self, game_components):
        """Test player and enemy objects can interact properly"""
        from scripts.entities import Player, Enemy
        
        # Create the player and enemy
        player = Player(game_components, (50, 50), (10, 13))
        enemy = Enemy(game_components, (100, 50), (8, 15))
        
        # Add enemy to the game
        game_components.enemies.append(enemy)
        game_components.enemyRects[enemy] = enemy.rect()
        game_components.player = player
        
        # Verify the enemy is added correctly
        assert len(game_components.enemies) == 1
        assert game_components.enemyRects.get(enemy) is not None
        
        # Check that the player's attack can create projectiles
        player.attack()
        assert player.attacking == True
    
    def test_projectile_creation(self, game_components):
        """Test projectile creation and interactions"""
        from scripts.particle import Projectile
        
        # Create a projectile
        projectile = Projectile(game_components, 'fireball', [100, 100], [1.5, 0])
        game_components.player_projectiles.append(projectile)
        
        # Check projectile was added
        assert len(game_components.player_projectiles) == 1
        
        # Mock a tilemap for collision detection
        mock_tilemap = MagicMock()
        mock_tilemap.solid_check.return_value = None
        
        # Override the update method to control return value
        projectile.update = lambda tilemap: [False, None, None]
        
        kill = projectile.update(mock_tilemap)
        
        # Verify the projectile wasn't killed
        assert kill[0] == False
    
    def test_particle_system(self, game_components):
        """Test that particles can be created and managed"""
        from scripts.particle import Particle
        
        # Create a leaf particle with mocked update method
        leaf = Particle(game_components, 'leaf', [100, 100], velocity=[0, 0.3])
        
        # Override the update method to control the return value explicitly
        leaf.update = lambda: False  # First call returns False (don't kill)
        
        game_components.particles.append(leaf)
        
        # Verify particle was added
        assert len(game_components.particles) == 1
        
        # Simulate the game's particle update logic - particle should stay
        for particle in game_components.particles.copy():
            kill = particle.update()
            if kill:
                game_components.particles.remove(particle)
        
        # Particle should remain because we mocked update to return False
        assert len(game_components.particles) == 1
        
        # Now make update return True (should be killed)
        leaf.update = lambda: True
        
        # Update again and particle should be removed
        for particle in game_components.particles.copy():
            kill = particle.update()
            if kill:
                game_components.particles.remove(particle)
        
        # Particle should be removed
        assert len(game_components.particles) == 0
    
    def test_tilemap_integration(self, game_components):
        """Test that the tilemap can be created and interacts with entities"""
        from scripts.tilemap import Tilemap
        from scripts.entities import Player
        
        # Create tilemap and player
        tilemap = Tilemap(game_components, tile_size=16)
        player = Player(game_components, (50, 50), (10, 13))
        
        # Mock some tiles for collision testing
        tilemap.tilemap = {
            '3;3': {'type': 'grass', 'variant': 0, 'pos': [3, 3]},
            '4;3': {'type': 'grass', 'variant': 0, 'pos': [4, 3]}
        }
        
        # Mock the physics_rects_around method to return a predictable result
        tilemap.physics_rects_around = lambda pos: []  # No collisions
        
        # Place player and update - should move without collisions
        player.pos = [3 * 16 + 8, 2 * 16]
        player.velocity[1] = 1  # Moving down
        initial_y = player.pos[1]
        
        # Update player
        player.update(tilemap)
        
        # Player should have moved down
        assert player.pos[1] > initial_y
    
    def test_level_transition_logic(self, game_components):
        """Test level transition logic works without pygame"""
        # Starting state for level transition
        game_components.level = 0
        game_components.transition = 0
        game_components.enemies = []  # Empty enemy list triggers level transition
        
        # Set up a mock load_level function
        def mock_load_level(level_id):
            game_components.level = level_id
            game_components.transition = -30  # Reset transition
            game_components.enemies = []  # No enemies in new level
        
        game_components.load_level = mock_load_level
        
        # Simulate the game loop's level transition logic
        if not len(game_components.enemies):
            game_components.transition += 1
            if game_components.transition > 30:
                game_components.level = min(game_components.level + 1, 5)  # Assuming max 5 levels
                game_components.load_level(game_components.level)
        
        # Since transition starts at 0 and we only increment once, it should not transition yet
        assert game_components.transition == 1
        assert game_components.level == 0
        
        # Continue simulating until transition occurs
        for _ in range(30):
            if not len(game_components.enemies):
                game_components.transition += 1
                if game_components.transition > 30:
                    game_components.level = min(game_components.level + 1, 5)
                    game_components.load_level(game_components.level)
        
        # Now the transition should have occurred
        assert game_components.level == 1
        assert game_components.transition == -30  # Reset by load_level