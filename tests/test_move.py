# TODO: Rework the test to account for FPS and machine differences, use player's position and go to the next step after reaching near a specific point
# TODO: Mock keybinds instead of intercepting script functions
import sys
import importlib
import time
import pytest
import pygame
import multiprocessing
from scripts.entities import Player
from scripts.particle import Projectile

movements = [
        (5, (-1, 0)),
        (6, (0, 0)),
        (6.3, (1, 0)),
        (6.5, (0, 0)),
        (13, (-1, 0)),
        (14, (0, 0)),
    ]
jumps = [
    (4, False),
    (5, True),
    (7, False),
    (7.3, True),
    (7.5, False),
]

def fail_test(string="Test failed"):
        pytest.fail(string)

def get_movement(start_time, movements):
    """
    Determines the player's movement based on elapsed time and movement schedule.

    :param start_time: The time when the test started.
    :param movements: A list of tuples (time_threshold, movement).
    :return: A tuple representing the player's movement.
    """
    elapsed_time = time.time() - start_time
    for time_threshold, movement in movements:
        if elapsed_time < time_threshold:
            return movement
    return movements[-1][1]  # Default to the last movement if no threshold matches

def should_jump(start_time, jumps):
    """
    Determines if the player should jump based on elapsed time and jump schedule.

    :param start_time: The time when the test started.
    :param jumps: A list of tuples (time_threshold, should_jump).
    :return: A boolean indicating whether the player should jump.
    """
    elapsed_time = time.time() - start_time
    for time_threshold, jump in jumps:
        if elapsed_time < time_threshold:
            return jump
    return False  # Default to no jump if no threshold matches

def import_class(q):
        module_name = "CalenCuesta_Game"  # Name of the module
        try:
            importlib.import_module(module_name)  # Dynamically import module which runs the game
        except Exception as e:
            q.put(e)

@pytest.mark.skipif(sys.platform != "linux", reason="This test only runs on Linux platforms and certain machines.")
def test_move(monkeypatch):
    game_instance = None
    start_time = time.time()

    original_plr_update = Player.update

    def mock_update(self, tilemap, movement=(0, 0)):
        if (time.time() - start_time) > 14:
            assert (abs(self.pos[0] + 391) <= 10 and abs(self.pos[1] - 355.3) <= 10), "Failed to move near specified position"

        # Get the appropriate movement and jump status
        new_movement = get_movement(start_time, movements)
        if should_jump(start_time, jumps):
            self.jump()  # Call the jump method on the player
        
        return original_plr_update(self, tilemap, new_movement)

    monkeypatch.setattr(Player, "update", mock_update)

    original_projectile_init = Projectile.__init__

    def mock_projectile_init(self, game, p_type, pos, velocity=[0, 0], frame=0):
        """
        Mock function to initialize a projectile.
        """
        nonlocal game_instance
        game_instance = game # Intercepts projectile init to get the game instance
        return original_projectile_init(self, game, p_type, pos, velocity, frame)
    
    monkeypatch.setattr(Projectile, "__init__", mock_projectile_init)

    original_pygame_event_get = pygame.event.get
    debounce = False

    def mock_pygame_event_get():
        """
        Mock function to simulate pygame event queue.
        """
        queue = original_pygame_event_get()
        
        nonlocal debounce
        if not debounce:
            debounce = True
            # Simulate a KEYDOWN event for the 'space' key
            event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
            queue.append(event)
        else: # To make sure gameInstance is not None
            nonlocal game_instance
            game_instance.dead = 0 # Prevents the character from dying

        return queue
    
    monkeypatch.setattr(pygame.event, "get", mock_pygame_event_get)

    q = multiprocessing.Queue()
    proc = multiprocessing.Process(target=import_class, args=(q,))
    proc.start()

    start = time.time()
    while proc.is_alive():
        if not q.empty():
            # If the queue is not empty, it means the test failed
            fail_test(f"Test failed with error: {q.get()}")
        if time.time() - start > 15:
            break
        time.sleep(0.1)  # Small delay to prevent busy-waiting

    proc.terminate()  # Sends a SIGTERM

    if not q.empty():
            # If the queue is not empty, it means the test failed
            fail_test(f"Test failed with error: {q.get()}")

    if time.time() - start < 14.1:
        fail_test("Unexpected program termination. Game did not run for long enough to test movement.")