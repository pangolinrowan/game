import queue
import sys
import importlib
import threading
import time
import pytest
import pygame
from scripts.entities import Player
from scripts.particle import Projectile

def fail_test(string="Test failed"):
    pytest.fail(string)

def import_class(q):
    module_name = "CalenCuesta_Game"  # Name of the module
    try:
        importlib.import_module(module_name)  # Dynamically import module which runs the game
    except Exception as e:
        q.put(e)

class TestAction:
    @pytest.mark.skipif(sys.platform != "linux", reason="This test only runs on Linux platforms and certain machines.")
    def test_move(self, monkeypatch):
        self.game_instance = None

        self.original_projectile_init = Projectile.__init__

        def mock_projectile_init(class_self, game, p_type, pos, velocity=[0, 0], frame=0):
            """
            Mock function to initialize a projectile.
            """
            self.game_instance = game # Intercepts projectile init to get the game instance
            return self.original_projectile_init(class_self, game, p_type, pos, velocity, frame)
        
        monkeypatch.setattr(Projectile, "__init__", mock_projectile_init)

        self.original_pygame_event_get = pygame.event.get
        self.ticks = 0
        self.action_queue = []

        def keypress(key, duration=1, start=10):
            """
            Helper function to create a keypress event.
            """
            if start == 10 and len(self.action_queue) != 0:
                start = self.action_queue[-1][0]

            self.action_queue.append((start, pygame.event.Event(pygame.KEYDOWN, key=key)))
            self.action_queue.append((start + duration, pygame.event.Event(pygame.KEYUP, key=key)))

        # Simulate key presses
        keypress(pygame.K_a, 60 * 5.2)
        keypress(pygame.K_d, 60 * 0.5)
        keypress(pygame.K_a, 60 * 0.8)
        keypress(pygame.K_w, 60 * 0.1)
        keypress(pygame.K_a, 60 * 6)

        def mock_pygame_event_get():
            """
            Mock function to simulate pygame event queue.
            """
            queue = self.original_pygame_event_get()

            self.ticks += 1

            for event in self.action_queue:
                if self.ticks == event[0]:
                    queue.append(event[1])

            if self.game_instance: # To make sure game instance is found
                self.game_instance.dead = 0 # Prevents the character from dying
            else: # Fire a fireball to intercept the game instance from the projectile class
                # Simulate a KEYDOWN event for the 'space' key
                event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
                queue.append(event)

            return queue
        
        monkeypatch.setattr(pygame.event, "get", mock_pygame_event_get)

        q = queue.Queue()
        thread = threading.Thread(target=import_class, args=(q,))
        thread.daemon = True
        thread.start()

        start = time.time()
        while thread.is_alive():
            if not q.empty():
                # If the queue is not empty, it means the test failed
                fail_test(f"Test failed with error: {q.get()}")
            if time.time() - start > 15:
                break
            time.sleep(0.1)  # Small delay to prevent busy-waiting

        assert (abs(self.game_instance.player.pos[0] + 391) <= 10 and abs(self.game_instance.player.pos[1] - 355.3) <= 10), "Failed to move near specified position"

        if not q.empty():
            # If the queue is not empty, it means the test failed
            fail_test(f"Test failed with error: {q.get()}")