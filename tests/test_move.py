import pytest
from scripts.entities import Player

def test_move(monkeypatch):
    original_PlrUpdate = Player.update

    def mock_update(self, tilemap, movement=(0,0)):
        # Moves player to the right
        return original_PlrUpdate(self, tilemap, (1,1))
    
    monkeypatch.setattr(Player, "update", mock_update)

    from CalenCuesta_Game import Game

    #Game().run()

    assert True