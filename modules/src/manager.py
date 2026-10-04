# ==========================================================================
# Project Saver Module: Pluggable Module & Package Manager (manager.py)
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import time
import json
import urllib.request
import importlib.util

# ─── MODULE SYSTEM MANIFEST REGISTRY ───
MODULE_MANIFEST = {
    "name": "manager",
    "display_name": "Module Manager",
    "display_menu": "[M]odules Manager",
    "menu_shortcut": "m",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.76",
        "requires": "v0.0.79",     # Minimal version required of the core engine
        "enabled": True,           # Hard toggle to switch the module on/off
        "available": True          # Sets availability for cloud installation/use
    },
    "autostart": False,            # Loaded manually via hotkey actions
    "defaults": {
        "target_repository": "gowildchild/Project-Saver",
        "target_branch": "modules" 
    }
}

def register_module_callbacks(server_reference=None):
    """Executed automatically on boot if autostart is True."""
    pass

def install_module_from_cloud(module_name, github_repo):
    """Stream-downloads raw code text directly from the target GitHub modules subfolder branch."""
    import project_saver_config
    
    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    target_path = os.path.join(script_base_dir, "modules", f"{module_name.lower()}.py")
    
    target_branch = project_saver_config.SYSTEM_CONFIG.get("manager_target_branch", "modules")
    
    raw_url = f"https://raw.githubusercontent.com/{github_repo}/{target_branch}/modules/{module_name.lower()}.py"
    print(f"\n[*] Connecting to distribution repository: {raw_url}")
    
    try:
        req = urllib.request.Request(raw_url, headers={'User-Agent': 'Project-Saver-Package-Manager'})
        with urllib.request.urlopen(req, timeout=5) as response:
            code_payload = response.read()
            
        with open(target_path, "wb") as f:
            f.write(code_payload)
        return True
    except Exception as e:
        print(f"🔴 FAILED: Cloud package installer routine failed to fetch module: {e}")
        time.sleep(2)
        return False

def execute_interactive_menu(cli_dict, app_version, port_num):
    """
    Fired instantly when the user hits 'M' inside the master dashboard menu views.
    Completely isolates package installations, parameter configuration, and uninstalls.
    """
    import project_saver_config
    import project_saver_ui

    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    modules_dir = os.path.join(script_base_dir, "modules")
    status_message = "Module Extension Manager Engine stabilized. Ready for commands."

    while True:
        # 1. Clear terminal screen platform-natively
        os.system('cls' if os.name == 'nt' else 'clear')

        # 2. Extract repository configuration parameters safely
        target_repo = project_saver_config.SYSTEM_CONFIG.get("manager_target_repository", "gowildchild/Project-Saver")
        target_branch = project_saver_config.SYSTEM_CONFIG.get("manager_target_branch", "modules")

        # 3. Dynamic Local Directory File Scanning Sweep Loop Pass
        installed_extensions = []
        if os.path.exists(modules_dir):
            for file_entry in os.listdir(modules_dir):
                # * [FIXED] EXPAND DISCOVERY PATTERNS TO CAPTURE SCRIPTS AND COMPILED BINARIES NATIVELY
                is_script = file_entry.endswith(".py") and file_entry != "__init__.py"
                is_binary = file_entry.endswith(".exe") or (os.name != 'nt' and '.' not in file_entry and file_entry != "__init__.py")
                
                if is_script or is_binary:
                    mod_name, _ = os.path.splitext(file_entry)
                    if mod_name.lower() not in installed_extensions:
                        installed_extensions.append(mod_name.lower())

        # 4. Build terminal manager control panel box UI display list
        manager_panel = [
            f" Active Module Name:  {MODULE_MANIFEST['display_name']}",
            f" Target Repository :  https://github.com/{target_repo}",
            f" Distribution Branch:  {target_branch.upper()}",
            "---",
            "📦 INSTALLED LOCAL MODULES:",
            f"   {', '.join(sorted(installed_extensions)) if installed_extensions else '(No external extensions found)'}",
            "---",
            "🛠️ OPERATIONS HANDLERS:",
            "   [I] Install    - Stream-download a fresh pluggable module from GitHub.",
            "   [U] Uninstall  - Erase a module extension file and unload its variables.",
            "   [C] Configure  - Modify operational parameter values inside project_saver.cfg.",
            "---",
            f" Status Indicator:    {status_message}",
            "---",
            " [-] Press [Minus Key] to drop back out to Main Menu..."
        ]

        # 5. Render via your native box utility layout engine
        project_saver_ui.render_better_box(
            manager_panel,
            title_str="Module Manager",
            box_width_override=74
        )

        # 6. Non-blocking keyboard state monitoring
        sys.stdout.write("\x1b[2K\r[ Manager] Ready for key: ")
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

        # Reset structural configuration tracking strings on loop turn
        status_message = "Awaiting input command option..."

        # HOTKEY MATRIX ACTIONS
        if user_input == '-':
            print("\n[*] Exiting Module Manager. Returning to  Dashboard...")
            break

        elif user_input == 'i':
            print("\n")
            target_name = input("[*] Enter name of the target module to pull from GitHub: ").strip().lower()
            if target_name:
                status_message = f"[*] Stream-fetching module '{target_name}'..."
                if install_module_from_cloud(target_name, target_repo):
                    status_message = f"🟢 SUCCESS: Module '{target_name}' hot-loaded into local directory registry safely!"
                    # * [FIXED] ROUTE TO CORRECT RUNTIME ENGINE REGISTRY IDENTIFIER FOR DYNAMIC HOT LOADING
                    main_module_ref = sys.modules.get('__main__')
                    if main_module_ref and hasattr(main_module_ref, 'project_saver_modules'):
                        main_module_ref.project_saver_modules.bootstrap_and_discover_modules(cli_dict, app_version, port_num)
                else:
                    status_message = f"🔴 FAILED: Could not pull module '{target_name}' over the wire."
            else:
                status_message = "⚠️ WARNING: Aborted. Module target entry field string was empty."

        elif user_input == 'u':
            print("\n")
            target_name = input("[*] Enter name of local module script to physically erase: ").strip().lower()
            target_file_py = os.path.join(modules_dir, f"{target_name}.py")
            target_file_exe = os.path.join(modules_dir, f"{target_name}.exe")
            
            if (os.path.exists(target_file_py) or os.path.exists(target_file_exe)) and target_name != "manager":
                try:
                    if os.path.exists(target_file_py): os.remove(target_file_py)
                    if os.path.exists(target_file_exe): os.remove(target_file_exe)
                    status_message = f"🟢 SUCCESS: Pluggable file '{target_name}' erased from disk storage context."
                    # * [FIXED] ROUTE TO CORRECT RUNTIME ENGINE REGISTRY IDENTIFIER FOR DYNAMIC SWEEP ALIGNMENTS
                    main_module_ref = sys.modules.get('__main__')
                    if main_module_ref and hasattr(main_module_ref, 'project_saver_modules'):
                        main_module_ref.project_saver_modules.bootstrap_and_discover_modules(cli_dict, app_version, port_num)
                except Exception as err:
                    status_message = f"🔴 ERROR: Failed to sweep target off disk -> {err}"
            else:
                status_message = "🔴 ERROR: Target module does not exist, or is locked by system core configurations."


        elif user_input == 'c':
            print("\n")
            target_name = input("[*] Enter module name section header to configure: ").strip().lower()
            if target_name in installed_extensions or target_name == "manager":
                print(f"\n[+] Active configuration keys for [{target_name}]:")
                prefix = f"{target_name}_"
                matching_keys = [k for k in project_saver_config.SYSTEM_CONFIG.keys() if k.startswith(prefix)]
                
                if matching_keys:
                    for k in matching_keys:
                        clean_key = k[len(prefix):]
                        current_val = project_saver_config.SYSTEM_CONFIG[k]
                        print(f" -> {clean_key} (Current: {current_val})")
                    
                    target_key = input("\nEnter specific parameter key row name to change: ").strip().lower()
                    full_lookup_key = f"{prefix}{target_key}"
                    
                    if full_lookup_key in project_saver_config.SYSTEM_CONFIG:
                        new_val = input(f"Enter new value for [{target_key}]: ").strip()
                        if new_val:
                            project_saver_config.SYSTEM_CONFIG[full_lookup_key] = new_val
                            status_message = f"🟢 SUCCESS: Parameter variable [{target_key}] updated in memory arrays."
                            # * [FIXED] PASSED VALID MASTER NAMESPACE OBJECT REFERENCES TO PREVENT ATTRIBUTE LOOKUP ERRS
                            main_module_ref = sys.modules.get('__main__')
                            parent_args = getattr(main_module_ref, 'CLI_ARGS', cli_dict)
                            project_saver_config.save_config_file("project_saver.cfg", parent_args, app_version)
                        else:
                            status_message = "⚠️ WARNING: Configuration change skipped. Input parameter empty."
                    else:
                        status_message = "🔴 ERROR: Specified variable target parameter row name key invalid."
                else:
                    status_message = f"⚠️ WARNING: No active defaults initialized for section block [{target_name}]."
            else:
                status_message = "🔴 ERROR: Target module selection not verified inside active local libraries."

        time.sleep(0.05)
