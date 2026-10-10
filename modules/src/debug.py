# ==========================================================================
# Project Saver Module: Diagnostic System Inspector (debug.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import time
import module_library

MODULE_MANIFEST = {
    "name": "debug",
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.30",
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
    cli_dict, app_version, port_num = module_library.bootstrap_session(cli_dict, app_version, port_num)
    
    while True:
        # 1. Clear terminal screen platform-natively
        module_library.clear_screen_with_trace(MODULE_MANIFEST, __file__)

        # 2. Extract configuration parameter elements out of the section block properties
        log_enabled = module_library.get_setting("debug", "log_to_file", "yes")
        verbose_mode = module_library.get_setting("debug", "verbose_output", "no")
        token_mode = module_library.get_setting("debug", "token", "shared")

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
            f"   Security Token Credentials  : {module_library.get_setting('singlefile', 'token', 'N/A')}",
            "---",
            "GLOBAL SYSTEM_CONFIG DICTIONARY EXTRACTS:"
        ]

        # 4. Safely iterate and print every runtime variable key packed in the registry
        import configparser
        base_path = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        if base_path.lower().endswith("modules"): base_path = os.path.dirname(base_path)
        cfg_path = os.path.join(base_path, "project_saver.cfg")
        
        config = configparser.ConfigParser()
        config_items = []
        if os.path.exists(cfg_path):
            try:
                config.read(cfg_path, encoding="utf-8")
                for section in config.sections():
                    for k, v in config.items(section):
                        config_items.append((f"{section.lower()}_{k.lower()}", v))
            except:
                pass
        config_items = sorted(config_items)
        for idx, (key, val) in enumerate(config_items[:12]):
            truncated_val = str(val)[:45] + "..." if len(str(val)) > 45 else str(val)
            debug_tree.append(f"   [{idx:02d}] {key} = {truncated_val}")
            
        if len(config_items) > 12:
            debug_tree.append(f"   [+] ... and {len(config_items) - 12} other configuration records hidden.")

        debug_tree.append("---")
        debug_tree.append("   [-] Press [Minus Key] to drop back out to Main Menu...")


        # 5. Render the sandboxed overview via your native layout engine
        import project_saver_x
        project_saver_x.render_better_box(
            debug_tree, 
            title_str="Debug Diagnostic Module Context", 
            box_width_override=72
        )

        # 6. Non-blocking keyboard state monitoring
        sys.stdout.write("\x1b[2K\r[Debug] Ready for key: ")
        sys.stdout.flush()

        user_input = module_library.get_keystroke()

        if user_input == "":
            time.sleep(0.05)
            continue
        
        # Check for break condition back to parent daemon frame loop execution
        if user_input == '-':
            print("\n[*] Exiting Debug workspace. Returning to Master Dashboard...")
            break
            
        # Throttles execution frames slightly to protect processor cores from looping
        time.sleep(0.05)

if __name__ == "__main__":
    module_library.run_standalone_safely(MODULE_MANIFEST, execute_interactive_menu)
