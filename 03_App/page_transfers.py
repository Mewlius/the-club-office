"""Transfers: the arrivals and departures of the club for the selected season."""
from nicegui import ui

import football
import layout
import season_stats

# Transfer windows, from the date of each transfer (see season_stats.transfer_window)
WINDOWS = {"All": None, "Summer": "Summer", "Winter": "Winter"}

POSITION_SORT = f"(a, b) => {football.POSITION_ORDER}.indexOf(a) - {football.POSITION_ORDER}.indexOf(b)"


def width(percent: int) -> dict:
    """Same column widths in both tables, so that Arrivals and Departures line up."""
    return {"style": f"width: {percent}%", "headerStyle": f"width: {percent}%"}


def columns(club_label: str) -> list[dict]:
    return [
        {"name": "date", "label": "Date", "field": "date_sort", "sortable": True, "align": "left", **width(15)},
        {"name": "player", "label": "Player", "field": "player", "sortable": True, "align": "left", **width(23)},
        {"name": "position", "label": "Pos", "field": "position", "sortable": True, "align": "left",
         ":sort": POSITION_SORT, **width(8)},
        {"name": "age", "label": "Age", "field": "age", "sortable": True, **width(7)},
        {"name": "overall", "label": "OVR", "field": "overall", "sortable": True, **width(7)},
        {"name": "potential", "label": "POT", "field": "potential", "sortable": True, **width(7)},
        {"name": "club", "label": club_label, "field": "club", "sortable": True, "align": "left", **width(19)},
        {"name": "fee", "label": "Fee", "field": "fee_sort", "sortable": True, **width(14)},
    ]


# One template for every cell: unknown dates, position colour, fee or "Loan", exchange player
CELL = r'''
<q-td :props="props">
  <template v-if="props.col.name === 'date'">
    <span v-if="props.row.date_text">{{ props.row.date_text }}</span>
    <span v-else class="unknown">Unknown</span>
  </template>
  <template v-else-if="props.col.name === 'player'"><span class="player">{{ props.value }}</span></template>
  <template v-else-if="props.col.name === 'position'">
    <span v-if="props.value" :class="'pos pos-' + props.row.group">{{ props.value }}</span>
  </template>
  <template v-else-if="props.col.name === 'fee'">
    <span :class="props.row.loan ? 'loan' : 'fee'">{{ props.row.fee_text }}</span>
    <div v-if="props.row.exchange" class="exchange">+ {{ props.row.exchange }} (deal {{ props.row.deal_text }})</div>
  </template>
  <template v-else>{{ props.value === null || props.value === undefined || props.value === '' ? '-' : props.value }}</template>
</q-td>
'''


def table_rows(items: list[dict]) -> list[dict]:
    return [{
        "key": index,
        "date_sort": index,  # the list is already in date order
        "date_text": item["date_text"],
        "player": item["player"],
        "position": item["position"],
        "group": item["group"],
        "age": item["age"],
        "overall": item["overall"],
        "potential": item["potential"],
        "club": item["club"],
        "loan": item["loan"],
        "fee_sort": -1 if item["loan"] else item["fee"],
        "fee_text": "Loan" if item["loan"] else season_stats.money(item["fee"]),
        "exchange": item["exchange"],
        "deal_text": season_stats.money(item["deal_value"]),
    } for index, item in enumerate(items)]


def word(count: int, singular: str) -> str:
    """word(1, "arrival") -> arrival, word(3, "arrival") -> arrivals."""
    return singular if count == 1 else singular + "s"


@ui.page("/transfers")
def transfers_page() -> None:
    with layout.frame("/transfers", wide=True) as (career, season):
        if career is None:
            return

        rows = season_stats.season_rows(career["folder"], season, "transfers") if season else None

        if rows is None:
            ui.label("Transfers").classes("page-title")
            if season is None:
                ui.label("No season exported yet for this career.").classes("page-note")
            else:
                ui.label(f"No transfers exported for {season} yet. They arrive with the next export "
                         "of tco_session.lua in the game.").classes("page-note")
            return

        build_page(rows)


def build_page(rows: list[dict]) -> None:
    state = {"window": "All"}
    items = season_stats.transfer_list(rows)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Transfers").classes("page-title")
        ui.toggle(list(WINDOWS), value="All", on_change=lambda e: change_window(e.value)).props(
            "no-caps unelevated color=white text-color=primary toggle-color=primary toggle-text-color=white"
        ).classes("comp-toggle window-toggle")

    summary = ui.element("div").classes("summary w-full")
    unknown_note = ui.label().classes("page-note")

    with ui.element("div").classes("main-grid w-full"):
        with ui.column().classes("w-full min-w-0 gap-2"):
            tables = {}
            for direction, title, club_label in [("IN", "Arrivals", "From"), ("OUT", "Departures", "To")]:
                heading = ui.label(title).classes("panel-title")
                table = ui.table(
                    rows=[],
                    columns=columns(club_label),
                    row_key="key",
                    pagination={"rowsPerPage": 0, "sortBy": "date", "descending": False},
                ).props("dense flat hide-bottom").classes(f"transfer-table w-full {direction.lower()}-table")
                table.add_slot("body-cell", CELL)
                empty = ui.label().classes("page-note")
                tables[direction] = (title, heading, table, empty)

        panel = ui.column().classes("side-panel w-full gap-3")

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def refresh() -> None:
        window = WINDOWS[state["window"]]
        shown = [t for t in items if window is None or t["window"] == window]

        for direction, (title, heading, table, empty) in tables.items():
            moves = [t for t in shown if t["direction"] == direction]
            heading.set_text(f"{title} ({len(moves)})")
            table.rows = table_rows(moves)
            table.update()
            table.set_visibility(bool(moves))
            where = "this season" if window is None else f"in the {window.lower()} window"
            empty.set_text(f"No {'arrival' if direction == 'IN' else 'departure'} {where}.")
            empty.set_visibility(not moves)

        # Same figures as on Home, for the chosen window
        totals = season_stats.transfers([r for r in rows if window is None
                                         or season_stats.transfer_window(r.get("date")) == window])
        net = totals["net_spend"]
        summary.clear()
        with summary:
            for value, label, extra in [
                (totals["in"], word(totals["in"], "arrival")
                 + (f" ({totals['loans_in']} on loan)" if totals["loans_in"] else ""), ""),
                (totals["out"], word(totals["out"], "departure")
                 + (f" ({totals['loans_out']} on loan)" if totals["loans_out"] else ""), ""),
                (season_stats.money(totals["spent"]), "spent", ""),
                (season_stats.money(totals["received"]), "received", ""),
                (season_stats.money(net), "net spend", "money-out" if net > 0 else "money-in" if net < 0 else ""),
            ]:
                with ui.element("span"):
                    ui.label(str(value)).classes(f"value inline {extra}")
                    ui.label(label).classes("label inline")

        unknown = sum(1 for t in items if t["window"] is None)
        unknown_note.set_text(f"{unknown} {word(unknown, 'transfer')} with an unknown date "
                              f"{'is' if unknown == 1 else 'are'} only listed under All.")
        unknown_note.set_visibility(window is not None and unknown > 0)

    def change_window(window: str | None) -> None:
        state["window"] = window if window in WINDOWS else "All"
        refresh()

    # ------------------------------------------------------------------
    # Side panel: the biggest signing and sale of the season (all windows)
    # ------------------------------------------------------------------
    def side_panel() -> None:
        panel.clear()
        with panel:
            ui.label("Biggest deals of the season").classes("side-title")
            for direction, label, empty in [("IN", "Signing", "No signing with a fee this season."),
                                            ("OUT", "Sale", "No sale with a fee this season.")]:
                ui.label(label).classes("section-title")
                deal = season_stats.biggest_transfer(items, direction)
                if deal is None:
                    ui.label(empty).classes("side-note")
                    continue
                with ui.element("div").classes(f"deal {direction.lower()}-deal"):
                    ui.label(season_stats.money(deal["fee"])).classes("big-score")
                    with ui.column().classes("gap-0 min-w-0"):
                        with ui.row().classes("items-center gap-2 no-wrap min-w-0"):
                            if deal["position"]:
                                ui.label(deal["position"]).classes(f"pos pos-{deal['group']}")
                            ui.label(deal["player"]).classes("deal-player")
                        where = f"{'from' if direction == 'IN' else 'to'} {deal['club']}" if deal["club"] else ""
                        ui.label(", ".join(p for p in [where, deal["date_text"]] if p)).classes("side-note")
                        if deal["exchange"]:
                            ui.label(f"+ {deal['exchange']} (deal {season_stats.money(deal['deal_value'])})") \
                                .classes("side-note")

    refresh()
    side_panel()
