"""browser_shim: lets the repo's tools/ scripts run where there are no real processes, no git and no bash.

Nothing here makes a check pass that would not pass: whatever cannot be emulated fails, raises, or is reported SKIP.

  * python subprocesses (sys.executable / python3 <script> ...) run in-process, with argv, stdin, stdout, cwd and env isolated.
  * git is answered read-only from the bundled snapshot (a clean checkout of one commit). Network git (ls-remote, push, fetch),
    anything that mutates, and any directory that is not the snapshot root answer like real git would when it cannot comply.
  * bash and every other program: FileNotFoundError, as on a machine without it.
  * long-running Popen children (servers, watchers): unsupported, OSError.
  * signal.alarm timeouts are no-ops here, so a runaway check is not interrupted.
"""
import sys, os, io, runpy, traceback, signal, types, re, json, shlex, tempfile

ROOT = "/repo"
HEAD = "0" * 40
BRANCH = "leader"
_PYNAMES = {"python", "python3"}

PIPE, STDOUT, DEVNULL = -1, -2, -3


class TimeoutExpired(Exception):
    def __init__(self, cmd, timeout, output=None, stderr=None):
        super().__init__("Command %r timed out after %s seconds" % (cmd, timeout))
        self.cmd, self.timeout, self.output, self.stderr = cmd, timeout, output, stderr


class CalledProcessError(Exception):
    def __init__(self, returncode, cmd, output=None, stderr=None):
        super().__init__("Command %r returned non-zero exit status %s." % (cmd, returncode))
        self.returncode, self.cmd, self.output, self.stdout, self.stderr = returncode, cmd, output, output, stderr


class CompletedProcess:
    def __init__(self, args, returncode, stdout=None, stderr=None):
        self.args, self.returncode, self.stdout, self.stderr = args, returncode, stdout, stderr

    def check_returncode(self):
        if self.returncode:
            raise CalledProcessError(self.returncode, self.args, self.stdout, self.stderr)


def _is_py(c0):
    return c0 in _PYNAMES or (bool(sys.executable) and c0 == sys.executable) or os.path.basename(c0).startswith("python")


def _in_repo(cwd):
    c = os.path.realpath(cwd or os.getcwd())
    r = os.path.realpath(ROOT)
    return c == r or c.startswith(r + os.sep)


def _git(args, cwd):
    """Return (returncode, stdout, stderr) the way git would answer for the bundled clean snapshot."""
    args = list(args)
    while args and args[0] == "-C" and len(args) >= 2:
        cwd = os.path.join(cwd or os.getcwd(), args[1])
        args = args[2:]
    if not _in_repo(cwd):
        return 128, "", "fatal: not a git repository (or any of the parent directories): .git\n"
    if not args:
        return 1, "", "usage: git <command>\n"
    a = args
    if a[:2] == ["status", "--porcelain"] and len(a) == 2:
        return 0, "", ""
    if a == ["rev-parse", "HEAD"]:
        return 0, HEAD + "\n", ""
    if a == ["rev-parse", "--abbrev-ref", "HEAD"]:
        return 0, BRANCH + "\n", ""
    if a == ["rev-parse", "--short", "HEAD"]:
        return 0, HEAD[:7] + "\n", ""
    if a == ["rev-parse", "--show-toplevel"]:
        return 0, ROOT + "\n", ""
    if a[0] == "diff" and "--name-only" in a and len(a) == 3 and a[2].count("...") == 1:
        left, right = a[2].split("...")
        known = {"origin/" + BRANCH, BRANCH, "HEAD"}
        if left in known and right in known:
            return 0, "", ""
        return 128, "", "fatal: bad revision '%s' (only the bundled branch is available here)\n" % a[2]
    if a == ["ls-files"]:
        rels = []
        for d, ds, fs in os.walk(ROOT):
            for f in fs:
                rels.append(os.path.relpath(os.path.join(d, f), ROOT))
        return 0, "\n".join(sorted(rels)) + "\n", ""
    if a[0] in ("ls-remote", "push", "fetch", "pull", "clone"):
        return 128, "", "fatal: unable to access remote: no network from the browser\n"
    return 128, "", "git: '%s' is not available in the browser snapshot\n" % " ".join(a)


def _run_py(args, input_text, cwd, env):
    """Run `python <script> ...` in-process; returns (returncode, stdout, stderr)."""
    args = list(args)
    while args and args[0].startswith("-"):
        flag = args.pop(0)
        if flag in ("-c", "-m"):
            raise OSError("python %s is not supported in the browser" % flag)
    if not args:
        raise OSError("interactive python is not supported in the browser")
    script, rest = args[0], args[1:]
    if cwd and not os.path.isabs(script):
        script = os.path.join(cwd, script)
    saved = (sys.argv, sys.stdin, sys.stdout, sys.stderr, os.getcwd(), dict(os.environ), list(sys.path), set(sys.modules))
    out, err = io.StringIO(), io.StringIO()
    code = 0
    try:
        if cwd:
            os.chdir(cwd)
        if env is not None:
            os.environ.clear()
            os.environ.update(env)
        sys.argv = [script] + rest
        sys.stdin = io.StringIO(input_text or "")
        sys.stdout, sys.stderr = out, err
        sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
        try:
            runpy.run_path(script, run_name="__main__")
        except SystemExit as e:
            c = e.code
            if c is None:
                code = 0
            elif isinstance(c, int):
                code = c
            else:
                err.write(str(c) + "\n")
                code = 1
        except BaseException:
            traceback.print_exc(file=err)
            code = 1
    finally:
        sys.argv, sys.stdin, sys.stdout, sys.stderr = saved[0], saved[1], saved[2], saved[3]
        try:
            os.chdir(saved[4])
        except OSError:
            pass
        os.environ.clear()
        os.environ.update(saved[5])
        sys.path[:] = saved[6]
        tmp = tempfile.gettempdir()
        for name in set(sys.modules) - saved[7]:
            f = getattr(sys.modules.get(name), "__file__", None) or ""
            if f.startswith(ROOT) or f.startswith(tmp):
                sys.modules.pop(name, None)
    return code, out.getvalue(), err.getvalue()


def run(args, *, input=None, capture_output=False, stdout=None, stderr=None, text=None, universal_newlines=None,
        cwd=None, env=None, timeout=None, check=False, encoding=None, errors=None, shell=False, stdin=None, **kw):
    if isinstance(args, (str, bytes)):
        args = shlex.split(args.decode() if isinstance(args, bytes) else args)
    args = [os.fspath(a) for a in args]
    if not args:
        raise ValueError("empty command")
    cwd = os.fspath(cwd) if cwd is not None else None
    want_text = bool(text or universal_newlines or encoding)
    if isinstance(input, bytes):
        input = input.decode()
    c0 = args[0]
    if _is_py(c0):
        rc, o, e = _run_py(args[1:], input, cwd, env)
    elif c0 == "git":
        rc, o, e = _git(args[1:], cwd)
    else:
        raise FileNotFoundError(2, "No such file or directory: %r (not available in the browser)" % c0)
    cap_out = capture_output or stdout == PIPE
    cap_err = capture_output or stderr == PIPE
    if stderr == STDOUT:
        o, e, cap_err = o + e, "", False
        cap_out = cap_out or stdout == PIPE
    if not cap_out:
        sys.stdout.write(o)
        o = None
    if not cap_err and e:
        sys.stderr.write(e)
    if not cap_err:
        e = None
    if not want_text:
        o = o.encode() if o is not None else None
        e = e.encode() if e is not None else None
    cp = CompletedProcess(args, rc, o, e)
    if check and rc:
        raise CalledProcessError(rc, args, o, e)
    return cp


def call(args, **kw):
    return run(args, **kw).returncode


def check_call(args, **kw):
    kw["check"] = True
    return run(args, **kw).returncode


def check_output(args, **kw):
    kw["check"] = True
    kw["stdout"] = PIPE
    return run(args, **kw).stdout


class Popen:
    def __init__(self, *a, **k):
        raise OSError("long-running child processes are not supported in the browser")


def _make_subprocess():
    m = types.ModuleType("subprocess")
    for k, v in dict(BROWSER_SHIM=True, PIPE=PIPE, STDOUT=STDOUT, DEVNULL=DEVNULL, TimeoutExpired=TimeoutExpired,
                     CalledProcessError=CalledProcessError, CompletedProcess=CompletedProcess, run=run, call=call,
                     check_call=check_call, check_output=check_output, Popen=Popen, SubprocessError=Exception).items():
        setattr(m, k, v)
    return m


def install(root, head, branch):
    global ROOT, HEAD, BRANCH
    ROOT, HEAD, BRANCH = root, head, branch
    sys.modules["subprocess"] = _make_subprocess()
    if not hasattr(signal, "SIGALRM"):
        signal.SIGALRM = 14
    if not hasattr(signal, "alarm"):
        signal.alarm = lambda n: 0
    _real = signal.signal

    def _sig(num, handler):
        try:
            return _real(num, handler)
        except (OSError, ValueError, RuntimeError):
            return None
    signal.signal = _sig


def run_script(path):
    """Run one tools/ script the way `python3 <path>` would from the repo root: (exit code, combined output)."""
    rc, o, e = _run_py([path], None, ROOT, None)
    return rc, o + e


# ------------------------------------------------------------------ check-all.sh, ported
_REQUIRED = ["CLAUDE.md", ".claude/cardinal-map.json", ".claude/hooks/cardinal.py", ".claude/hooks/decide-act.py",
             ".claude/hooks/gate.sh", "tools/matrix.py", "tools/racetrack.py", "docs/ai-cto/fleet/racetrack/RULES.md"]
_STEP_NAMES = ["clean working tree", "leader matches origin/leader", "orient.probe", "decide.probe", "observe.probe push",
               "check-cardinal", "check-superfleet", "check-decisions", "check-docs", "check-provenance", "check-registers",
               "racetrack arena self-test", "no agent running (agent ledger)", "check-matrix (end to end)",
               "check-stop-hook", "check-doctrine", "check-statements"]


def check_all(quick=False):
    steps = []

    def add(group, name, status, detail=""):
        steps.append({"group": group, "name": name, "status": status, "detail": detail})

    def py(group, name, *argv):
        try:
            r = run(["python3", *argv], cwd=ROOT, capture_output=True, text=True)
            o = ((r.stdout or "") + (r.stderr or "")).strip()
            if r.returncode == 0:
                add(group, name, "pass")
            else:
                add(group, name, "fail", "exit %d\n%s" % (r.returncode, "\n".join(o.splitlines()[-6:])))
        except Exception as e:  # a missing capability is a failure to verify, never a pass
            add(group, name, "fail", "%s: %s" % (type(e).__name__, e))

    g = "repo state"
    rc, o, _ = _git(["status", "--porcelain"], ROOT)
    add(g, "clean working tree", "pass" if rc == 0 and not o.strip() else "fail",
        "the bundled snapshot is a clean checkout of %s" % HEAD[:7])
    add(g, "leader matches origin/leader", "skip", "needs the network (git ls-remote); not checkable from a browser")
    g = "required files"
    for f in _REQUIRED:
        add(g, "present " + f, "pass" if os.path.exists(os.path.join(ROOT, f)) else "fail")
    g = "matrix probes (lane 0)"
    py(g, "orient.probe", "tools/matrix.py", "orient.probe")
    py(g, "decide.probe", "tools/matrix.py", "decide.probe")
    py(g, "observe.probe push", "tools/matrix.py", "observe.probe", "push")
    g = "static gates"
    py(g, "check-cardinal", "tools/check-cardinal.py")
    py(g, "check-superfleet", "tools/check-superfleet.py")
    py(g, "check-decisions", "tools/check-decisions.py")
    py(g, "check-docs", "tools/check-docs.py")
    py(g, "check-provenance", "tools/check-provenance.py")
    py(g, "check-registers", "tools/check-registers.py")
    py(g, "racetrack arena self-test", "tools/racetrack.py", "--selftest")
    py(g, "no agent running (agent ledger)", "tools/matrix.py", "observe.agents", "check")
    if not quick:
        g = "slower gates"
        add(g, "check-matrix (end to end)", "skip", "it kills and caps real child processes to prove its limits; run in-process it would kill the host, so it needs a real OS")
        py(g, "check-stop-hook", "tools/check-stop-hook.py")
        py(g, "check-doctrine", "tools/check-doctrine.py")
        py(g, "check-statements", "tools/check-statements.py")
    drift = ""
    try:
        src = open(os.path.join(ROOT, "tools/check-all.sh"), encoding="utf-8").read()
        sh = set(re.findall(r'step "([^"]+)"', src))
        if sh != set(_STEP_NAMES):
            drift = "check-all.sh steps differ from this port. Only in script: %s. Only in port: %s." % (
                sorted(sh - set(_STEP_NAMES)), sorted(set(_STEP_NAMES) - sh))
    except OSError as e:
        drift = "could not read tools/check-all.sh to compare: %s" % e
    n = lambda s: sum(1 for x in steps if x["status"] == s)
    return json.dumps({"steps": steps, "passed": n("pass"), "failed": n("fail"), "skipped": n("skip"), "drift": drift})


# ------------------------------------------------------------------ harness hooks, driven by .claude/settings.json
def run_hooks(event, payload_json, matcher_value="", extra_env_json="{}"):
    """Run every hook settings.json registers for `event` whose matcher fits `matcher_value`.

    python3 <script>   runs in-process. A command that ends in .sh runs its Python port from tools/browser/<name>.py
    when there is one; with no port it is reported as status "no_port" (never as passed). Returns a JSON list of
    {command, ran, status, code, stdout, stderr}."""
    results = []
    try:
        cfg = json.load(open(os.path.join(ROOT, ".claude/settings.json"), encoding="utf-8"))
    except (OSError, ValueError) as e:
        return json.dumps([{"command": ".claude/settings.json", "ran": "", "status": "error", "code": 1,
                            "stdout": "", "stderr": "cannot read settings: %s" % e}])
    extra = json.loads(extra_env_json or "{}")
    for grp in (cfg.get("hooks") or {}).get(event, []):
        m = grp.get("matcher")
        if m and not re.fullmatch(m, matcher_value or ""):
            continue
        for h in grp.get("hooks", []):
            if h.get("type") != "command":
                continue
            cmd = h.get("command", "")
            try:
                argv = shlex.split(cmd.replace("$CLAUDE_PROJECT_DIR", ROOT))
            except ValueError as e:
                results.append({"command": cmd, "ran": "", "status": "error", "code": 1, "stdout": "", "stderr": str(e)})
                continue
            if argv and _is_py(argv[0]):
                argv = argv[1:]
            script = argv[0] if argv else ""
            status = "ran"
            if script.endswith(".sh"):
                port = os.path.join(ROOT, "tools/browser", os.path.splitext(os.path.basename(script))[0] + ".py")
                if os.path.isfile(port):
                    script = port
                else:
                    results.append({"command": cmd, "ran": "", "status": "no_port", "code": None, "stdout": "",
                                    "stderr": "no Python port in tools/browser/ for %s" % os.path.basename(script)})
                    continue
            env = dict(os.environ)
            env["CLAUDE_PROJECT_DIR"] = ROOT
            env.update(extra)
            try:
                rc, o, e = _run_py([script] + argv[1:], payload_json, ROOT, env)
            except Exception as ex:
                rc, o, e = 1, "", "%s: %s" % (type(ex).__name__, ex)
                status = "error"
            results.append({"command": cmd, "ran": os.path.relpath(script, ROOT) if script.startswith(ROOT) else script,
                            "status": status, "code": rc, "stdout": o, "stderr": e})
    return json.dumps(results)
