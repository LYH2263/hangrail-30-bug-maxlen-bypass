
"""衣长上限判定：挂杆页配置值、上杆校验、占位段长共用同一口径。"""
from __future__ import annotations


def cap_allows(garment_cm: float, max_garment_cm: float | None) -> bool:
    """衣长严格大于该杆上限则不得占用；未配置上限（None）的杆不限衣长。"""
    if max_garment_cm is None:
        return True
    return garment_cm <= max_garment_cm
