"""The Club Office - start the app.

Launch with launch_app.bat (Windows) or `python main.py`.
"""
import os

from nicegui import app, ui

import identity
import page_careers  # noqa: F401  (registers the pages)
import page_data  # noqa: F401
import page_history  # noqa: F401
import page_home  # noqa: F401
import page_matches  # noqa: F401
import page_player_stats  # noqa: F401
import page_standings  # noqa: F401
import page_transfers  # noqa: F401
import settings
import sync

# Copy the new exports every time the app starts
app.on_startup(sync.sync_all)

# Logos and banners of the careers, and the app's own logo (identity.py)
for folder, url in [(settings.careers_assets_dir(), identity.URL_CAREERS), (settings.app_assets_dir(), identity.URL_APP)]:
    folder.mkdir(parents=True, exist_ok=True)
    app.add_static_files(url, folder, max_cache_age=0)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="The Club Office",
        favicon="⚽",
        port=int(os.environ.get("TCO_PORT", "8765")),
        reload=False,
        show=os.environ.get("TCO_NO_BROWSER") is None,
    )
