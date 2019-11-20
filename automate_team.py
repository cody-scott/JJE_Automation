import uuid

import requests
import os
from bs4 import BeautifulSoup

import itertools
import operator

from selenium import webdriver
import time
import random
import pandas as pd
import datetime

driver_path = r"F:\A_Data Backup\Desktop\Projects\PycharmProjects\JJE_Automation\chromedriver.exe"
# driver_path = '/Users/codyscott/PycharmProjects/Jupyter/chromedriver'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

today_value = datetime.datetime.today().strftime("%Y%m%d")

# BAD but could just change these with a global... Mr.Lazy
__results_table = os.path.join(BASE_DIR, f'RESULTS_{today_value}.hdf5')
__uuid_table = os.path.join(BASE_DIR, f'UUID_{today_value}.hdf5')
__teams_table = os.path.join(BASE_DIR, f'TEAMS_{today_value}.hdf5')
__rank_table = os.path.join(BASE_DIR, f'RANKS_{today_value}.hdf5')

# protected players
rookies = [
    [7528, 'Nick Suzuki', 'Util'],
    [7927, 'Rasmus Sandin', 'Util'],
]
goalies = [
    [5820, 'Connor Hellebuyck', 'G'],
    [4003, 'Semyon Varlamov', 'G'],
]
bench_goalies = [
    [4589, 'Jake Allen', 'G'],
]

protected_list = [
    [6752, 'Mikko Rantanen', 'IR'],
    [5820, 'Connor Hellebuyck', 'G'],
    [4003, 'Semyon Varlamov', 'G'],
    [4589, 'Jake Allen', 'G'],
    [4682, 'Victor Hedman', 'D'],
]


def _update_progress(ci, mx_num=None, **kwargs):
    if mx_num is None:
        mx_num=0
    # clear_output(wait = True)

    # for i in kwargs.get("start_print", []):
    #         print(i)
            
    if mx_num > 0:
        bar_length = 20            
        # print(f"{ci:,} of {mx_num:,}")
        pg = (ci/mx_num)
        block = int(round(bar_length * pg))
        # print("\r")
        text = "\rProgress: [{0}] {1:.1f}%".format( "#" * block + "-" * (bar_length - block), pg * 100)
        print(text, flush=True, end="")
    else:
        print(f"{ci:,}")
        
    for i in kwargs.get("end_print", []):
            print(i)


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


def series_to_team_class(_df_series, crc=None):
    tc = TeamList()
    tc.LW = [int(x) for x in _df_series['LW'].split(",")]
    tc.C = [int(x) for x in _df_series['C'].split(",")]
    tc.RW = [int(x) for x in _df_series['RW'].split(",")]
    tc.D = [int(x) for x in _df_series['D'].split(",")]
    tc.IR = [int(x) for x in _df_series['IR'].split(",")]
    tc.G = [int(x) for x in _df_series['G'].split(",")]
    tc.Util = [int(x) for x in _df_series['Util'].split(",")]
    
    _fl = list(itertools.chain.from_iterable([tc.LW, tc.C, tc.RW, tc.D, tc.IR, tc.G, tc.Util, _df_series['BN'].split(",")]))    
    tc.FullList = [int(x) for x in _fl]
    tc.CurrentRosterClass = crc
    tc.UUID = _df_series['UUID']
    return tc


def get_current_roster():
    r = _request_roster()
    players = process_request(r)
    c_r = process_current_positions(r)
    return players, c_r


def _request_roster():
    headers = {
        'Authorization': "Token 9007e963847a704cdb85684228924fa457ea5bf5"
    }
    base_url = 'https://jje-league.herokuapp.com/'
    url = os.path.join(base_url,'oauth/api/getroster/')
    
    r = requests.get(url, headers=headers, params={"team_id": 9})
    
    return r


def _request_FA_players(data=None, start_num=None):
    headers = {
        'Authorization': "Token 9007e963847a704cdb85684228924fa457ea5bf5"
    }
    base_url = 'https://jje-league.herokuapp.com/'
    url = os.path.join(base_url,'oauth/api/searchplayers/')
    if data is None:
        data = {
            'status': "FA",
            "sort_type": "lastweek",
            "sort": "AR",
        }
    if start_num is not None:
        data['start'] = start_num

    r = requests.get(url, headers=headers, params=data)
    return r


def process_FA(data=None, start_num=None):
    _fa = _request_FA_players(data, start_num)
    return process_request(_fa)


def process_request(r):
    soup = BeautifulSoup(r.text.replace("\\n", "\n"), 'html.parser')
    
    players = []
    for player in soup.find('players').find_all('player'):
        _id = get_number_or_none(player, 'player_id')
        _name = get_value_or_none(player, 'full')
        _positions = get_positions(player)
        players.append([_id,_name, ",".join(_positions)])
    return players


def process_current_positions(r):
    soup = BeautifulSoup(r.text.replace("\\n", "\n"), 'html.parser')
    
    players = []
    for player in soup.find('players').find_all('player'):
        _id = get_number_or_none(player, 'player_id')
        _name = get_value_or_none(player, 'full')
        _positions = player.find('selected_position').find('position').text
        _positions = _positions.replace("+", "")
        players.append([_id,_name, _positions])
    return players


def get_value_or_none(_soup, val):
    try:
        return _soup.find(val).text
    except:
        return None


def get_number_or_none(_soup, val, num_type=None):
    if num_type is None:
        num_type = int
    try:
        return num_type(get_value_or_none(_soup, val))
    except:
        return None
    

def get_positions(_soup):
    ep = _soup.find('eligible_positions')
    if ep is None:
        return []    
    return [v.text.replace("+", "") for v in ep.find_all('position') if v.text not in ['Util']]


def _get_icount(_cc):
    return max(list(itertools.accumulate([len(_cc[r]) for r in _cc if len(_cc[r])>0], operator.mul)))


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
        if (i%5000 == 0): _update_progress(i, _combo_count, **kwargs)
        
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


def get_player_data(player_id, driver):
    url = f'https://sports.yahoo.com/nhl/players/{player_id}/gamelog/'    
    driver.get(url)
    data = parse_site_data(driver, player_id)
    return data


def parse_site_data(driver, player_id, level=None):
    try:
        time.sleep(2)
        headers = [
            'player_id', 'Date', "G", "A", "Pts", "PM", "PIM", "Hits", "PPG", "PPA", "GWG"
        ]
        data = []
        
        bs = BeautifulSoup(driver.page_source)
        ys_gs = bs.find('div', attrs={'class': "ys-graph-stats"})
        tbody = ys_gs.find('tbody').find_all('tr')
        for tt in tbody:
            td = tt.find_all('td')
            vals = [player_id]
            vals.append(td[0].text)
            for i in [4, 5, 6, 7, 8 ,9, 11, 12, 15]:
                vals.append(int(td[i].text))
            data.append(vals)

        return data
    except Exception as e:
        print(e)
        if level is None:
            driver.find_element_by_link_text("Game Log").click()
            parse_site_data(driver, player_id, 1)
        else:
            return None


def collect_player_data(_players):
    """Should be list of players [id, name, positions]"""
    options = webdriver.ChromeOptions()
    options.add_argument('headless')    
    c = webdriver.Chrome(driver_path, options=options)
    headers, data = [], []
    ply_len = len(_players)
    for i_, player in enumerate(_players):
        _update_progress(i_+1, ply_len)
        _id = player[0]
        _d = get_player_data(_id, c)
        if _d is None: continue
        data.extend(_d)           
        stime = random.randint(1, 5)
        time.sleep(stime)
    _update_progress(ply_len, ply_len)
    c.quit()
    return data


def _create_frame(headers, data):
    def calc_date(val):
        year_2020 = ["Jan", "Feb", "Mar", "Apr"]
        yr = 2019
        if val.split(" ")[0] in year_2020:
            yr = 2020
        dt = datetime.datetime.strptime(f"{val} {yr}", "%b %d %Y")
        return dt
    
    df = pd.DataFrame(data, columns=headers)
    df["Date"] = df["Date"].apply(calc_date)
    df["PPP"] = df[['PPG', 'PPA']].sum(axis=1)
    df = df.drop(columns=['PPG', "PPA"])
    
    return df


def get_player_dataframe(_players):
    cache_df = check_cache_data()
    if cache_df is not None:
        check_players = [p for p in _players if (p[0] not in cache_df["player_id"].values) and (p[-1] not in ["G"])]    
    else:
        check_players = _players
    
    h = [
        'player_id', 'Date', "G", "A", "Pts", "PM", "PIM", "Hits", "PPG", "PPA", "GWG"
    ]
    if len(check_players)==0:
        print("No new data - loading cache")
        return cache_df
    
    d = collect_player_data(check_players)
    df = _create_frame(h, d)
    df = pd.concat([cache_df, df])
    save_cache_data(df)
    return df
    

def check_cache_data():
    td = datetime.datetime.today().strftime("%Y%m%d")
    data = []
    if os.path.isfile(f"df_{td}.csv"):
        _df = pd.read_csv(f"df_{td}.csv", index_col=0)
        _df["Date"] = pd.to_datetime(_df["Date"])
        return _df
    else:
        return None


def save_cache_data(_df):
    td = datetime.datetime.today().strftime("%Y%m%d")
    _df.to_csv(f"df_{td}.csv")


def reduce_frame(_df, _days=None):
    """this reduces the full list of games for the players down to a single row for the specified period"""
    if _days is None:
        _days=8
    _id_df = _df[["player_id"]].drop_duplicates().set_index("player_id")
    sum_df = _df.loc[_df['Date']>=datetime.datetime.today()-datetime.timedelta(days=_days)].groupby("player_id").sum()
    new_df = _id_df.join(sum_df).fillna(0)
    return new_df
    

def _print_positions(t_class, players):
    print("\n".join(["LW"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.LW]), "\n")
    print("\n".join(["C"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.C]), "\n")
    print("\n".join(["RW"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.RW]), "\n")
    print("\n".join(["D"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.D]), "\n")
    print("\n".join(["Util"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.Util]), "\n")
    print("\n".join(["G"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.G]), "\n")
    print("\n".join(["IR"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.IR]), "\n")
    print("\n".join(["BN"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.Bench]), "\n")


# actual work area
def player_list():
    # get my players
    print("loading player info")
    all_players, current_roster = get_current_roster()
    current_roster_class = team_from_list(current_roster)

    # this is list of players to check mixes of. Remove goalies and rookies from combinations
    _check_players = [p for p in all_players if p[0] not in [x[0] for x in rookies + goalies + bench_goalies]]
    _check_player_ids = [p[0] for p in _check_players]

    # get list of free agents
    _free_agents = [f for f in process_FA() for z in f[-1].split(",") if z not in ["G", "IR", "C"]]
    _free_agents_id = [f[0] for f in _free_agents]

    full_player_list = []
    ix = []
    for i in all_players + _free_agents:
        if i[0] not in ix:
            ix.append(i[0])
            full_player_list.append(i)

    # check players is my current team.
    # if i come up with a new permutation that works better i could just feed that in as the input
    # if a team combo has a free agent as the best option, then re run this using that player as the input
    tmp_ls = []
    for p in _free_agents:
        tmp_ls.append(_check_players + [p])
    print('')
    return {
        'all_players': all_players, 'current_roster_class': current_roster_class, 
        'check_players': _check_players, 'free_agents': _free_agents,  
        'full_player_list': full_player_list, 'team_list': tmp_ls,
        'original_roster_class': current_roster_class
    }


def performance_data(_check_players, _free_agents):
    # selenium BS4 loader
    print("Loading performance data")
    ply = get_player_dataframe(_check_players + _free_agents)
    res_df = reduce_frame(ply)
    print('')
    return res_df


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


def calculate_team_combinations(tmp_ls, current_roster_class):
    if os.path.exists(__teams_table):
        return __teams_table

    for i, tt in enumerate(tmp_ls):
        pt = [f"Team {i+1} of {len(tmp_ls)}"]
        print(pt[0])

        _pdict = build_positional_list(tt)
        _cdict = build_positional_combinations(_pdict)
        _ac_list = get_all_combinations(_cdict)
        print(f"{_get_icount(_cdict):,} total combinations")
        out_list = generate_unique_teams(
            _ac_list, tt+bench_goalies, [g[0] for g in goalies], [r[0] for r in rookies], 
            current_roster_class, _get_icount(_cdict)
        )
        print(f"{len(out_list):,} final teams")
        
        df = team_class_to_DF(out_list, start_print=pt+["Convering Classes to Data Frame"])
        df.to_hdf(__teams_table, key='team_list', format='table', append=True)
        print('')
        break
    return __teams_table


# noinspection PyTypeChecker
def generate_results(res_df):
    print("Generating Results")
    print("loading teams table")
    uuid_df = pd.read_hdf(__teams_table)
    uuid_df['Active'] = uuid_df["LW"]+','+uuid_df["C"]+','+uuid_df["RW"]+','+uuid_df["D"]
    uuid_df = uuid_df[["UUID", "Active"]]
    uuid_df.to_hdf(__uuid_table, key='team_list', format='table', append=True)
    del(uuid_df)
    chunk_size=10000
    for chunk in pd.read_hdf(__uuid_table, 'team_list', chunksize=chunk_size):
        chunk['Active'] = chunk["Active"].str.split(',')
        # chunk['Active'] = chunk['Active'].apply(lambda x: int(x))
        chunk = chunk.explode('Active').rename(columns={'Active': 'player_id'})
        chunk['player_id'] = chunk['player_id'].apply(lambda x: int(x))
        joined_df = chunk.merge(res_df, left_on='player_id', right_index=True)
        stats_df = joined_df.groupby('UUID').sum().drop(columns=['player_id'])
        stats_df.to_hdf(__results_table, key='team_list', format='table', append=True)
    return __results_table


def _is_team_identical(tc):
    n0 = [p.UUID for p in tc if p.number_of_adds == 0]
    if len(n0) > 1:
        return True
    else:
        return False


def rank_results(current_roster_class, full_player_list):
    print("Ranking Results")
    print("Loading team table")
    uuid_df = pd.read_hdf(__teams_table)

    print("loading results table")
    tmpdf = pd.read_hdf(__results_table)
    ranks = tmpdf.rank(method='min', ascending=False).mean(axis=1).to_frame("mean rank")
    ranks = ranks.join(ranks.rank(method='min')["mean rank"].to_frame('rank'))
    ranks = ranks.sort_values('rank')

    r1 = ranks.loc[ranks['rank'] == 1]
    ranks = r1.loc[~r1.index.duplicated(keep='first')]
    
    tc = []
    tl = ranks.loc[ranks['rank']==1].shape[0]
    print("Converting Highest rank teams")
    for ix, i in enumerate(ranks.loc[ranks['rank']==1].itertuples()):    
        _update_progress(ix+1, tl)
        tc.append(
            series_to_team_class(uuid_df.loc[uuid_df['UUID']==i[0]].iloc[0], current_roster_class)
        )
    print("")

    if _is_team_identical(tc):
        # means one of the teams equals the existing team, therefore that is the team to use
        return tc[0], True
    else:
        return tc[0], False


def _bench_players(tc):
    bn = []
    for p in tc:
        bn += [z for z in p.Bench + p.IR if z not in [x[0] for x in protected_list]]
    return bn


def print_results(tc, full_player_list, original_team_class):
    tc.CurrentRosterClass = original_team_class
    tc = [tc]

    print("Players detected to add")
    for p in list(set(([t.calculate_adds_drops()['add'][0] for t in tc]))):
        [print(r) for r in full_player_list if p == r[0]]
    print('')

    print("Players on bench in in optimal teams")
    bn = _bench_players([tc])

    bn = {c:bn.count(c) for c in set(bn)}
    bn = {y:bn[y] for y in bn if bn[y] == max([bn[x] for x in bn])}
    for p in bn:
        [print(r) for r in full_player_list if p == r[0]]
    print('')

    print("Optimal Roster", "\n")
    _print_positions(tc[0], full_player_list)
    return tc[0]


def main(plist=None, **kwargs):
    if plist is None:
        plist = player_list()

    res_df = performance_data(plist['check_players'], plist['free_agents'])
    calculate_team_combinations(plist['team_list'], plist['current_roster_class'])
    generate_results(res_df)
    otc, ident = rank_results(plist['current_roster_class'], plist['full_player_list'])
    if ident is True:
        print_results(otc, plist['full_player_list'], plist['original_roster_class'])
    else:
        main(generate_new_loop_data(plist, otc))
    # save_results()


def save_results(tc):
    uuid_df = pd.read_hdf(__teams_table)
    tmpdf = pd.read_hdf(__results_table)


def generate_new_loop_data(plist, optimal_team_class):
    if optimal_team_class.Active == plist['current_roster_class'].Active:
        return None

    bp = _bench_players([optimal_team_class])
    drop_player = bp[0]
    ap = [p for p in plist['all_players'] if p[0] != drop_player]
    crc = optimal_team_class
    ckp = [p for p in plist['check_players'] if p[0] != drop_player]
    fa = [p for p in plist['free_agents'] if p[0] != drop_player]
    fpl = [p for p in plist['full_player_list'] if p[0] != drop_player]
    team_list = [p for p in plist['team_list'] if p[0] != drop_player]

    return {
        'all_players': ap, 'current_roster_class': crc,
        'check_players': ckp, 'free_agents': fa,
        'full_player_list': fpl, 'team_list': team_list,
        'original_roster_class': plist['original_roster_class']
    }


if __name__ == '__main__':
    main()
"""
if i want to loop optimize i need to supply this dictionary
    return {
        'all_players': all_players, 'current_roster_class': current_roster_class, 
        'check_players': _check_players, 'free_agents': _free_agents,  
        'full_player_list': full_player_list, 'team_list': tmp_ls
    }
"""
