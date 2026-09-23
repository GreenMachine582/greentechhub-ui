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
