from _team_list_class import TeamList, series_to_team_class
from _protected_lists import rookies, goalies, bench_goalies, protected_list

import os
import pandas as pd
import datetime
from _helpers import _bench_players

from _roster_calculations import player_list
from _player_stats import performance_data
from _team_combinations import calculate_team_combinations
from _results import generate_results, rank_results, print_results

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hdf_data')

today_value = datetime.datetime.today().strftime("%Y%m%d")
__results_table = os.path.join(BASE_DIR, f'RESULTS_{today_value}.hdf5')
__uuid_table = os.path.join(BASE_DIR, f'UUID_{today_value}.hdf5')
__teams_table = os.path.join(BASE_DIR, f'TEAMS_{today_value}.hdf5')
__rank_table = os.path.join(BASE_DIR, f'RANKS_{today_value}.hdf5')


def main(plist=None, **kwargs):
    iteration = kwargs.get('iteration', 1)
    print(f"Iteration {iteration}")
    update_table_info(iteration)
    if plist is None:
        plist = player_list()

    res_df = performance_data(plist['check_players'], plist['free_agents'])
    calculate_team_combinations(plist['team_list'], plist['current_roster_class'], __teams_table)

    print("Loading team table")
    uuid_df = pd.read_hdf(__teams_table)
    generate_results(res_df, uuid_df, __uuid_table, __results_table)

    print("loading results table")
    tmpdf = pd.read_hdf(__results_table)

    otc, ident = rank_results(plist['current_roster_class'], plist['full_player_list'], uuid_df, tmpdf)

    if ident is True:
        print_results(otc, plist['full_player_list'], plist['original_roster_class'])
    else:
        del uuid_df, tmpdf, res_df
        main(generate_new_loop_data(plist, otc), iteration=iteration+1)


def generate_new_loop_data(plist, optimal_team_class):
    print("Generating new loop data")
    if optimal_team_class.Active == plist['current_roster_class'].Active:
        return None

    bp = _bench_players([optimal_team_class])
    drop_player = bp[0]
    add_fa = optimal_team_class.calculate_adds_drops()['add']

    optimal_team_class.FullList = [f for f in optimal_team_class.FullList if f != drop_player]

    ap = [p for p in plist['all_players'] if p[0] != drop_player]
    crc = optimal_team_class
    ckp = [p for p in plist['check_players'] if p[0] != drop_player]
    fa = [p for p in plist['free_agents'] if p[0] not in [drop_player] + add_fa]
    fpl = [p for p in plist['full_player_list'] if p[0] not in [drop_player]]
    team_list = [p for p in plist['team_list'] if p[0] != drop_player]

    tmp_ls = []
    for p in fa:
        tmp_ls.append(ckp + [p])
    print('')
    return {
        'all_players': ap, 'current_roster_class': crc,
        'check_players': ckp, 'free_agents': fa,
        'full_player_list': fpl, 'team_list': tmp_ls,
        'original_roster_class': plist['original_roster_class']
    }


def update_table_info(i):
    global __teams_table, __rank_table, __results_table
    tt = __teams_table.split("\\")[-1].replace(".hdf5", "")
    __teams_table = os.path.join(BASE_DIR, f'{tt}_{i}.hdf5')

    rt = __rank_table.split("\\")[-1].replace(".hdf5", "")
    __rank_table = os.path.join(BASE_DIR, f'{rt}_{i}.hdf5')

    et = __results_table.split("\\")[-1].replace(".hdf5", "")
    __results_table = os.path.join(BASE_DIR, f'{et}_{i}.hdf5')


if __name__ == '__main__':
    main()
