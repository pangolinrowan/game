import time
import pytest
from scripts.entities import Player

def test_move(monkeypatch):
    original_PlrUpdate = Player.update
    start_time = time.time()
    movements = [
        (1, (0, 1)),  # Move down until 1 second
        (2, (1, 0)),  # Move right until 2 seconds
        (3, (0, -1)), # Move up until 3 seconds
        (4, (-1, 0)), # Move left until 4 seconds
        (5, (0, 0)),  # Stop until 5 seconds
        (10, (0, 0)), # Test ends
    ]

    def fail_test():
        pytest.fail("Test timed out")

    def get_movement(start_time, movements):
        elapsed_time = time.time() - start_time
        for time_threshold, movement in movements:
            if elapsed_time < time_threshold:
                return movement
            
        # If no movement is found, fail the test
        fail_test()

    def mock_update(self, tilemap, movement=(0,0)):
        # Moves player to the right
        # return original_PlrUpdate(self, tilemap, (1,1))

        # Moves player according to the movement tuple
        return original_PlrUpdate(self, tilemap, get_movement(start_time, movements))
    
    monkeypatch.setattr(Player, "update", mock_update)
    
    from CalenCuesta_Game import Game
    
    #Game().run()

    assert True