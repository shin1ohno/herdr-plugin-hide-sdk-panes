#!/usr/bin/env python3
"""Tag panes whose foreground process is a Claude remote-control session
(--sdk-url child, or `claude rc` / `claude remote-control`) with the token hide_sdk=1, and install an Agents view that excludes
them. Idempotent; safe to run on every event."""
import json, os, subprocess, sys

SOURCE = "plugin:" + os.environ.get("HERDR_PLUGIN_ID", "shin1ohno.hide-sdk-panes")
BIN = os.environ.get("HERDR_BIN_PATH", "herdr")
TOKEN = "hide_sdk"


def cli(*args):
    out = subprocess.run([BIN, *args], capture_output=True, text=True, timeout=20)
    return json.loads(out.stdout) if out.stdout.strip() else {}


def is_rc_argv(argv):
    """A Claude remote-control session: the SDK child (--sdk-url) or the
    interactive `claude rc` / `claude remote-control` command."""
    if "--sdk-url" in argv:
        return True
    return (len(argv) >= 2 and os.path.basename(argv[0]) == "claude"
            and argv[1] in ("rc", "remote-control"))


def is_sdk(pane_id):
    info = cli("pane", "process-info", "--pane", pane_id)
    procs = info.get("result", {}).get("process_info", {}).get("foreground_processes", [])
    return any(is_rc_argv(p.get("argv", [])) for p in procs)


def rpc(method, params):
    import socket
    path = os.environ["HERDR_SOCKET_PATH"]
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(10)
    s.connect(path)
    s.sendall((json.dumps({"id": "hsp", "method": method, "params": params}) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
    s.close()
    return json.loads(buf.decode() or "{}")


def sweep():
    panes = cli("pane", "list").get("result", {}).get("panes", [])
    for p in panes:
        pid = p["pane_id"]
        hide = is_sdk(pid)
        rpc("pane.report_metadata", {
            "pane_id": pid, "source": SOURCE,
            "tokens": {TOKEN: "1" if hide else None},
            "ttl_ms": 86400000,
        })
    rpc("agent.view.set", {
        "source": SOURCE, "label": "no-sdk",
        "filter": {"op": "not", "filter": {"op": "eq", "field": {"token": TOKEN}, "value": "1"}},
    })


if __name__ == "__main__":
    sweep() if (sys.argv[1:] or ["sweep"])[0] == "sweep" else None
