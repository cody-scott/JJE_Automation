import itertools
import operator
from _protected_lists import protected_list


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


def _get_icount(_cc):
    return max(list(itertools.accumulate([len(_cc[r]) for r in _cc if len(_cc[r])>0], operator.mul)))


def _bench_players(tc):
    bn = []
    for p in tc:
        bn += [z for z in p.Bench + p.IR if z not in [x[0] for x in protected_list]]
    return bn