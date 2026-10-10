# ==========================================================================
# Project Saver Shared Module Utilities (module_utils.py)
# ==========================================================================
import os
import sys

def get_keystroke():
    """Shared single-character blocking input loop pass for Windows and Linux."""
    if os.name == 'nt':
        import msvcrt
        return msvcrt.getch().decode('utf-8', errors='ignore').lower()
    else:
        import select
        import sys
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if not ready:
            return ""
        return sys.stdin.readline().strip().lower()

def bootstrap_session(default_cli, default_ver, default_port):
    """Recovers live parent configurations from subprocess argument arrays automatically."""
    if getattr(sys, 'frozen', False) and len(sys.argv) > 3:
        try:
            return json.loads(sys.argv[1]), sys.argv[2], int(sys.argv[3])
        except:
            pass
    return default_cli, default_ver, default_port

def load_disk_registry(modules_dir):
    """Parses manifest.json fields securely when isolated from parent memory allocations."""
    ledger_path = os.path.join(modules_dir, "manifest.json")
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, "r", encoding="utf-8") as lf:
                raw_json = json.load(lf)
                if "modules" in raw_json:
                    return raw_json.get("modules", {})
                return raw_json.get("platforms", {}).get("windows", {})
        except:
            pass
    return {}

def force_foreground():
    """Enforces active terminal shell window focus to pull panels to the front row."""
    try:
        if os.name == 'nt':
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        elif sys.platform == 'darwin':
            os.system("osascript -e 'tell application \"Terminal\" to activate'")
    except:
        pass
