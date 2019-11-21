import uuid
import itertools
# from _team_combinations import build_positional_list
from _helpers import _update_progress
import pandas as pd


class TeamList(object):
    def __init__(self):
        self.LW = []
        self.C = []
        self.RW = []
        self.D = []
        self.IR = []
        self.G = []
        self.Util = []

        self.FullList = []

        self.CurrentRosterClass = None
        self.UUID = f"{uuid.uuid4()}"

    @property
    def Active(self):
        return list(self.LW + self.C + self.RW + self.D)

    @property
    def Bench(self):
        _al = self.Active + self.Util + self.G + self.IR
        _fl = self.FullList
        return [p for p in _fl if p not in _al]

    def to_dict(self):
        return {
            'UUID': self.UUID,
            'LW': self.LW,
            "C": self.C,
            "RW": self.RW,
            "D": self.D,
            "Util": self.Util,
            "G": self.G,
            "BN": self.Bench,
            "IR": self.IR
        }

    def total_active_players(self):
        return len(self.Active)

    def valid_player_count(self):
        if self.total_active_players() != 18:
            return False
        else:
            return True

    def bench_size_valid(self):
        if len(self.Bench) > 4:
            return False
        else:
            return True

    def contains_no_duplicates(self):
        _ac = self.Active + self.IR
        _ac_set = set([_ac.count(a) for a in _ac])
        if max(_ac_set) > 1:
            return False
        else:
            return True

    def is_valid(self):
        if not self.valid_player_count():
            return False
        if not self.contains_no_duplicates():
            return False
        return True

    def calculate_adds_drops(self):
        if self.CurrentRosterClass is None:
            print("No current team class available")
            return

        c_fl = self.CurrentRosterClass.FullList
        new_fl = self.FullList
        drop_ids = [_id for _id in c_fl if _id not in new_fl]
        add_ids = [_id for _id in new_fl if _id not in c_fl]

        return {'drop': drop_ids, 'add': add_ids}

    def _number_of_add_or_drop(self, t):
        r = self.calculate_adds_drops()
        if r is not None:
            return len(r[t])
        return None

    @property
    def number_of_adds(self):
        return self._number_of_add_or_drop('add')

    @property
    def number_of_drops(self):
        return self._number_of_add_or_drop('drops')


def series_to_team_class(_df_series, crc=None):
    tc = TeamList()
    tc.LW = [int(x) for x in _df_series['LW'].split(",")]
    tc.C = [int(x) for x in _df_series['C'].split(",")]
    tc.RW = [int(x) for x in _df_series['RW'].split(",")]
    tc.D = [int(x) for x in _df_series['D'].split(",")]
    tc.IR = [int(x) for x in _df_series['IR'].split(",")]
    tc.G = [int(x) for x in _df_series['G'].split(",")]
    tc.Util = [int(x) for x in _df_series['Util'].split(",")]

    _fl = list(
        itertools.chain.from_iterable([tc.LW, tc.C, tc.RW, tc.D, tc.IR, tc.G, tc.Util, _df_series['BN'].split(",")]))
    tc.FullList = [int(x) for x in _fl]
    tc.CurrentRosterClass = crc
    tc.UUID = _df_series['UUID']
    return tc


# def team_from_list(team_list, _goalies=None):
#     pl = build_positional_list(team_list)
#     _fl = list(set([i[0] for i in team_list]))
#     gs = pl["G"]
#     if _goalies is not None:
#         gs = [g for g in pl["G"] if g in _goalies]
#     tl = TeamList()
#     tl.LW = pl["LW"]
#     tl.C = pl["C"]
#     tl.RW = pl["RW"]
#     tl.D = pl["D"]
#     tl.Util = pl['Util']
#     tl.IR = pl["IR"]
#     tl.G = gs
#     tl.FullList = _fl
#     return tl


# wrap the call to this in a locked call if coming from a multithreaded approach
def team_class_to_DF(_team_list, **kwargs):
    """
    Export list of team classes to dataframe representing the positions they are assigned
    Purpose of this is to allow to save the large amounts of individual permutations generated from the many alternatives
    """
    t_dict = []
    for i, t in enumerate(_team_list):
        if ((i+1)%1000) == 0: _update_progress(i+1, len(_team_list), **kwargs)
        cd = {c: ",".join([str(r) for r in t.to_dict()[c]]) for c in t.to_dict()}
        cd["UUID"] = t.UUID
        t_dict.append(cd)
    _update_progress(len(_team_list), len(_team_list), **kwargs)
    print("")
    return pd.DataFrame.from_dict(t_dict)
