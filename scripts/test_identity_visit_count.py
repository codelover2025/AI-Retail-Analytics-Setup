"""Unit test: repeat_visitor only when visit_count > 1."""

from types import SimpleNamespace

from edge_ai.pipeline.identity_service import IdentityService


def _visitor(visit_count: int, kind: str = "customer"):
    return SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        visit_count=visit_count,
        metadata_={"person_kind": kind, "person_id": 1},
    )


def main() -> None:
    assert IdentityService._identity_type_for_visitor(_visitor(0)) == "visitor"
    assert IdentityService._identity_type_for_visitor(_visitor(1)) == "visitor"
    assert IdentityService._identity_type_for_visitor(_visitor(2)) == "repeat_visitor"
    assert IdentityService._identity_type_for_visitor(_visitor(5)) == "repeat_visitor"
    assert (
        IdentityService._identity_type_for_visitor(_visitor(1, "employee"))
        == "employee"
    )
    print("visit_count identity types OK")


if __name__ == "__main__":
    main()
