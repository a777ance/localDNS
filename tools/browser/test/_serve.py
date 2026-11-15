"""Build the explorer page into a temp folder and serve it on a free local port, for the Chromium tests.

    from _serve import served, CHROME, HERE
    with served() as base: ...  # base is "http://127.0.0.1:PORT"

CHROME is $CHROME, else /usr/bin/google-chrome if present, else None (Playwright's own Chromium).
"""
import contextlib, functools, http.server, os, pathlib, subprocess, sys, tempfile, threading

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHROME = os.environ.get("CHROME") or ("/usr/bin/google-chrome" if os.path.exists("/usr/bin/google-chrome") else None)


@contextlib.contextmanager
def served():
    with tempfile.TemporaryDirectory() as out:
        subprocess.run([sys.executable, str(ROOT / "tools/browser/explorer/build.py"), out], check=True, stdout=subprocess.DEVNULL)
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a):
                pass
        handler = functools.partial(Quiet, directory=out)
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            yield f"http://127.0.0.1:{srv.server_address[1]}"
        finally:
            srv.shutdown()
