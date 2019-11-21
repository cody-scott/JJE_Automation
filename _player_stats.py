import time
import random
import datetime
import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from _helpers import _update_progress

driver_path = r"F:\A_Data Backup\Desktop\Projects\PycharmProjects\JJE_Automation\chromedriver.exe"
# driver_path = '/Users/codyscott/PycharmProjects/Jupyter/chromedriver'


def performance_data(_check_players, _free_agents):
    # selenium BS4 loader should add check on which players did not load. try it again if failed?
    print("Loading performance data")
    ply = get_player_dataframe(_check_players + _free_agents)
    res_df = reduce_frame(ply)
    print('')
    return res_df


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

        bs = BeautifulSoup(driver.page_source, 'html.parser')
        ys_gs = bs.find('div', attrs={'class': "ys-graph-stats"})
        tbody = ys_gs.find('tbody').find_all('tr')
        for tt in tbody:
            td = tt.find_all('td')
            vals = [player_id]
            vals.append(td[0].text)
            for i in [4, 5, 6, 7, 8, 9, 11, 12, 15]:
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
        _update_progress(i_ + 1, ply_len)
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
    if len(check_players) == 0:
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
        _days = 8
    _id_df = _df[["player_id"]].drop_duplicates().set_index("player_id")
    sum_df = _df.loc[_df['Date'] >= datetime.datetime.today() - datetime.timedelta(days=_days)].groupby(
        "player_id").sum()
    new_df = _id_df.join(sum_df).fillna(0)
    return new_df
