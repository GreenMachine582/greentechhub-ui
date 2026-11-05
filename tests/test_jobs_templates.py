"""gth_job_status (v0.21) and the job_status.html / jobs_page.html templates
greentechhub-fastapi's JobViews renders: an active job polls and swaps its
own contents, shows progress, its message and Pause/Resume/Cancel; a
finished one is a gth_result_panel (badges, error, cancelled)."""

import re
from datetime import UTC, datetime

import html5lib
from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from test_macros_snapshot import assert_snapshot

import greentechhub_ui


def _env() -> Environment:
    env = Environment(autoescape=True, loader=ChoiceLoader([
        FileSystemLoader(greentechhub_ui.templates_path),
        FileSystemLoader(greentechhub_ui.components_path),
    ]))
    greentechhub_ui.install(env, service_name="Playground", nav_items=[])
    return env


def _job(**changes):
    job = {"id": "abc", "kind": "scan", "label": "Scan <music>", "owner": "local",
           "state": "running", "done": 3, "total": 12, "message": "D:/Music/a.mp3",
           "result": {}, "error": None, "created_at": None, "started_at": None,
           "finished_at": None, "active": True, "fraction": 0.25, "percent": 25}
    return job | changes


URLS = {"poll_url": "/jobs/abc", "pause_url": "/jobs/abc/pause",
        "resume_url": "/jobs/abc/resume", "cancel_url": "/jobs/abc/cancel"}


def _status(job, **context) -> str:
    return _env().get_template("job_status.html").render(job=job, **(URLS | context))


def test_a_running_job_polls_and_swaps_its_own_contents():
    html = _status(_job())
    wrapper = re.search(r'<div class="gth-job-status[^>]*>', html).group(0)
    assert 'aria-live="polite"' in wrapper and 'data-gth-job-state="running"' in wrapper
    assert 'hx-get="/jobs/abc" hx-trigger="every 1s"' in wrapper
    assert ('hx-target="#gth-job-abc" hx-select="#gth-job-abc .gth-job-body" '
            'hx-swap="innerHTML"') in wrapper
    assert '<div class="gth-job-running" aria-live="off">' in html


def test_progress_message_and_state():
    html = _status(_job())
    assert 'role="progressbar" aria-label="Scan &lt;music&gt;"' in html
    assert 'aria-valuenow="3"' in html and 'aria-valuemax="12"' in html
    assert 'aria-valuetext="3 of 12"' in html and "progress-bar-striped" in html
    assert ">Running</span>" in html
    assert 'class="small text-secondary mt-1 mb-0 text-truncate gth-job-message"' in html
    assert "D:/Music/a.mp3" in html


def test_an_unknown_total_is_indeterminate():
    html = _status(_job(total=None, done=0))
    assert "aria-valuenow" not in html and 'aria-valuetext="Working…"' in html


def test_pause_and_cancel_while_running_resume_while_paused():
    running = _status(_job())
    assert 'hx-post="/jobs/abc/pause"' in running and 'hx-post="/jobs/abc/cancel"' in running
    assert "gth-job-resume" not in running
    paused = _status(_job(state="paused"))
    assert 'hx-post="/jobs/abc/resume"' in paused and "gth-job-pause" not in paused
    assert ">Paused</span>" in paused and "progress-bar-striped" not in paused
    for button in re.findall(r"<button[^>]*>", running):
        assert 'hx-select="#gth-job-abc .gth-job-body"' in button
        assert 'hx-disabled-elt="this"' in button


def test_no_buttons_without_urls():
    html = _env().from_string(
        '{% from "jobs.html" import gth_job_status %}{{ gth_job_status(job) }}').render(job=_job())
    assert "gth-job-actions" not in html and "hx-get" not in html


def test_a_succeeded_job_is_a_result_panel():
    job = _job(state="succeeded", active=False, done=12,
               result={"files": 12, "badges": [["12 files", "good"], ["2 skipped", "warn"]],
                       "problems": ["bad.mp3 is unreadable"],
                       "link": {"url": "/library", "label": "Open the library"}})
    html = _status(job, poll_url=None)
    assert "hx-get" not in html and "gth-job-running" not in html
    assert "gth-result-panel" in html and "Scan &lt;music&gt;" in html
    assert "12 files" in html and "2 skipped" in html and "bad.mp3 is unreadable" in html
    assert 'href="/library"' in html and "Open the library" in html


def test_a_failed_job_shows_its_error():
    html = _status(_job(state="failed", active=False, error="Drive D: is not ready"), poll_url=None)
    assert "gth-toast-danger" in html and 'role="alert"' in html
    assert "Drive D: is not ready" in html


def test_a_cancelled_job_says_so():
    html = _status(_job(state="cancelled", active=False), poll_url=None)
    assert ">Cancelled</span>" in html and "gth-toast-danger" not in html


def test_snapshot_and_well_formed():
    html = _status(_job())
    assert_snapshot(html, "job_status_running")
    html5lib.HTMLParser(strict=True).parseFragment(html)
    done = _status(_job(state="succeeded", result={"badges": [["12 files", "good"]]}),
                   poll_url=None)
    html5lib.HTMLParser(strict=True).parseFragment(done)


def test_jobs_page_lists_jobs():
    started = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
    jobs = [_job(started_at=started, status_url="/jobs/abc"),
            _job(id="def", label="Build", state="failed", active=False, total=None,
                 error="disk full", message="", started_at=started, finished_at=started)]
    html = _env().get_template("jobs_page.html").render(page_title="Jobs", jobs=jobs,
                                                        jobs_url="/jobs")
    rows = re.findall(r"<tr>(.*?)</tr>", html.split("<tbody", 1)[1], re.S)
    assert len(rows) == 2
    assert "3 of 12 (25%)" in rows[0] and ">Running</span>" in rows[0]
    assert ">Failed</span>" in rows[1] and "disk full" in rows[1]
    assert '<time datetime="2026-10-01T09:00:00+00:00">' in rows[1]
    html5lib.HTMLParser(strict=True).parse(html)
    assert "No jobs have run yet." in _env().get_template("jobs_page.html").render(jobs=[])
