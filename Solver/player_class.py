from typing import List, Dict, Tuple, Optional

from dataclasses import dataclass, field
from ortools.sat.python import cp_model
import json

@dataclass
class Player:
    id: int
    name: str
    team: str
    positions: List[str]
    goals: int
    assists: int
    points: int
    plusMinus: int
    pim: int
    powerPlayPoints: int
    gameWinningGoals: int
    hits: int
    
    protected: bool = False
    util: bool = False
    current_position: str = "Waivers"
    
    model_positions: Dict = field(default_factory=dict) # list of all the position permutations for the player
    allow_positions: Dict = field(default_factory=dict) # dictionary of each position and the model variables for it
    
    def get_placed_position(self, _solved_model: cp_model.CpSolver, exclude_positions: List[str] = None):
        """given a solved model, return the allocated position"""
        exclude_positions = exclude_positions or []
        for p in self.allow_positions:
            if p in exclude_positions:
                continue
            lbl = f"{self.name} - {p}"
            if any(
                [
                    _solved_model.Value(_) 
                    for _ in self.allow_positions[p]
                ]):
                return p
        return "Waivers"

    def unravel_model_positions(self, data, exclude_positions: List[str] = None):
        exclude_positions = exclude_positions or []
        return [__ for _ in data for __ in data[_] if _ not in exclude_positions]
    
def load_players(_path: str, protected_list=None):
    with open(_path) as f:
        data = json.loads(f.read())

    data = [Player(**p) for p in data]
    data = join_protected(data, protected_list)

    return data

def join_protected(data, protected_list):
    if protected_list:
        with open(protected_list) as f:
            protected_list = json.loads(f.read())

        for p in data:
            for _ in protected_list:
                if _["id"]!=p.id:
                    continue

                # p.util = _.get('util', False)
                if _.get('util') is not None:                    
                    p.positions.append('Util')
                p.protected = True
    return data
