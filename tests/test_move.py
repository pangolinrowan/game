import queue
import importlib
import threading
import time
import pytest
import pygame
from scripts.particle import Projectile

def fail_test(string="Test failed"):
    pytest.fail(string)

def import_class(q):
    module_name = "CalenCuesta_Game"  # Name of the module
    try:
        importlib.import_module(module_name)  # Dynamically import module which runs the game
    except Exception as e:
        q.put(e)

action_queue = []

def keypress(key, duration=1, start=10):
    """
    Helper function to create a keypress event.
    """
    if start == 10 and len(action_queue) != 0:
        start = action_queue[-1][0]

    action_queue.append((start, pygame.event.Event(pygame.KEYDOWN, key=key)))
    action_queue.append((start + duration, pygame.event.Event(pygame.KEYUP, key=key)))

# Simulate key presses
keypress(pygame.K_a, 60 * 5.2)
keypress(pygame.K_d, 60 * 0.5)
keypress(pygame.K_a, 60 * 0.8)
keypress(pygame.K_w, 60 * 0.1)
keypress(pygame.K_a, 60 * 6)

class TestAction:
    @pytest.fixture(autouse=True)
    def setup(self):
        yield
        
        self.__dict__.clear() # Clear the instance variables after each test to avoid interference
    
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_death(self, monkeypatch):
        original_pygame_event_get = pygame.event.get  # Save the original pygame event get function
        original_projectile_init = Projectile.__init__
        self.quitgame = False
        self.game_instance = None
        
        def mock_projectile_init(class_self, game, p_type, pos, velocity=[0, 0], frame=0):
            self.game_instance = game
            return original_projectile_init(class_self, game, p_type, pos, velocity, frame)
        
        def mock_pygame_event_get():
            queue = original_pygame_event_get()
            
            if self.quitgame:
                queue.append(pygame.event.Event(pygame.QUIT))
            if not self.game_instance:
                
                queue.append(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
                queue.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))

            return queue

        monkeypatch.setattr(Projectile, "__init__", mock_projectile_init)
        monkeypatch.setattr(pygame.event, "get", mock_pygame_event_get)

        thread = threading.Thread(target=import_class, args=(queue.Queue(),))
        thread.start()

        while thread.is_alive():
            if self.game_instance and self.game_instance.dead > 0:
                break

        self.quitgame = True

        # Wait for the thread to finish
        thread.join()
    
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_game_window(self, monkeypatch):
        original_pygame_event_get = pygame.event.get  # Save the original pygame event get function
        quitgame = False

        def mock_pygame_event_get():
            queue = original_pygame_event_get()

            nonlocal quitgame
            if quitgame:
                queue.append(pygame.event.Event(pygame.QUIT))

            return queue

        monkeypatch.setattr(pygame.event, "get", mock_pygame_event_get)

        thread = threading.Thread(target=import_class, args=(queue.Queue(),))
        thread.start()

        start = time.time()
        while thread.is_alive():
            if start and time.time() - start > 1:
                break
            time.sleep(0.1)

        assert thread.is_alive() == True and time.time() - start > 1, "Game window should be alive for at least 1 second"
        
        quitgame = True

        # Wait for the thread to finish
        thread.join()
    
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_move(self, monkeypatch):
        self.setup_mocks(monkeypatch)
        q, thread = self.start_game_thread()
        self.run_test_loop(q, thread)
        self.verify_results(q)

    def setup_mocks(self, monkeypatch):
        """
        Set up mock functions for Projectile and pygame events.
        """
        self.game_instance = None
        self.original_projectile_init = Projectile.__init__
        self.original_pygame_event_get = pygame.event.get
        self.ticks = 0
        self.quit = False

        def mock_projectile_init(class_self, game, p_type, pos, velocity=[0, 0], frame=0):
            self.game_instance = game
            return self.original_projectile_init(class_self, game, p_type, pos, velocity, frame)

        def mock_pygame_event_get():
            queue = self.original_pygame_event_get()
            self.ticks += 1

            for event in action_queue:
                if self.ticks == event[0]:
                    queue.append(event[1])

            if self.game_instance:
                self.game_instance.dead = 0
            else:
                queue.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))

            if self.quit:
                queue.append(pygame.event.Event(pygame.QUIT))

            return queue

        monkeypatch.setattr(Projectile, "__init__", mock_projectile_init)
        monkeypatch.setattr(pygame.event, "get", mock_pygame_event_get)

    def start_game_thread(self):
        """
        Start the game thread and return the queue and thread.
        """
        q = queue.Queue()
        thread = threading.Thread(target=import_class, args=(q,))
        thread.start()
        return q, thread

    def run_test_loop(self, q, thread):
        """
        Run the main test loop to monitor the game thread.
        """
        start = time.time()
        while thread.is_alive():
            if not q.empty():
                fail_test(f"Test failed with error: {q.get()}")
            if time.time() - start > 16 or (self.game_instance and abs(self.game_instance.player.pos[0] + 391) <= 10 and abs(self.game_instance.player.pos[1] - 355.3) <= 10):
                self.quit = True
            time.sleep(0.1)

    def verify_results(self, q):
        """
        Verify the test results and assert conditions.
        """
        assert (abs(self.game_instance.player.pos[0] + 391) <= 10 and abs(self.game_instance.player.pos[1] - 355.3) <= 10), "Failed to move near specified position"

        if not q.empty():
            fail_test(f"Test failed with error: {q.get()}")