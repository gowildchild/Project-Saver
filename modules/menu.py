# ==========================================================================
# Project Saver Module: Customisable Multi-Layer Menu Navigator (menu.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import time

# ─── MODULE SYSTEM MANIFEST REGISTRY ───
MODULE_MANIFEST = {
    "name": "menu",
    "display_name": "Custom Menu Navigator",
    "display_menu": "[X] Custom Menu",
    "menu_shortcut": "x",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.1",
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
    import project_saver_config
    import project_saver_ui

    # Access the active loaded modules repository tree from the parent application state
    # (Simulated tracking mapping data fallback for isolated execution testing)
    detected_modules_pool = getattr(sys.modules['__main__'], 'ACTIVE_MODULES', {
        "shutdown": "h",
        "debug": "d",
        "custom": "c",
        "archiver": "a"
    })

    current_category = project_saver_config.SYSTEM_CONFIG.get("menu_default_active_category", "utilities")

    while True:
        # 1. Clear terminal screen platform-natively
        os.system('cls' if os.name == 'nt' else 'clear')

        # 2. Build the customisable multi-layered sub-menu dashboard rows
        navigator_panel = [
            f"   Active Module Name:  {MODULE_MANIFEST['display_name']}",
            f"   Active Category   :  {current_category.upper()}",
            "---",
            "🗂️ MULTI-LAYER ROUTING GROUPS:",
            "   [1] Power Utilities   | [2] System Diagnostics | [3] Extension Assets",
            "---",
            "🔌 DYNAMICALLY PLUGGED COMPATIBLE MODULES:"
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
        sys.stdout.write("\x1b[2K\r[🗂️ Navigator] Ready for key: ")
        sys.stdout.flush()

        user_input = ""
        if os.name == 'nt':
            import msvcrt
            if msvcrt.kbhit():
                user_input = msvcrt.getch().decode('utf-8', errors='ignore').lower()
            else:
                time.sleep(0.05)
                continue
        else:
            import select
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not ready:
                continue
            user_input = sys.stdin.readline().strip().lower()

        # ─── PROCESS LOCALIZED INTERACTIVE INPUTS ───
        if user_input == '-':
            break
        elif user_input == '1':
            current_category = "utilities"
        elif user_input == '2':
            current_category = "diagnostics"
        elif user_input == '3':
            current_category = "extensions"
            
        # If the user hits a hotkey corresponding to an active module, we pass execution downstream
        elif user_input in detected_modules_pool.values():
            print(f"\n[*] Route shortcut target captured! Redirecting path execution to module...")
            # Interactive redirection logic will hook cleanly inside your parent loop block
            time.sleep(0.5)

        time.sleep(0.05)
