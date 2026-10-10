# ==========================================================================
# Project Saver Shared Module Utilities (module_utils.py)
# Copyright by Gunther Voet
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

def clear_screen_with_trace(manifest):
    """Clears terminal natively and prints standardized loading path trace data."""
    import os
    import sys
    os.system('cls' if os.name == 'nt' else 'clear')
    if getattr(sys, 'frozen', False):
        current_path = sys.executable
    else:
        current_path = execution_context_file
    current_path = sys.executable if getattr(sys, 'frozen', False) else __file__
    print(f"[MODULE]: {manifest.get('display_name', 'Unknown')} ({meta_dict.get('version', 'v0.0.1')}) by {meta_dict.get('author', 'Gunther Voet')}")
    print(f"[PATH]: {os.path.abspath(current_path)}\n")

def get_setting(module_name, key, default_value=""):
    """Safely extracts live config parameters out of master configuration memory frames."""
    try:
        import project_saver_config
        lookup_key = f"{module_name.lower()}_{key.lower()}"
        return project_saver_config.SYSTEM_CONFIG.get(lookup_key, default_value)
    except:
        return default_value
