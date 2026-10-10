# ==========================================================================
# Project Saver Module: Customisable Multi-Layer Menu Navigator (menu.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved. 
# ==========================================================================
import os
import sys
import time
import module_library

# ─── MODULE SYSTEM MANIFEST REGISTRY ───
MODULE_MANIFEST = {
    "name": "menu",
    "display_name": "Custom Menu Navigator",
    "display_menu": "[X] Custom Menu",
    "menu_shortcut": "x",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.28",
        "requires": "v0.0.79",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True          # Sets availability for cloud installation/use
    },
    "autostart": False,            # Loaded manually via hotkey actions
    "defaults": {
        "default_active_category": "utilities",
        "render_style": "compact"
    }
}

def register_module_callbacks(server_reference=None):
    """Executed automatically on boot if autostart is True."""
    pass

def execute_interactive_menu(cli_dict, app_version, port_num):
    """
    Fired instantly when the user hits 'M' -> selects 'menu',
    or strikes the direct shortcut hotkey 'X' inside the master dashboard view.
    """
    import project_saver_ui
    import project_saver_modules
    import json

    cli_dict, app_version, port_num = module_library.bootstrap_session(cli_dict, app_version, port_num)
    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    if getattr(sys, 'frozen', False) or script_base_dir.lower().endswith("modules"):
        modules_dir = script_base_dir
    else:
        modules_dir = os.path.join(script_base_dir, "modules")

    active_registry = getattr(project_saver_modules, 'ACTIVE_MODULES', {})
    if not active_registry:
        active_registry = module_library.load_disk_registry(modules_dir)
    detected_modules_pool = {}
    for active_name, entry in active_registry.items():
        if isinstance(entry, dict):
            shortcut_key = entry.get("menu_shortcut", "").lower()
        else:
            mod_obj = entry["mock"] if hasattr(entry, "get") and entry.get("type") == "binary" else entry
            manifest_ref = getattr(mod_obj, "MODULE_MANIFEST", {})
            shortcut_key = manifest_ref.get("menu_shortcut", "").lower()
        if shortcut_key:
            detected_modules_pool[active_name] = shortcut_key

    current_category = module_library.get_setting("menu", "default_active_category", "utilities")

    while True:
        module_library.clear_screen_with_trace(MODULE_MANIFEST, __file__)

        # 2. Build the customisable multi-layered sub-menu dashboard rows
        navigator_panel = [
            f"   Active Module Name:  {MODULE_MANIFEST['display_name']}",
            f"   Active Category   :  {current_category.upper()}",
            "---",
            "   MULTI-LAYER ROUTING GROUPS:",
            "   [1] Power Utilities   | [2] System Diagnostics | [3] Extension Assets",
            "---",
            "   DYNAMICALLY PLUGGED COMPATIBLE MODULES:"
        ]

        # 3. Read out and display active extensions matching the categorized paths gracefully
        has_items = False
        for mod_name, hotkey in detected_modules_pool.items():
            if current_category == "utilities" and mod_name in ["shutdown"]:
                navigator_panel.append(f"   -> Press [{hotkey.upper()}] : Launch pluggable System Power Controller module.")
                has_items = True
            elif current_category == "diagnostics" and mod_name in ["debug"]:
                navigator_panel.append(f"   -> Press [{hotkey.upper()}] : Open local Diagnostic System Inspector tree.")
                has_items = True
            elif current_category == "extensions" and mod_name in ["custom", "archiver"]:
                navigator_panel.append(f"   -> Press [{hotkey.upper()}] : Step into pluggable '{mod_name}' module frame.")
                has_items = True

        if not has_items:
            navigator_panel.append("   (No active, enabled modules registered under this sub-category row.)")

        navigator_panel.append("---")
        navigator_panel.append("   [-] Press [Minus Key] to drop back out to Main Menu...")

        # 4. Render via your native box utility layout engine
        project_saver_ui.render_better_box(
            navigator_panel, 
            title_str=f"Navigation Grid Controller Engine", 
            box_width_override=74
        )

        # 5. Non-blocking keyboard state monitoring
        sys.stdout.write("\x1b[2K\r[Navigator] Ready for key: ")
        sys.stdout.flush()

        user_input = module_library.get_keystroke()
        if user_input == '-':
            break
        elif user_input == '1':
            current_category = "utilities"
        elif user_input == '2':
            current_category = "diagnostics"
        elif user_input == '3':
            current_category = "extensions"
            
        elif user_input in detected_modules_pool.values():
            # Identify which module matches the user's pressed shortcut hotkey
            target_module_key = None
            for mod_name, shortcut_char in detected_modules_pool.items():
                if shortcut_char == user_input:
                    target_module_key = mod_name
                    break
            
            if target_module_key:
                mod_obj = project_saver_modules.ACTIVE_MODULES.get(target_module_key)
                
                # * [FIXED] REDIRECT COMPILED EXTENSION TARGETS THROUGH NATIVE OS SUB-PROCESS HOOKS
                if isinstance(mod_obj, dict) and mod_obj.get("type") == "binary":
                    import subprocess
                    try:
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(f"[*] Sub-process offload: Executing standalone binary -> {target_module_key.upper()}")
                        subprocess.run([mod_obj["path"]], check=True)
                    except Exception as bin_err:
                        print(f"\n[-] Standalone extension binary execution crashed: {bin_err}")
                        time.sleep(2)
                
                # ─── FALLBACK MATRIX FOR SCRIPT MODULE OBJECT REFLECTIONS ───
                elif mod_obj and hasattr(mod_obj, "execute_interactive_menu"):
                    print(f"\n[*] Route shortcut target captured! Redirecting path execution to module: {target_module_key.upper()}")
                    time.sleep(0.3)
                    try:
                        mod_obj.execute_interactive_menu(cli_dict, app_version, port_num)
                    except Exception as e:
                        print(f"\n[-] Execution blew up inside nested sub-module [{target_module_key}]: {e}")
                        time.sleep(2)

        time.sleep(0.05)

if __name__ == "__main__":
    module_library.run_standalone_safely(MODULE_MANIFEST, execute_interactive_menu)
