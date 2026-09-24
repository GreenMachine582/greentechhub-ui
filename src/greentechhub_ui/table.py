"""TableState — one config object drives gth_data_table's navigation.

A table's navigation is a per-table *config* choice, not a different
template: the same `gth_data_table` call renders

- ``"none"``      — every row the consumer passes, no controls
- ``"load_more"`` — a trailing "Load more" row that appends the next page
- ``"infinite"``  — the same row, fired when it scrolls into view
- ``"pages"``     — numbered page links (+ optional page-size select)

plus sortable headers and a filter bar in every mode. The state is parsed
from the request's query (any ``Mapping`` — FastAPI's
``request.query_params``, Django's ``request.GET``), so it's framework-
agnostic like the rest of the package::

    state = TableState.from_query(request.query_params, id="stocks",
                                  base_url="/stocks", mode="pages",
                                  sortable=("name", "price"), page_sizes=(25, 50))
    rows, total = repo.list(offset=state.offset, limit=state.limit,
                            sort=state.sort, direction=state.direction, **state.filters)
    state = state.with_result(total=total)

Query parameters (fixed names): ``page``, ``size``, ``sort``, ``dir``,
``partial=rows`` (a load-more/infinite append — render only the rows), and
one per ``filter_params`` entry.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from urllib.parse import urlencode

from greentechhub_ui.htmx import hx_target

MODES = ("none", "load_more", "infinite", "pages")

# Sentinel for url() overrides: "leave this parameter as the state has it".
_KEEP = object()


def _int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class TableState:
    id: str
    base_url: str
    mode: str = "load_more"
    page: int = 1
    page_size: int = 25
    default_page_size: int = 25
    page_sizes: tuple[int, ...] = ()
    sort: str | None = None
    direction: str = "asc"
    default_sort: str | None = None
    default_direction: str = "asc"
    sortable: tuple[str, ...] = ()
    filters: Mapping[str, str] = field(default_factory=dict)
    filter_params: tuple[str, ...] = ("q",)
    total: int | None = None
    has_next: bool | None = None
    rows_only: bool = False
    push_url: bool = False
    window: int = 2
    max_height: str | None = None

    def __post_init__(self):
        if self.mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {self.mode!r}")

    @classmethod
    def from_query(
        cls,
        query: Mapping[str, str],
        *,
        id: str,
        base_url: str,
        mode: str = "load_more",
        page_size: int = 25,
        page_sizes: Iterable[int] = (),
        sortable: Iterable[str] = (),
        default_sort: str | None = None,
        default_direction: str = "asc",
        filter_params: Iterable[str] = ("q",),
        total: int | None = None,
        has_next: bool | None = None,
        push_url: bool = False,
        window: int = 2,
        max_height: str | None = None,
    ) -> "TableState":
        """Parse page/size/sort/dir/filters from `query`, ignoring anything
        out of range or not allow-listed (a hand-edited URL can't request
        an unsortable column or a 10,000-row page)."""
        page_sizes = tuple(page_sizes)
        sortable = tuple(sortable)
        filter_params = tuple(filter_params)

        size = _int(query.get("size"), page_size)
        if size not in page_sizes:
            size = page_size

        sort = query.get("sort")
        if sort in sortable:
            direction = "desc" if query.get("dir") == "desc" else "asc"
        else:
            sort, direction = default_sort, default_direction

        filters = {}
        for name in filter_params:
            value = (query.get(name) or "").strip()
            if value:
                filters[name] = value

        return cls(
            id=id,
            base_url=base_url,
            mode=mode,
            page=max(1, _int(query.get("page"), 1)),
            page_size=size,
            default_page_size=page_size,
            page_sizes=page_sizes,
            sort=sort,
            direction=direction,
            default_sort=default_sort,
            default_direction=default_direction,
            sortable=sortable,
            filters=filters,
            filter_params=filter_params,
            total=total,
            has_next=has_next,
            rows_only=query.get("partial") == "rows" and mode in ("load_more", "infinite"),
            push_url=push_url,
            window=window,
            max_height=max_height,
        )

    def with_result(self, *, total: int | None = None, has_next: bool | None = None):
        """The state once the page has been fetched: pass `total` when the
        count is known, or `has_next` (e.g. fetch limit+1 rows) when not."""
        return replace(self, total=total, has_next=has_next)

    # ── Paging math ──────────────────────────────────────────────────────

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size

    @property
    def total_pages(self) -> int | None:
        if self.total is None:
            return None
        return max(1, -(-self.total // self.page_size))

    @property
    def is_last_page(self) -> bool:
        if self.total is not None:
            return self.page >= self.total_pages
        return not self.has_next

    def page_links(self) -> list[int | None]:
        """Page numbers to show, None for an ellipsis: first, last, and
        `window` pages either side of the current one. A gap of exactly one
        page shows that page rather than an ellipsis."""
        last = self.total_pages
        if last is None:
            return []
        shown = {1, last} | set(range(self.page - self.window, self.page + self.window + 1))
        pages = sorted(p for p in shown if 1 <= p <= last)
        links: list[int | None] = []
        for p in pages:
            if links and p - links[-1] == 2:
                links.append(p - 1)
            elif links and p - links[-1] > 2:
                links.append(None)
            links.append(p)
        return links

    # ── URLs ─────────────────────────────────────────────────────────────

    def url(self, *, page=_KEEP, size=_KEEP, sort=_KEEP, dir=_KEEP, partial=None, **filters) -> str:
        """This table's URL with the current sort/filters/size, overriding
        any of them (None drops a parameter). Defaults are left out, so the
        URLs stay short: page 1, the default size, the default sort."""
        page = self.page if page is _KEEP else page
        size = self.page_size if size is _KEEP else size
        sort = self.sort if sort is _KEEP else sort
        direction = self.direction if dir is _KEEP else dir

        params: list[tuple[str, object]] = []
        merged = {**self.filters, **filters}
        params += [(k, v) for k, v in merged.items() if v not in (None, "")]
        if sort is not None and (sort, direction) != (self.default_sort, self.default_direction):
            params += [("sort", sort), ("dir", direction or "asc")]
        if size is not None and size != self.default_page_size:
            params.append(("size", size))
        if page is not None and page != 1:
            params.append(("page", page))
        if partial:
            params.append(("partial", partial))
        if not params:
            return self.base_url
        sep = "&" if "?" in self.base_url else "?"
        return self.base_url + sep + urlencode(params)

    def page_url(self, page: int) -> str:
        return self.url(page=page)

    @property
    def next_url(self) -> str | None:
        """Next page. For load_more/infinite it's a rows-only append URL."""
        if self.mode == "none" or self.is_last_page:
            return None
        partial = "rows" if self.mode in ("load_more", "infinite") else None
        return self.url(page=self.page + 1, partial=partial)

    @property
    def prev_url(self) -> str | None:
        return self.url(page=self.page - 1) if self.page > 1 else None

    def sort_url(self, key: str) -> str:
        """Sort by `key` from page 1: ascending, or flipped if it's already
        the sort column."""
        if self.sort == key:
            direction = "desc" if self.direction == "asc" else "asc"
        else:
            direction = "asc"
        return self.url(page=None, sort=key, dir=direction)

    def aria_sort(self, key: str) -> str | None:
        if self.sort != key:
            return None
        return "descending" if self.direction == "desc" else "ascending"

    @property
    def filter_url(self) -> str:
        """Base for gth_table_filter's form: page 1, without the filter
        params (the form's own inputs supply them)."""
        return self.url(page=None, **{name: None for name in self.filter_params})

    def is_own_swap(self, headers: Mapping[str, str]) -> bool:
        """This request is one of this table's own controls re-requesting it
        (sort, filter, pager: HX-Target is the table's id) — e.g. a record
        picker's panel endpoint returns just the table then, and the filter
        bar + table on the panel's first load."""
        return hx_target(headers) == self.id

    @property
    def size_url(self) -> str:
        """Base for the page-size select (which supplies `size` itself)."""
        return self.url(page=None, size=None)
