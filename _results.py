import pandas as pd
from _protected_lists import protected_list
from _helpers import _update_progress
from _team_list_class import series_to_team_class


def rank_results(current_roster_class, full_player_list, uuid_df, tmpdf):
    print("Ranking Results")
    ranks = tmpdf.rank(method='min', ascending=False).mean(axis=1).to_frame("mean rank")
    ranks = ranks.join(ranks.rank(method='min')["mean rank"].to_frame('rank'))
    ranks = ranks.sort_values('rank')

    r1 = ranks.loc[ranks['rank'] == 1]
    ranks = r1.loc[~r1.index.duplicated(keep='first')]

    tc = []
    tl = ranks.loc[ranks['rank'] == 1].shape[0]
    print("Converting Highest rank teams")  # add print tl here
    for ix, i in enumerate(ranks.loc[ranks['rank'] == 1].itertuples()):
        _update_progress(ix + 1, tl)
        tc.append(
            series_to_team_class(uuid_df.loc[uuid_df['UUID'] == i[0]].iloc[0], current_roster_class)
        )
    print("")

    if _is_team_identical(tc):
        # means one of the teams equals the existing team, therefore that is the team to use
        return tc[0], True
    else:
        return tc[0], False


def generate_results(res_df, uuid_df, __uuid_table, __results_table):
    print("Generating Results")
    # print("loading teams table")
    # uuid_df = pd.read_hdf(__teams_table)
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


def print_results(tc, full_player_list, original_team_class):
    tc.CurrentRosterClass = original_team_class
    tc = tc

    print("Players detected to add")
    for p in list(set(([t.calculate_adds_drops()['add'][0] for t in [tc]]))):
        [print(r) for r in full_player_list if p == r[0]]
    print('')

    print("Players on bench in in optimal teams")
    bn = _bench_players([tc])

    print("Players who've been dropped")
    i_v = [i for i in tc.FullList if i not in tc.CurrentRosterClass.FullList]


    bn = {c:bn.count(c) for c in set(bn)}
    bn = {y:bn[y] for y in bn if bn[y] == max([bn[x] for x in bn])}
    for p in bn:
        [print(r) for r in full_player_list if p == r[0]]
    print('')

    print("Optimal Roster", "\n")
    _print_positions(tc, full_player_list)
    return tc


def _bench_players(tc):
    bn = []
    for p in tc:
        bn += [z for z in p.Bench + p.IR if z not in [x[0] for x in protected_list]]
    return bn


def _print_positions(t_class, players):
    print("\n".join(["LW"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.LW]), "\n")
    print("\n".join(["C"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.C]), "\n")
    print("\n".join(["RW"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.RW]), "\n")
    print("\n".join(["D"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.D]), "\n")
    print("\n".join(["Util"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.Util]), "\n")
    print("\n".join(["G"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.G]), "\n")
    print("\n".join(["IR"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.IR]), "\n")
    print("\n".join(["BN"] + ["\t".join([str(x) for x in p]) for p in players if p[0] in t_class.Bench]), "\n")


def _is_team_identical(tc):
    n0 = [p.UUID for p in tc if p.number_of_adds == 0]
    if len(n0) > 1:
        return True
    else:
        return False
