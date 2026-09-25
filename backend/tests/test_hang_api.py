from sqlalchemy import select

from app.models.models import RailPlacement


def _fill_gaps(session, env):
    """填满 A、B 杆的剩余空隙（A 已占 0-80，B 已占 0-40）。"""
    a = env["rail"]("A 杆")
    b = env["rail"]("B 杆")
    filler = env["order"]("HR-2003").id
    session.add_all(
        [
            RailPlacement(rail_id=a.id, order_id=filler, start_cm=80, end_cm=200, active=1),
            RailPlacement(rail_id=b.id, order_id=filler, start_cm=40, end_cm=160, active=1),
        ]
    )
    session.commit()


def test_long_coat_skips_capped_rail_and_lands_on_b(env):
    # 种子：A 杆上限 80，羽绒服衣长 90。A 空余足够也必须跳过，继续试 B 并成功。
    order_id = env["order"]("HR-2003").id
    res = env["client"].post("/api/hang", json={"order_id": order_id})
    assert res.status_code == 200
    assert res.json()["status"] == "hung"

    session = env["session"]()
    try:
        order = env["order"]("HR-2003", session)
        active = session.scalars(
            select(RailPlacement).where(RailPlacement.order_id == order.id, RailPlacement.active == 1)
        ).all()
        assert len(active) == 1
        assert active[0].rail_id == env["rail"]("B 杆", session).id
        assert active[0].start_cm == 40
        assert active[0].end_cm == 130
    finally:
        session.close()


def test_all_rails_over_cap_returns_distinct_error(env):
    # 全店可试挂杆都因衣长上限拒挂 → 错误区别于单纯无空隙
    session = env["session"]()
    try:
        env["rail"]("B 杆", session).max_garment_cm = 80
        session.commit()
        order_id = env["order"]("HR-2003", session).id
    finally:
        session.close()

    res = env["client"].post("/api/hang", json={"order_id": order_id})
    assert res.status_code == 409
    detail = res.json()["detail"]
    assert detail != "挂杆空间不足"
    assert "衣长" in detail and "上限" in detail


def test_pure_no_space_returns_space_error(env):
    # 连衣裙衣长 30，未超任何杆上限；两杆填满 → 单纯无空隙错误
    session = env["session"]()
    try:
        _fill_gaps(session, env)
        order_id = env["order"]("HR-2004", session).id
    finally:
        session.close()

    res = env["client"].post("/api/hang", json={"order_id": order_id})
    assert res.status_code == 409
    assert res.json()["detail"] == "挂杆空间不足"


def test_uncapped_rail_accepts_long_garment(env):
    # B 杆未配置上限：即使 A 杆上限 80，指定挂 B 的 90cm 羽绒服可成功
    session = env["session"]()
    try:
        order_id = env["order"]("HR-2003", session).id
        b_id = env["rail"]("B 杆", session).id
        assert env["rail"]("B 杆", session).max_garment_cm is None
    finally:
        session.close()

    res = env["client"].post("/api/hang", json={"order_id": order_id, "rail_id": b_id})
    assert res.status_code == 200
    assert res.json()["status"] == "hung"


def test_named_over_cap_rail_is_rejected(env):
    # 指定上杆不享有豁免：90cm 羽绒服指定上上限 80 的 A 杆必须被拒，且不得产生占位
    session = env["session"]()
    try:
        order_id = env["order"]("HR-2003", session).id
        a_id = env["rail"]("A 杆", session).id
    finally:
        session.close()

    res = env["client"].post("/api/hang", json={"order_id": order_id, "rail_id": a_id})
    assert res.status_code == 409
    assert "衣长" in res.json()["detail"] and "上限" in res.json()["detail"]

    session = env["session"]()
    try:
        order = env["order"]("HR-2003", session)
        assert order.status == "ready"
        active = session.scalars(
            select(RailPlacement).where(RailPlacement.order_id == order.id, RailPlacement.active == 1)
        ).all()
        assert active == []
    finally:
        session.close()


def test_cap_is_strict_boundary_with_no_slack(env):
    # 81cm 工单（旧 8cm 容差下能上 A 杆）现在必须跳过 A 落 B；占位段长恰好 81，不大于…
    # 对 B（无上限）不限；同时验证等于上限 80 的工单在 A 上的段长正好等于上限
    session = env["session"]()
    try:
        from app.models.models import WorkOrder

        store_id = env["order"]("HR-2001", session).store_id
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        over = WorkOrder(
            store_id=store_id, ticket_code="HR-2101", garment_name="长风衣",
            length_cm=81, status="ready", due_at=now + timedelta(days=1),
        )
        edge = WorkOrder(
            store_id=store_id, ticket_code="HR-2102", garment_name="呢大衣",
            length_cm=80, status="ready", due_at=now + timedelta(days=1),
        )
        session.add_all([over, edge])
        session.commit()
        over_id, edge_id, a_id, b_id = over.id, edge.id, env["rail"]("A 杆", session).id, env["rail"]("B 杆", session).id
    finally:
        session.close()

    res = env["client"].post("/api/hang", json={"order_id": over_id})
    assert res.status_code == 200
    res = env["client"].post("/api/hang", json={"order_id": edge_id, "rail_id": a_id})
    assert res.status_code == 200

    session = env["session"]()
    try:
        over_pl = session.scalars(
            select(RailPlacement).where(RailPlacement.order_id == over_id, RailPlacement.active == 1)
        ).one()
        edge_pl = session.scalars(
            select(RailPlacement).where(RailPlacement.order_id == edge_id, RailPlacement.active == 1)
        ).one()
        # 81cm 被迫跳过 A，落在 B（B 已占 0-40）
        assert over_pl.rail_id == b_id
        assert over_pl.start_cm == 40 and over_pl.end_cm == 121
        # 恰好等于上限：A 上段长 = 上限，不会超过
        assert edge_pl.rail_id == a_id
        assert edge_pl.end_cm - edge_pl.start_cm == 80
    finally:
        session.close()


def test_sweep_never_sends_over_cap_back_to_capped_rail(env):
    # 连续自动扫杆两次：超限衣一旦落在无上限的 B，任何重试都不得把它送回 A
    order_id = env["order"]("HR-2003").id
    assert env["client"].post("/api/hang", json={"order_id": order_id}).status_code == 200
    # 再次扫描不应移动已挂工单；模拟人工重试也仍被 A 拒绝
    res = env["client"].post("/api/hang", json={"order_id": order_id, "rail_id": env["rail"]("A 杆").id})
    assert res.status_code == 400  # 已在杆上，状态不可重复上杆；关键是没有任何新占位落 A
    session = env["session"]()
    try:
        pls = session.scalars(
            select(RailPlacement).where(RailPlacement.order_id == order_id, RailPlacement.active == 1)
        ).all()
        assert len(pls) == 1
        assert pls[0].rail_id == env["rail"]("B 杆", session).id
    finally:
        session.close()


def test_patch_rail_cap_persists(env):
    a_id = env["rail"]("A 杆").id

    res = env["client"].patch(f"/api/rails/{a_id}", json={"max_garment_cm": 120})
    assert res.status_code == 200
    assert res.json()["max_garment_cm"] == 120

    # 重新获取（模拟再次进入页面）上限仍在
    res = env["client"].get("/api/rails")
    caps = {r["label"]: r["max_garment_cm"] for r in res.json()}
    assert caps["A 杆"] == 120
    assert caps["B 杆"] is None

    # 清空上限 → 不限衣长
    res = env["client"].patch(f"/api/rails/{a_id}", json={"max_garment_cm": None})
    assert res.status_code == 200
    assert res.json()["max_garment_cm"] is None
