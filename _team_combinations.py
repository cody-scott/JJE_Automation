import itertools
from _helpers import _update_progress
from _team_list_class import TeamList, team_class_to_DF
from _helpers import _get_icount
from _protected_lists import bench_goalies, goalies, rookies


def calculate_team_combinations(tmp_ls, current_roster_class, __teams_table):
    for i, tt in enumerate(tmp_ls):
        pt = [f"Team {i + 1} of {len(tmp_ls)}"]
        print(pt[0])

        _pdict = build_positional_list(tt)
        _cdict = build_positional_combinations(_pdict)
        _ac_list = get_all_combinations(_cdict)
        print(f"{_get_icount(_cdict):,} total combinations")
        out_list = generate_unique_teams(
            _ac_list, tt + bench_goalies, [g[0] for g in goalies], [r[0] for r in rookies],
            current_roster_class, _get_icount(_cdict)
        )
        print(f"{len(out_list):,} final teams")

        df = team_class_to_DF(out_list, start_print=pt + ["Convering Classes to Data Frame"])
        df.to_hdf(__teams_table, key='team_list', format='table', append=True)
        print('')
        # break
    return __teams_table


def build_positional_list(_player_list, **kwargs):
    print("Building positional dictionary")
    pos_dct = {"LW": [], "C": [], "RW": [], "D": [], "Util": [], "G": [], "IR": []}
    for i in _player_list:
        for p in i[-1].split(","):
            if p not in pos_dct: continue
            pos_dct[p].append(int(i[0]))
    return pos_dct


def build_positional_combinations(_positional_dict):
    print('Generating positional combinations')
    perm_dct = {}
    for p in _positional_dict:
        c = 4
        if p == "D":
            c = 6
        elif p == "IR":
            c = 1
        l = list(itertools.combinations(_positional_dict[p], c))
        perm_dct[p] = l
    return perm_dct


def get_all_combinations(_combo_dict):
    print("Generating Team combinations")
    s = [_combo_dict[i] for i in ["LW", "C", "RW", "D", "IR"]]
    i_list = itertools.product(*s)
    return i_list


def _subcheck(i_item):
    _ac = list(itertools.chain.from_iterable(i_item))
    d = []
    for i in _ac:
        if i in d:
            return False
        d.append(i)
    return True


def generate_unique_teams(i_list, player_list, _goalies, _rookies, current_roster_class=None, _combo_count=0, **kwargs):
    # i_list is generator object from all positional counts
    print("Validating Teams")
    _fl = [i[0] for i in player_list]
    team_classes = []
    for i, i_item in enumerate(i_list):
        if (i % 5000 == 0): _update_progress(i, _combo_count, **kwargs)

        # this checks if list is unique
        if not _subcheck(i_item):
            continue

        tl = TeamList()
        tl.LW = list(i_item[0])
        tl.C = list(i_item[1])
        tl.RW = list(i_item[2])
        tl.D = list(i_item[3])
        tl.Util = _rookies
        tl.G = _goalies
        tl.IR = list(i_item[4])
        tl.FullList = _fl
        tl.CurrentRosterClass = current_roster_class
        team_classes.append(tl)
    _update_progress(_combo_count, _combo_count, **kwargs)
    print("")
    return team_classes

def team_from_list(team_list, _goalies=None):
    pl = build_positional_list(team_list)
    _fl = list(set([i[0] for i in team_list]))
    gs = pl["G"]
    if _goalies is not None:
        gs = [g for g in pl["G"] if g in _goalies]
    tl = TeamList()
    tl.LW = pl["LW"]
    tl.C = pl["C"]
    tl.RW = pl["RW"]
    tl.D = pl["D"]
    tl.Util = pl['Util']
    tl.IR = pl["IR"]
    tl.G = gs
    tl.FullList = _fl
    return tl

{
    1: {'current': 0, 'count': 100}
}