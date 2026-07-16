[← Back to README](../README.md)

# 🔌 The Framework-Agnostic Template Contract

This is the standout design decision of `greentechhub-ui` — the piece that makes the rest of the package possible.

FastAPI's `Jinja2Templates` and Django's `Jinja2` template backend (`django.template.backends.jinja2.Jinja2`) are **both just Jinja2 underneath**. That means the same `.html` macro files can render correctly from a FastAPI service (BottleBot, PyFinBot) *and* from GreenTechHub's Django app — without a rewrite — as long as the macros don't reach for framework-specific globals (FastAPI's `request`, Django's `request.user`, differing `url_for` signatures).

So `greentechhub-ui` macros are written against a **plain context contract** instead of a framework object:

```python
# what every macro expects in its Jinja2 context — nothing framework-specific
{
  "nav_items": [...],        # from navigation.py
  "current_user": {...} | None,
  "flashes": [...],          # from greentechhub-core's flash module (or Django messages, adapted)
  "url_for": callable,       # injected per-framework: FastAPI's request.url_for, or a thin Django shim
  "brand": {"name": "GreenTechHub", "logo_url": "...", "service_name": "PyFinBot"},
  "extra_head": [...],       # optional per-page <head> additions — see docs/extensibility.md
}
```

**Practical effect**: GreenTechHub doesn't have to migrate off Django to get the same navbar, cards, and modals as PyFinBot and BottleBot — it wires Django's Jinja2 backend to the same template/macro directories and supplies the same context shape.

Worth calling out explicitly because it's not obvious from "just use Jinja2 macros" — the contract discipline is what actually makes it portable. Concrete wiring for both frameworks is in [docs/architecture.md](architecture.md#integration-pattern).
