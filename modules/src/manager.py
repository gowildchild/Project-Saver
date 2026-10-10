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
import module_library

# ─── MODULE SYSTEM MANIFEST REGISTRY ───
MODULE_MANIFEST = {
    "name": "manager",
    "display_name": "Module Manager",
    "display_menu": "[M]odules Manager",
    "menu_shortcut": "m",          # Direct hotkey trigger from the master dashboard menu
    "meta": {
        "author": "Gunther Voet",
        "version": "v0.0.26",
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
    cli_dict, app_version, port_num = module_library.bootstrap_session(cli_dict, app_version, port_num)
    
    if getattr(sys, 'frozen', False) or script_base_dir.lower().endswith("modules"):
        modules_dir = script_base_dir
    else:
        modules_dir = os.path.join(script_base_dir, "modules")

    main_module_ref = sys.modules.get('__main__')
    modules_framework = sys.modules.get('project_saver_modules')
    active_registry = getattr(modules_framework, 'ACTIVE_MODULES', {}) if modules_framework else {}
    using_manifest_fallback = False
    if not active_registry:
        active_registry = module_library.load_disk_registry(modules_dir)
        if active_registry:
            using_manifest_fallback = True
    status_message = "Module Manager Loaded, ready for commands."

    while True:
        module_library.clear_screen_with_trace(MODULE_MANIFEST, __file__)
        target_repo = module_library.get_setting("manager", "target_repository", "gowildchild/Project-Saver")
        target_branch = module_library.get_setting("manager", "target_branch", "modules")
        installed_extensions = []
        if os.path.exists(modules_dir):
            for file_entry in os.listdir(modules_dir):
                is_script = file_entry.endswith(".py") and file_entry != "__init__.py"
                is_binary = file_entry.endswith(".exe") or (os.name != 'nt' and '.' not in file_entry and file_entry != "__init__.py")
                
                if is_script or is_binary:
                    mod_name, _ = os.path.splitext(file_entry)
                    if mod_name.lower() not in installed_extensions:
                        installed_extensions.append(mod_name.lower())

        memory_breakdown_lines = []
        total_allocated_bytes = 0

        for name, mod_ref in active_registry.items():
            if using_manifest_fallback:
                target_filename = mod_ref.get("binary_filename", f"{name}.exe" if os.name == 'nt' else name)
                target_file_path = os.path.join(modules_dir, target_filename)
                if not os.path.exists(target_file_path) and os.name == 'nt' and not target_filename.endswith(".exe"):
                    target_file_path = os.path.join(modules_dir, f"{target_filename}.py")
                if os.path.exists(target_file_path):
                    mod_size = os.path.getsize(target_file_path)
                else:
                    mod_size = sys.getsizeof(str(mod_ref))
                total_allocated_bytes += mod_size
                memory_breakdown_lines.append(f"   -> [{name.upper()}] Disk Weight: {mod_size} bytes")
            else:
                mod_size = sys.getsizeof(mod_ref)
                total_allocated_bytes += mod_size
                memory_breakdown_lines.append(f"   -> [{name.upper()}] RAM Weight: {mod_size} bytes")

        
        manager_panel = [
            f" Active Module Name:  {MODULE_MANIFEST['display_name']}",
            f" Target Repository :  https://github.com/{target_repo}",
            f" Distribution Branch:  {target_branch.upper()}",
            "---",
            "📦 INSTALLED LOCAL MODULES:",
            f"   {', '.join(sorted(installed_extensions)) if installed_extensions else '(No external extensions found)'}",
            "---",
            "🧠 LIVE MEMORY METRICS:",
            f"   Total Loaded Cache Size: {total_allocated_bytes} bytes"
        ]

        manager_panel.extend(memory_breakdown_lines)

        manager_panel.extend([
            "---",
            "🛠 MODULE MANAGER:",
            "   [I] Install    - Stream-download a fresh pluggable module from GitHub.",
            "   [U] Uninstall  - Erase a module extension file and unload its variables.",
            "   [C] Configure  - Modify operational parameter values inside project_saver.cfg.",
            "---",
            f" Status Indicator:    {status_message}",
            "---",
            " [-] Press [Minus Key] to drop back out to Main Menu..."
        ])

        project_saver_ui.render_better_box(
            manager_panel,
            title_str="Module Manager",
            box_width_override=74
        )

        sys.stdout.write("\x1b[2K\r[Manager] Ready for key: ")
        sys.stdout.flush()

        user_input = module_library.get_keystroke()
        if user_input == "":
            time.sleep(0.05)
            continue

        status_message = "Awaiting input command option..."

        if user_input == '-':
            print("\n[*] Exiting Module Manager. Returning to Dashboard...")
            break

        elif user_input == 'i':
            print("\n")
            target_name = input("[*] Enter name of the target module to pull from GitHub: ").strip().lower()
            if target_name:
                status_message = f"[*] Stream-fetching module '{target_name}'..."
                if install_module_from_cloud(target_name, target_repo):
                    status_message = f"🟢 SUCCESS: Module '{target_name}' hot-loaded into local directory registry safely!"
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
                            main_module_ref = sys.modules.get('__main__')
                            parent_args = getattr(main_module_ref, 'CLI_ARGS', None) or cli_dict
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

    if "project_saver_config" in sys.modules or os.path.exists("project_saver.cfg"):
        import project_saver_config
        import project_saver_modules
        
        base_path = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        cfg_profile = os.path.join(base_path, "project_saver.cfg")
        if not os.path.exists(cfg_profile) and base_path.lower().endswith("modules"):
            cfg_profile = os.path.join(os.path.dirname(base_path), "project_saver.cfg")
            
        if os.path.exists(cfg_profile):
            project_saver_config.load_config_file(cfg_profile)
            
        fallback_cli = {}
        run_version = MODULE_MANIFEST.get("meta", {}).get("version", "v0.0.1")
        
        project_saver_modules.bootstrap_and_discover_modules(fallback_cli, run_version, 19763)
        execute_interactive_menu(fallback_cli, run_version, 19763)
    else:
        print("\n[!] Module called from Project Saver...")
