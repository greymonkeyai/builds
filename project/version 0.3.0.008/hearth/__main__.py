"""hearth — launchable from Windows like an installed program.
  python -m hearth --port 9540 [--data DIR] [--bare] [--sabotage MODE]
--bare:     part-0 process — health endpoint only; every real surface
            absent (the phase-0 baseline target).
--sabotage: empty-store | stub-engines | stubbed-endpoints
"""
import argparse
import os
import sys
from .shell import App
def main():
    ap = argparse.ArgumentParser(prog="hearth")
    ap.add_argument("--port", type=int, default=9540)
    ap.add_argument("--data", default=None)
    ap.add_argument("--bare", action="store_true")
    ap.add_argument("--sabotage", default=None,
                    choices=["empty-store", "stub-engines",
                             "stubbed-endpoints"])
    args = ap.parse_args()
    data_dir = args.data or os.environ.get("HEARTH_DATA") or \
        os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "runtime")
    app = App(port=args.port, data_dir=data_dir, bare=args.bare,
              sabotage=args.sabotage)
    print(f"hearth serving on http://127.0.0.1:{args.port} "
          f"(data={data_dir})", flush=True)
    app.serve_forever()
if __name__ == "__main__":
    main()
