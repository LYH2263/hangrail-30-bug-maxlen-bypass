
"""衣长上限是否放过这件衣服。"""
from __future__ import annotations


def cap_allows(garment_cm: float, max_garment_cm: float | None) -> bool:
    # 未配置上限的杆不限衣长；配置了上限的杆严格拒收超限衣，
    # 不设容差，也不因"指定了杆"而放行。
    if max_garment_cm is None:
        return True
    return garment_cm <= max_garment_cm


def page_cap_cm(max_garment_cm: float | None) -> float | None:
    # 挂杆页展示与杆配置同源：页面看到的上限就是上杆校验用的上限。
    return max_garment_cm
