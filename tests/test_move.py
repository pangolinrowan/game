import time
import pytest
from scripts.entities import Player

def test_move(monkeypatch):
    original_PlrUpdate = Player.update
    start_time = time.time()
    movements = [
        # (1, (0, 1)),  # Move down until 1 second
        # (2, (1, 0)),  # Move right until 2 seconds
        # (3, (0, -1)), # Move up until 3 seconds
        # (4, (-1, 0)), # Move left until 4 seconds
        # (5, (0, 0)),  # Stop until 5 seconds
        (10, (0, 0)), # Test ends
    ]
    jumps = [
        (0, False),  # Jump at 2 seconds
        (4, False),  # Jump at 4 seconds
        (5, True),  # No jump at 5 seconds
        (10, False) # No jump after 10 seconds
    ]

    def fail_test():
        pytest.fail("Test timed out")

    def get_movement(start_time, movements):
        elapsed_time = time.time() - start_time
        for time_threshold, movement in movements:
            if elapsed_time < time_threshold:
                return movement
        fail_test()

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

    def mock_update(self, tilemap, movement=(0, 0)):
        # Get the appropriate movement and jump status
        movement = get_movement(start_time, movements)
        if should_jump(start_time, jumps):
            self.jump()  # Call the jump method on the player
            
        return original_PlrUpdate(self, tilemap, movement)

    monkeypatch.setattr(Player, "update", mock_update)

    from CalenCuesta_Game import Game

    # Game().run()  # Uncomment if needed to run the game loop

    assert True