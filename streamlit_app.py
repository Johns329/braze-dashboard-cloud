"""Streamlit Community Cloud entrypoint.

This wrapper keeps the original app code located at dashboard/app.py.
"""

from __future__ import annotations

import os
import runpy


def main() -> None:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    runpy.run_path(os.path.join("dashboard", "app.py"), run_name="__main__")


if __name__ == "__main__":
    main()
