from typing import List, Dict, Tuple, Optional

from ortools.sat.python import cp_model
from sklearn.preprocessing import MinMaxScaler

from Solver.player_class import Player, join_protected
from dataclasses import asdict
import json
import datetime

class FantasyModel:
    def __init__(self) -> None:
        self.model = None
        self.players = None
        self.solved_status = None
        self.solved_model = None

    def build_player_positions(self, model: cp_model.CpModel, player_data: List[Player], positions: Dict[str, int]):
        # return dictionary containing {position: {id: [model_vars]}}
        position_dict = {_: {} for _ in positions}
        for player in player_data:
            for position in positions: 
                # list on player containing its positional variables
                player.allow_positions[position] = []
                player.model_positions[position] = []

                pp = position_dict[position].get(player.id, [])
                
                # for each position, loop the allowed number per-position
                for i in range(positions[position]):
                    _lbl = f'{player.id} - {player.name} - {position} - {i}'
                    # if position == 'Bench':
                        # pos_var = model.NewBoolVar(_lbl)
                        # player.allow_positions[position].append(pos_var)

                    # elif position == 'Util' and player.util:
                    if position == 'Util' and player.util:
                        pos_var = model.NewBoolVar(_lbl)
                        player.allow_positions[position].append(pos_var)

                    elif (position in player.positions):
                        pos_var = model.NewBoolVar(_lbl)
                        player.allow_positions[position].append(pos_var)
                        
                    else:
                        # if its not an allowed position then set the variable to be 0,0
                        pos_var = model.NewIntVar(0, 0, _lbl)
                    
                    # all applicable positions for a player
                    player.model_positions[position].append(pos_var)
                    pp.append(pos_var)
                    
                position_dict[position][player.id] = pp
        return position_dict

    def build_objective_by_attr(self, players, target, scale=True):
        scaler = self.build_scaler(players, target)

        objective = []
        coef = []
        for player in players:
            for data in player.unravel_model_positions(player.model_positions, ['IR', 'Bench']):
                objective.append(data)
                _attr_value = getattr(player, target)
                _value = self.apply_scaler(scaler, _attr_value) if scale else _attr_value
                coef.append(_value)
        return objective, coef
        
    def build_scaler(self, players, attr):
        scaler = MinMaxScaler((0, 100))
        scaler.fit([[getattr(_, attr)] for _ in players])
        return scaler

    def apply_scaler(self, scaler, value):
        return int(scaler.transform([[value]])[0][0])
        
    def solution_dictionary(self):
        players = self.players
        solved_model = self.solved_model
        res = [
            [pp, _.id] 
            for _ in players 
            if (pp := _.get_placed_position(solved_model)) not in ['Waivers']
        ]

        positions = {}
        for _ in res:
            r = positions.get(_[0], [])
            r.append(_[1])
            positions[_[0]] = r

        return positions

    def build_model(self, players: List[Player]):
        model = cp_model.CpModel()

        positions = {'LW': 3, 'RW': 3, 'C': 3, 'D': 5, 'Util': 1, 'IR': 2, 'Bench': 3}
    
        positions_dict = self.build_player_positions(model, players, positions)
        

        for player in players:
            if player.protected:
                model.Add(
                    sum(
                        player.unravel_model_positions(player.model_positions)
                    ) == 1
                )
            else:
                model.Add(
                    sum(
                        player.unravel_model_positions(player.model_positions)
                    ) <= 1
                )
        
        # limit the number of allowed players per-position
        for p in positions_dict:
            p_count = positions[p]
            if p == 'IR':
                model.Add(sum(
                    [
                    __ 
                    for _ in positions_dict[p] 
                    for __ in positions_dict[p][_]
                    ]
                ) <= p_count)
            else:
                model.Add(sum(
                    [
                    __ 
                    for _ in positions_dict[p] 
                    for __ in positions_dict[p][_]
                    ]
                ) == p_count)


        goal_objective, goal_coef = self.build_objective_by_attr(players, 'goals')     
        assist_objective, assist_coef = self.build_objective_by_attr(players, 'assists') 
        points_objective, points_coef = self.build_objective_by_attr(players, 'points')   
        pm_objective, pm_coef = self.build_objective_by_attr(players, 'plusMinus')
        pim_objective, pim_coef = self.build_objective_by_attr(players, 'pim')
        ppp_objective, ppp_coef = self.build_objective_by_attr(players, 'powerPlayPoints')
        hits_objective, hits_coef = self.build_objective_by_attr(players, 'hits')
        
        model.Maximize(
            sum((goal_objective[i]*goal_coef[i]) for i in range(len(goal_objective))) +
            sum((assist_objective[i]*assist_coef[i]) for i in range(len(assist_objective))) +
            sum((points_objective[i]*points_coef[i]) for i in range(len(points_objective))) +
            sum((pm_objective[i]*pm_coef[i]) for i in range(len(pm_objective))) +
            sum((pim_objective[i]*pim_coef[i]) for i in range(len(pim_objective))) +
            sum((ppp_objective[i]*ppp_coef[i]) for i in range(len(ppp_objective))) +
            sum((hits_objective[i]*hits_coef[i]) for i in range(len(hits_objective))) +
            sum([__ for _ in players for __ in _.unravel_model_positions(_.model_positions)])
        )

        self.model = model
        self.players = players
        return dict(model=model, players=players)

    def solve_model(self):
        model = self.model
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        self.solved_model = solver
        self.solved_status = status

        print('Solve status: %s' % solver.StatusName(status))
        print('Statistics')
        print('  - conflicts : %i' % solver.NumConflicts())
        print('  - branches  : %i' % solver.NumBranches())
        print('  - wall time : %f s' % solver.WallTime())
        print()
        return dict(status=status, solver=solver)

    def results_to_json(self):
        data = []
        for p in self.players:
            dc = asdict(p)
            dc = {_: dc[_] for _ in dc if _ not in ['model_positions', 'allow_positions']}
            dc['placed_position'] = p.get_placed_position(self.solved_model)
            data.append(dc)
        
        return json.dumps(data, indent=4)

    def print_solved(self, show_unplaced=True, show_stats=True):
        skip_positions = [] if show_unplaced else ["Waivers"]
        if self.solved_status != cp_model.OPTIMAL:
            return
        _solved_model = self.solved_model
        targets = {
            'Goals': 'goals',
            'Assists': 'assists',
            'Points': 'points',
            'Plus/Minus': 'plusMinus',
            'PIMs': 'pim',
            'Powerplay Points': 'powerPlayPoints',
            'Game winning goals': 'gameWinningGoals',
            'Hits': 'hits'
        }

        if show_stats:
            for target in targets:
                new_sum = sum(
                    [
                        getattr(_, targets[target]) 
                        for _ in self.players
                        if _.get_placed_position(_solved_model) not in ['IR', 'Bench', 'Waivers']
                    ]               
                )
                current_sum = sum(
                    [
                        getattr(_, targets[target]) 
                        for _ in self.players
                        if _.current_position not in ['IR', 'Bench', 'Waivers']
                    ] 
                )
                print(
                    f"{target}", 
                    f"New: {new_sum}",
                    f"Current: {current_sum}", 
                    f"Delta: {new_sum - current_sum}", 
                    sep=" | ")
            print()    


        # pos_list = []
        # for _ in self.players:
        #     pp = _.get_placed_position(_solved_model)
        #     cpos = "*" if _.current_position == 'Waivers' else ''
        #     if pp not in skip_positions:
                
        #         pos_list.append(f"{_.name} - {pp}" )


        print("\n".join(
            sorted(
                [
                    f"{'*' if _.current_position == 'Waivers' else ''}{_.name} - {pp}" 
                    for _ in self.players
                    if (pp := _.get_placed_position(_solved_model)) not in skip_positions
                ],
                key=lambda x: {'LW': 0, 'C': 1, 'RW': 2, 'D': 3, 'IR': 4, 'Util': 5, 'Bench': 6}.get(x.split(" - ")[-1], 9)
            )
            )
        )


