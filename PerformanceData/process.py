import time
import random
import datetime
import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from pathlib import Path

driver_path = Path('PerformanceData/driver/chromedriver')
year_val = 2021

def performance_data(players):
    # selenium BS4 loader should add check on which players did not load. try it again if failed?
    print("Loading performance data")
    ply = get_player_dataframe(players)
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
            'id', 'Date', "G", "A", "Pts", "PM", "PIM", "Hits", "PPG", "PPA", "GWG"
        ]
        data = []

        bs = BeautifulSoup(driver.page_source, 'html.parser')
        ys_gs = bs.find('div', attrs={'class': "ys-graph-stats"})
        tbody = ys_gs.find('tbody').find_all('tr')
        for tt in tbody:
            td = tt.find_all('td')
            vals = [player_id]
            vals.append(td[0].text)

            if td[0].text == "":
                x=1
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
    # c = webdriver.Chrome(driver_path, options=options)
    c = webdriver.Chrome(driver_path, options=options)
    headers, data = [], []
    ply_len = len(_players)
    for i_, player in enumerate(_players):
        _update_progress(i_ + 1, ply_len)
        _id = player['id']
        _d = get_player_data(_id, c)
        if _d is None: continue
        data.extend(_d)
        # stime = random.randint(1, 5)
        # time.sleep(stime)
    _update_progress(ply_len, ply_len)
    c.quit()
    return data


def _create_frame(headers, data):
    def calc_date(val):
        year_2020 = ["Jan", "Feb", "Mar", "Apr"]
        yr = year_val
        if val.split(" ")[0] in year_2020:
            yr = year_val + 1
        dt = datetime.datetime.strptime(f"{val} {yr}", "%b %d %Y")
        return dt

    df = pd.DataFrame(data, columns=headers)
    df["Date"] = df["Date"].apply(calc_date)
    df["ppp"] = df[['PPG', 'PPA']].sum(axis=1)
    df = df.drop(columns=['PPG', "PPA"])

    return df


def get_player_dataframe(_players):
    check_players = _players

    h = [
        'id', 'Date', "g", "a", "p", "pm", "pim", "hits", "PPG", "PPA", "gwg"
    ]
    if len(check_players) == 0:
        print("No new data - loading cache")
        return None

    d = collect_player_data(check_players)
    df = _create_frame(h, d)
    # df = pd.concat([cache_df, df])
    return df


def reduce_frame(_df, _days=None):
    """this reduces the full list of games for the players down to a single row for the specified period"""
    if _days is None:
        _days = 14
    _id_df = _df[["id"]].drop_duplicates().set_index("id")
    sum_df = _df.loc[_df['Date'] >= datetime.datetime.today() - datetime.timedelta(days=_days)].groupby(
        "id").sum()
    new_df = _id_df.join(sum_df).fillna(0)
    return new_df


def _update_progress(ci, mx_num=None, **kwargs):
    if mx_num is None:
        mx_num = 0

    if mx_num > 0:
        bar_length = 20
        # print(f"{ci:,} of {mx_num:,}")
        pg = (ci / mx_num)
        block = int(round(bar_length * pg))
        # print("\r")
        text = "\rProgress: [{0}] {1:.1f}%".format("#" * block + "-" * (bar_length - block), pg * 100)
        print(text, flush=True, end="")
    else:
        print(f"{ci:,}")

    for i in kwargs.get("end_print", []):
        print(i)

