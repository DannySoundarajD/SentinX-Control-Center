# -*- coding: utf-8 -*-
"""Entry point for SentinX Control Center.

Running ``python3 main.py`` launches the GTK4/LibAdwaita application.
"""

from __future__ import annotations

import sys

# Import the application class defined in ``app.py``.
from app import SentinXApp


def main(argv: list[str] | None = None) -> int:
    """Create the :class:`SentinXApp` instance and run it.

    Parameters
    ----------
    argv:
        Optional list of arguments – defaults to ``sys.argv``.
    """
    app = SentinXApp()
    return app.run(argv if argv is not None else sys.argv)


if __name__ == "__main__":
    sys.exit(main())
