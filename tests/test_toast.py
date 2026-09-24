import json

from greentechhub_ui import toast


def test_toast_only():
    assert json.loads(toast("Saved")) == {"showToast": {"message": "Saved", "kind": "success"}}


def test_toast_kind():
    assert json.loads(toast("Careful", "warning"))["showToast"]["kind"] == "warning"


def test_toast_merges_extra_events_into_one_header():
    payload = json.loads(toast("Saved", events=["closeModal", "stocksChanged"]))
    assert payload == {
        "showToast": {"message": "Saved", "kind": "success"},
        "closeModal": True,
        "stocksChanged": True,
    }


def test_defaults_stay_minimal():
    # A plain toast is exactly the pre-v0.8 payload: new options only appear when set.
    assert json.loads(toast("Saved")) == {"showToast": {"message": "Saved", "kind": "success"}}


def test_all_options_in_one_header():
    payload = json.loads(toast(
        "Deployed", "info", title="Deploy", icon="rocket", action={"label": "Open", "url": "/d"},
        duration=0, variant="solid", html=True, events=["closeModal"],
    ))
    assert payload == {
        "showToast": {"message": "Deployed", "kind": "info", "title": "Deploy", "icon": "rocket",
                      "action": {"label": "Open", "url": "/d"}, "duration": 0,
                      "variant": "solid", "html": True},
        "closeModal": True,
    }


def test_rejects_bad_variant_and_negative_duration():
    import pytest

    with pytest.raises(ValueError):
        toast("x", variant="glass")
    with pytest.raises(ValueError):
        toast("x", duration=-1)
