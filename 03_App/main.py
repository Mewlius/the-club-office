"""The Club Office - start the app.

Launch with launch_app.bat (Windows) or `python main.py`.
"""
import os

from nicegui import app, ui

import page_overview  # noqa: F401  (registers the pages)
import page_player_stats  # noqa: F401
import sync

# Copy the new exports every time the app starts
app.on_startup(sync.sync_all)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="The Club Office",
        favicon="⚽",
        port=int(os.environ.get("TCO_PORT", "8765")),
        reload=False,
        show=os.environ.get("TCO_NO_BROWSER") is None,
    )
