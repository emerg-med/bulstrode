from datetime import datetime
from itertools import groupby
from django.utils import timezone


# expando object, i.e. a class that we can add properties to dynamically
class Expando(object):
    def __init__(self, *args, **kwargs):
        if len(kwargs) > 0:
            for k in kwargs.keys():
                setattr(self, k, kwargs[k])


def multi_group_by(items, sort_keys, group_keys, level=0):
    if level == len(sort_keys) - 1:
        return sorted(items, key=lambda x: (getattr(x, sort_keys[level]), group_keys))

    if level >= len(sort_keys):
        return items

    group_key = group_keys[level]
    sort_key = sort_keys[level]

    return [(g[0], multi_group_by(g[1], sort_keys, group_keys, level + 1))
            for g in groupby(sorted(items, key=lambda x: getattr(x, sort_key)), lambda x: getattr(x, group_key))]


# Django's timezone.now() doesn't always return UTC (depends on config); this is the essence of that code but UTC only
def utc_now():
    return datetime.utcnow().replace(tzinfo=timezone.utc)
