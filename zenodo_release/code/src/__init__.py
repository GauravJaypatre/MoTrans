"""MoTrans-15 — dataset construction package."""

import datetime


def split_tag(date: datetime.date) -> str:
    """Return the sample-split label for a given date.

    Rules (from PROJECT_SPEC.md §Locked Design):
        train       : up to 2019-12-31
        crisis      : 2020-01-01 to 2021-12-31
        blind_test  : 2022-01-01 onward
    """
    if date <= datetime.date(2019, 12, 31):
        return "train"
    elif date <= datetime.date(2021, 12, 31):
        return "crisis"
    else:
        return "blind_test"
