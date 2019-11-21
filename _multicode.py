from _helpers import _update_progress


def update_progress(p_dict):
    for i in p_dict:
        c = p_dict[i].get('current')
        e = p_dict[i].get('total')
        _update_progress(c, e)
