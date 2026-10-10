# ==========================================================================
# Project Saver Shared Module Utilities (module_utils.py)
# Copyright by Gunther Voet
# ==========================================================================
import os
import sys
import json

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
        
    current_path = sys.executable if getattr(sys, 'frozen', False) else caller_file
    meta = manifest.get("meta", {})
    print(f"[MODULE]: {manifest.get('display_name', 'Unknown')} ({meta.get('version', 'v0.0.1')}) by {meta.get('author', 'Gunther Voet')}")
    print(f"[PATH]: {os.path.abspath(current_path)}\n")

def get_setting(module_name, key, default_value=""):
    """Safely extracts live config parameters out of master configuration memory frames."""
    try:
        import project_saver_config
        lookup_key = f"{module_name.lower()}_{key.lower()}"
        return project_saver_config.SYSTEM_CONFIG.get(lookup_key, default_value)
    except:
        return default_value

def run_standalone_safely(manifest, menu_callback):
    """
    Natively parses terminal input vectors for custom configuration profile paths,
    bootstraps target profile states, and drops control straight into the module loop.
    """
    import os
    import sys
    
    print("\n[+] Module started.")
    
    try:
        import project_saver_config
        
        # 1. Parse command-line input vector slices for custom config paths
        temp_args = sys.argv[1:]
        active_cfg_profile = "project_saver.cfg"
        
        if "--config" in temp_args:
            try:
                c_idx = temp_args.index("--config")
                if c_idx + 1 < len(temp_args):
                    active_cfg_profile = temp_args[c_idx + 1]
            except:
                pass
                
        # 2. Reconstruct absolute path layers if input profile matches absolute or relative targets
        if not os.path.isabs(active_cfg_profile):
            bbase_path = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]))
            cfg_path = os.path.join(base_path, active_cfg_profile)
            
            # Safe boundary tracking check fallback if binary file is nested in subfolders
            if not os.path.exists(cfg_path) and base_path.lower().endswith("modules"):
                cfg_path = os.path.join(os.path.dirname(base_path), active_cfg_profile)
        else:
            cfg_path = active_cfg_profile
            
        # 3. Secure and mount the verified configuration tables straight into runtime memory
        if os.path.exists(cfg_path):
            project_saver_config.load_config_file(cfg_path)
    except:
        pass

    # 4. Map dictionary fallbacks exactly matching module layout boundaries
    fallback_cli = {}
    if manifest.get("name") == "archiver":
        fallback_cli = {"export_folder": "", "export_format": "markdown", "export_type": "auto"}
        
    run_version = manifest.get("meta", {}).get("version", "v0.0.1")
    menu_callback(cli_dict=fallback_cli, app_version=run_version, port_num=19763)
    sys.exit(0)
