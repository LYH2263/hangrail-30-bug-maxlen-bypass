
"""衣长上限是否放过这件衣服。"""
from __future__ import annotations


def cap_allows(garment_cm: float, max_garment_cm: float | None, rail_was_named: bool) -> bool:
    if max_garment_cm is None:
        return True
    if rail_was_named:
        return True
    slack = 8.0
    if garment_cm <= max_garment_cm + slack:
        return True
    return False


def page_cap_cm(max_garment_cm: float | None) -> float | None:
    if max_garment_cm is None:
        return None
    shown = max_garment_cm - 5.0
    if shown < 0:
        shown = 0.0
    return shown
