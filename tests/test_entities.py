import pytest
import pygame
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.utilities import Animation

class TestPhysicsEntity:
    # Initialize pygame for testing and clean up afterward
    @pytest.fixture(autouse=True)
    def setup(self):
        pygame.init()
        
        # Minimal display setup needed for testing
        pygame.display.set_caption("Entity Test")
        pygame.display.set_mode((640, 480))
        
        # Create a mock game class for testing
        class GameMock:
            def __init__(self):
                self.assets = {
                    'player/idle': Animation([pygame.Surface((16, 16))], img_dur=5),
                    'player/run': Animation([pygame.Surface((16, 16))], img_dur=5),
                    'player/jump': Animation([pygame.Surface((16, 16))], img_dur=5),
                    'player/attack': Animation([pygame.Surface((32, 32))], img_dur=4, loop=False),
                    'player/weapon': pygame.Surface((16, 16)),
                    'enemy/idle': Animation([pygame.Surface((16, 16))], img_dur=5),
                    'enemy/run': Animation([pygame.Surface((16, 16))], img_dur=5),
                    'bow': pygame.Surface((8, 16))
                }
                self.screenshake = 0
                self.dead = 0
                self.sfx = {
                    'jump': MockSound(),
                    'landing': MockSound(),
                    'shoot': MockSound()
                }
                self.projectiles = []
                self.sparks = []
        
        # Mock sound class
        class MockSound:
            def __init__(self):
                self.play_count = 0
            
            def play(self, loops=0):
                self.play_count += 1
        
        # Create a mock tilemap for collision testing
        class MockTilemap:
            def __init__(self):
                self.collision_rects = []
            
            def physics_rects_around(self, pos):
                return self.collision_rects
            
            def solid_check(self, pos):
                # Return True if position collides with any solid tile
                return any(rect.collidepoint(pos) for rect in self.collision_rects)
        
        self.game_mock = GameMock()
        self.tilemap_mock = MockTilemap()
        
        yield
        
        pygame.quit()
    
    # Verify PhysicsEntity initialization with correct properties
    def test_physics_entity_initialization(self):
        entity = PhysicsEntity(self.game_mock, 'player', (100, 100), (16, 16))
        
        # Verify properties
        assert entity.game == self.game_mock
        assert entity.type == 'player'
        assert entity.pos == [100, 100]
        assert entity.size == (16, 16)
        assert entity.velocity == [0, 0]
        assert entity.collisions == {'up': False, 'down': False, 'right': False, 'left': False}
        assert entity.flip == False
        assert entity.action == 'idle'  # Default action set in init
        assert entity.attacking == False
        assert entity.attackingFrames == 0
    
    # Verify set_action changes animation correctly
    def test_physics_entity_set_action(self):
        entity = PhysicsEntity(self.game_mock, 'player', (100, 100), (16, 16))
        
        # Initial action should be 'idle'
        assert entity.action == 'idle'
        
        # Change action to 'run'
        entity.set_action('run')
        assert entity.action == 'run'
        assert entity.animation == self.game_mock.assets['player/run']
        
        # Setting the same action again should not change anything
        original_animation = entity.animation
        entity.set_action('run')
        assert entity.animation is original_animation  # Should be the same object
    
    # Verify rect method returns correct rectangle
    def test_physics_entity_rect(self):
        entity = PhysicsEntity(self.game_mock, 'player', (100, 100), (16, 16))
        
        rect = entity.rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.x == 100
        assert rect.y == 100
        assert rect.width == 16
        assert rect.height == 16
    
    # Verify update handles movement and collisions correctly
    def test_physics_entity_update(self):
        entity = PhysicsEntity(self.game_mock, 'player', (100, 100), (16, 16))
        
        # Test movement without collisions
        entity.update(self.tilemap_mock, movement=(1, 0))
        assert entity.pos == [101, 100]  # Should move right
        assert entity.flip == False  # Moving right, so not flipped
        
        # Test movement with right collision
        entity.pos = [100, 100]
        collision_rect = pygame.Rect(110, 100, 10, 10)
        self.tilemap_mock.collision_rects = [collision_rect]
        entity.update(self.tilemap_mock, movement=(20, 0))
        
        # Position should be adjusted to avoid overlap
        assert entity.pos[0] < 110
        assert entity.collisions['right'] == True
        
        # Test gravity and vertical collisions
        entity.pos = [100, 100]
        collision_rect = pygame.Rect(100, 120, 20, 10)
        self.tilemap_mock.collision_rects = [collision_rect]
        
        # Apply some vertical velocity
        entity.velocity[1] = 2
        entity.update(self.tilemap_mock)
        
        # Should have downward collision
        assert entity.collisions['down'] == True
        assert entity.velocity[1] == 0  # Velocity reset by collision
    
    # Verify render method calls blit with correct parameters
    def test_physics_entity_render(self):
        entity = PhysicsEntity(self.game_mock, 'player', (100, 100), (16, 16))
        
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
        
        # Render the entity
        entity.render(tracker)
        
        # Verify blit was called
        assert tracker.blit_count == 1
        # Position should be adjusted by anim_offset
        assert tracker.last_blit_pos == (entity.pos[0] + entity.anim_offset[0], entity.pos[1] + entity.anim_offset[1])


class TestPlayer(TestPhysicsEntity):
    # Verify Player initialization extends PhysicsEntity correctly
    def test_player_initialization(self):
        player = Player(self.game_mock, (100, 100), (16, 16))
        
        # Verify base properties
        assert player.game == self.game_mock
        assert player.type == 'player'
        assert player.pos == [100, 100]
        assert player.size == (16, 16)
        
        # Verify player-specific properties
        assert player.air_time == 0
        assert player.jumps == 2
    
    # Verify Player update extends PhysicsEntity and adds player-specific behavior
    def test_player_update(self):
        player = Player(self.game_mock, (100, 100), (16, 16))
        
        # Test air time increases
        initial_air_time = player.air_time
        player.update(self.tilemap_mock)
        assert player.air_time == initial_air_time + 1
        
        # Test landing resets air time and jumps
        player.air_time = 10
        player.jumps = 0
        
        # Add a floor collision
        floor_rect = pygame.Rect(90, 116, 30, 10)
        self.tilemap_mock.collision_rects = [floor_rect]
        
        # Update with floor collision
        player.update(self.tilemap_mock)
        assert player.air_time == 0
        assert player.jumps == 2
        assert player.collisions['down'] == True
        
        # Test death from long fall
        player.air_time = 120
        self.game_mock.dead = 0
        player.update(self.tilemap_mock)
        assert self.game_mock.dead > 0
        assert self.game_mock.screenshake >= 16
    
    # Verify Player jump method
    def test_player_jump(self):
        player = Player(self.game_mock, (100, 100), (16, 16))
        
        # Player should start with 2 jumps
        assert player.jumps == 2
        
        # First jump
        result = player.jump()
        assert result == True
        assert player.jumps == 1
        assert player.velocity[1] < 0  # Negative velocity = jumping up
        assert player.air_time > 0
        
        # Second jump
        initial_velocity = player.velocity[1]
        result = player.jump()
        assert result == True
        assert player.jumps == 0
        assert player.velocity[1] < initial_velocity  # Should jump again
        
        # No more jumps
        result = player.jump()
        assert result == None  # Should return None or False when out of jumps
    
    # Verify Player attack method
    def test_player_attack(self):
        player = Player(self.game_mock, (100, 100), (16, 16))
        
        # Should start not attacking
        assert player.attacking == False
        
        # Attack
        player.attack()
        assert player.attacking == True
        
        # Update should set attack animation
        player.update(self.tilemap_mock)
        assert player.action == 'attack'
        
        # Attack frames should increment
        assert player.attackingFrames > 0
        
        # Attack should end after enough frames
        player.attackingFrames = 36
        player.update(self.tilemap_mock)
        assert player.attacking == False
    
    # Verify Player render method
    def test_player_render(self):
        player = Player(self.game_mock, (100, 100), (16, 16))
        
        # Create a tracking surface class
        class BlitTracker:
            def __init__(self):
                self.surface = pygame.Surface((640, 480))
                self.blit_count = 0
                
            def blit(self, source, pos, *args, **kwargs):
                self.blit_count += 1
                return self.surface.blit(source, pos)
        
        tracker = BlitTracker()
        
        # Render the player without attacking
        player.render(tracker)
        
        # Should call blit twice (weapon + player sprite)
        assert tracker.blit_count == 2
        
        # Reset and test with attacking
        tracker.blit_count = 0
        player.attacking = True
        player.render(tracker)
        
        # Should call blit once for attacking animation
        assert tracker.blit_count == 1


class TestEnemy(TestPhysicsEntity):
    # Verify Enemy initialization extends PhysicsEntity correctly
    def test_enemy_initialization(self):
        enemy = Enemy(self.game_mock, (100, 100), (16, 16))
        
        # Verify base properties
        assert enemy.game == self.game_mock
        assert enemy.type == 'enemy'
        assert enemy.pos == [100, 100]
        assert enemy.size == (16, 16)
        
        # Verify enemy-specific properties
        assert enemy.walking == 0
    
    # Verify Enemy update extends PhysicsEntity and adds enemy-specific behavior
    def test_enemy_update(self):
        enemy = Enemy(self.game_mock, (100, 100), (16, 16))
        
        # Add player to game
        self.game_mock.player = Player(self.game_mock, (150, 100), (16, 16))
        
        # Test random walk initialization
        # Set a fixed seed to make the random test deterministic
        import random
        random.seed(1)  # Choose a seed that triggers walking
        
        enemy.update(self.tilemap_mock)
        assert enemy.walking > 0
        
        # Test walking movement
        initial_pos = enemy.pos[0]
        enemy.update(self.tilemap_mock)
        assert enemy.pos[0] != initial_pos
        
        # Test wall collision flips direction
        enemy.walking = 10
        enemy.collisions['right'] = True
        initial_flip = enemy.flip
        enemy.update(self.tilemap_mock)
        assert enemy.flip != initial_flip
        
        # Test shooting behavior
        enemy.walking = 0
        enemy.pos = [150, 100]  # Same X as player, close enough for Y
        self.game_mock.player.pos = [170, 100]
        enemy.flip = False  # Facing right toward player
        
        # Clear projectiles
        self.game_mock.projectiles = []
        
        enemy.update(self.tilemap_mock)
        
        # Should have fired a projectile
        assert len(self.game_mock.projectiles) > 0
        assert self.game_mock.sfx['shoot'].play_count > 0
    
    # Verify Enemy render method
    def test_enemy_render(self):
        enemy = Enemy(self.game_mock, (100, 100), (16, 16))
        
        # Create a tracking surface class
        class BlitTracker:
            def __init__(self):
                self.surface = pygame.Surface((640, 480))
                self.blit_count = 0
                
            def blit(self, source, pos, *args, **kwargs):
                self.blit_count += 1
                return self.surface.blit(source, pos)
        
        tracker = BlitTracker()
        
        # Render the enemy
        enemy.render(tracker)
        
        # Should call blit twice (enemy sprite + bow)
        assert tracker.blit_count == 2