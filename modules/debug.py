# ==========================================================================
# Project Saver Module: Diagnostic System Inspector (debug.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import time

# ─── MODULE SYSTEM MANIFEST REGISTRY ───
# Read dynamically by the parent daemon engine during the startup boot pass
MODULE_MANIFEST = {
    "name": "debug",
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.7",
        "requires": "v0.0.76",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True          # Sets availability for cloud installation/use
    },
    "display_name": "Diagnostic System Inspector",
    "menu_shortcut": "d",          # Direct hotkey trigger from the master dashboard menu
    "autostart": False,            # Manually loaded via workspace hotkey selections
    "defaults": {
        "token": "shared",         # Token profile strategy: shared, single, or ask
        "log_to_file": "yes",
        "verbose_output": "no"
    }
}

def register_module_callbacks(server_reference=None):
    """
    Executed on boot if autostart is True.
    Allows pluggable extensions to hook into server traffic pipelines.
    """
    pass

def execute_interactive_menu(cli_dict, app_version, port_num):
    """
    Fired instantly when the user hits 'M' -> selects 'debug', 
    or strikes the direct shortcut key 'D' inside the main menu.
    """
    import project_saver_config
    import project_saver_ui

    while True:
        # 1. Clear terminal screen platform-natively
        os.system('cls' if os.name == 'nt' else 'clear')

        # 2. Extract configuration parameter elements out of the section block properties
        log_enabled = project_saver_config.SYSTEM_CONFIG.get("debug_log_to_file", "yes")
        verbose_mode = project_saver_config.SYSTEM_CONFIG.get("debug_verbose_output", "no")
        token_mode = project_saver_config.SYSTEM_CONFIG.get("debug_token", "shared")

        # 3. Build diagnostic layout text matrix array
        debug_tree = [
            f"   Active Module Name:  {MODULE_MANIFEST['display_name']}",
            f"   Module Author:       {MODULE_MANIFEST['meta']['author']} ({MODULE_MANIFEST['meta']['version']})",
            f"   Token Profile Mode:  {token_mode.upper()}",
            f"   Config Log to File:  {log_enabled.upper()} | Verbose Matrix: {verbose_mode.upper()}",
            "---",
            "📊 LIVE SYSTEM PARAMETERS LOOKUP TREE:",
            f"   Active Application Version : {app_version}",
            f"   Core Daemon Server Port     : {port_num}",
            f"   Security Token Credentials  : {project_saver_config.EXPECTED_TOKEN}",
            "---",
            "⚙️ GLOBAL SYSTEM_CONFIG DICTIONARY EXTRACTS:"
        ]

        # 4. Safely iterate and print every runtime variable key packed in the registry
        for idx, (key, val) in enumerate(sorted(project_saver_config.SYSTEM_CONFIG.items())):
            # Formats long entries cleanly so they don't wrap and break frame boundaries
            truncated_val = str(val)[:45] + "..." if len(str(val)) > 45 else str(val)
            debug_tree.append(f"   [{idx:02d}] {key} = {truncated_val}")

        debug_tree.append("---")
        debug_tree.append("   [-] Press [Minus Key] to drop back out to Main Menu...")

        # 5. Render the sandboxed overview via your native layout engine
        project_saver_ui.render_better_box(
            debug_tree, 
            title_str=f"Debug Diagnostic Module Context", 
            box_width_override=72
        )

        # 6. Non-blocking keyboard state monitoring
        sys.stdout.write("\x1b[2K\r[🔍 Debug] Ready for key: ")
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

        if user_input == "":
            time.sleep(0.05)
            continue
        
        # Check for break condition back to parent daemon frame loop execution
        if user_input == '-':
            print("\n[*] Exiting Debug workspace. Returning to Master Dashboard...")
            break
        else:
            time.sleep(0.2)
            
        # Throttles execution frames slightly to protect processor cores from looping
        time.sleep(0.05)
