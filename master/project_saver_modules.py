# ==========================================================================
# Project Saver Engine: Pluggable Module Registry
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import json
import time
import importlib.util

ACTIVE_MODULES = {}
SHORTCUT_MAP = {}

def bootstrap_and_discover_modules(cli_dict, app_version, port_num, server_ref=None):
    """
    Scans the local modules/ directory, parses manifests, injects defaults
    into config structures, and initializes autostart hooks natively.
    """
    global ACTIVE_MODULES, SHORTCUT_MAP
    ACTIVE_MODULES.clear()
    SHORTCUT_MAP.clear()

    import project_saver_config
    
    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    modules_dir = os.path.join(script_base_dir, "modules")
    
    if not os.path.exists(modules_dir):
        try:
            os.makedirs(modules_dir, exist_ok=True)
            with open(os.path.join(modules_dir, "__init__.py"), "w") as f: f.write("")
        except:
            return

    # Add modules directory context to python search paths dynamically
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)

    for file_entry in os.listdir(modules_dir):
        is_script = file_entry.endswith(".py") and file_entry != "__init__.py"
        is_binary = file_entry.endswith(".exe") or (os.name != 'nt' and '.' not in file_entry and file_entry != "__init__.py")
        if is_script or is_binary:
            module_name, _ = os.path.splitext(file_entry)
            if module_name.lower().startswith("unins00"):
                continue
            module_path = os.path.join(modules_dir, file_entry)
            try:

                if is_script:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    
                    if hasattr(mod, "MODULE_MANIFEST"):
                        manifest = mod.MODULE_MANIFEST
                        meta = manifest.get("meta", {})
                        if not meta.get("enabled", True) or not meta.get("available", True): continue
                        
                        defaults = manifest.get("defaults", {})
                        for def_key, def_val in defaults.items():
                            cfg_key = f"{module_name.lower()}_{def_key.lower()}"
                            if cfg_key not in project_saver_config.SYSTEM_CONFIG:
                                project_saver_config.SYSTEM_CONFIG[cfg_key] = str(def_val)

                        if "display_menu" not in manifest:
                            manifest["display_menu"] = f"   [{manifest.get('menu_shortcut', 'X').upper()}] {module_name.capitalize()}"
                        if "display_desc" not in manifest:
                            manifest["display_desc"] = manifest.get("display_desc", "")
 
                        module_key = str(manifest["name"]).lower()
                        ACTIVE_MODULES[module_key] = {
                            "type": "script",
                            "instance": mod,
                            "MODULE_MANIFEST": manifest
                        }
                        
                        shortcut = manifest.get("menu_shortcut", "").lower()
                        if shortcut: 
                            SHORTCUT_MAP[shortcut] = module_key
                            
                        if manifest.get("autostart", False) and hasattr(mod, "register_module_callbacks"):
                            mod.register_module_callbacks(server_ref)                        

                elif is_binary:
                    ledger_path = os.path.join(modules_dir, "manifest.json")
                    manifest_data = {}                  
                    if os.path.exists(ledger_path):
                        try:
                            with open(ledger_path, "r", encoding="utf-8") as lf:
                                raw_json = json.load(lf)
                                manifest_data = raw_json.get("modules", {}).get(module_name.lower(), {})
                        except Exception as json_err:
                            print(f"JSON Parsing Fatal Exception: {json_err}")
                    else:
                        print(f"CRITICAL: File skipped because os.path.not-exists.")

                    display_name = manifest_data.get("display_name") or f"{module_name.capitalize()} Binary Module"
                    shortcut = manifest_data.get("menu_shortcut") or (module_name.lower() if module_name else "x")
                    author_val = manifest_data.get("author") or "Gunther Voet"
                    version_val = manifest_data.get("version") or "v0.0.1"
                    autostart_val = manifest_data.get("autostart", False)
                    
                    class MockBinaryModule:
                        MODULE_MANIFEST = {
                            "name": module_name.lower(),
                            "display_name": display_name,
                            "display_menu": manifest_data.get("display_menu") or f"[{shortcut.upper()}] {module_name.capitalize()}",
                            "display_desc": manifest_data.get("display_desc") or "",
                            "menu_shortcut": shortcut,
                            "autostart": autostart_val,
                            "display_multi": manifest_data.get("display_multi", []),
                            "defaults": manifest_data.get("defaults", {}),
                            "meta": {
                                "author": author_val,
                                "version": version_val,
                                "enabled": True,
                                "menu": int(manifest_data.get("menu", 3))
                            }
                        }
                    
                    binary_key = module_name.lower()
                    ACTIVE_MODULES[binary_key] = {
                        "type": "binary",
                        "path": module_path,
                        "MODULE_MANIFEST": MockBinaryModule.MODULE_MANIFEST
                    }
                    SHORTCUT_MAP[shortcut.lower()] = binary_key
            except Exception as e:
                print(f"[-] Failed to index module [{module_name}]: {e}")


def route_interactive_shortcut(hotkey_char, cli_dict, app_version, port_num):
    """
    Checks if a key matches an active module shortcut.
    If true, instantly passes complete console thread control to that module.
    """
    target_module_name = SHORTCUT_MAP.get(str(hotkey_char).lower())
    if target_module_name and target_module_name in ACTIVE_MODULES:
        module_object = ACTIVE_MODULES[target_module_name]
        if isinstance(module_object, dict) and module_object.get("type") == "binary":
            import subprocess
            try:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"[*] Executing MODULE binary -> {target_module_name.upper()}")
                # Launch binary cleanly and block parent thread execution until sub-process exits cleanly
                subprocess.run([module_object["path"]], check=True)
                return True
            except Exception as bin_err:
                print(f"\n[-] Standalone MODULE crashed: {bin_err}")
                time.sleep(2)
                return True
        
        elif isinstance(module_object, dict) and module_object.get("type") == "script":
            mod_inst = module_object.get("instance")
            if mod_inst and hasattr(mod_inst, "execute_interactive_menu"):
                try:
                    mod_inst.execute_interactive_menu(cli_dict, app_version, port_num)
                    return True
                except Exception as e:
                    print(f"\n[-] Executing MODULE critical: [{target_module_name}]: {e}")
                    time.sleep(2)
                    return True
    return False
    

def handle_module_cli_commands(module_args_list, cli_dict, app_version, port_num):
    """
    Parses and routes the structural incoming list array from --module [action] [args...]
    Usage examples:
      --module info
      --module install shutdown
      --module uninstall custom
      --module config debug log_to_file yes
      --module start shutdown timed
    """
    import project_saver_config

    if not module_args_list:
        print("🔴 ERROR: Missing [action] [sub-command] parameter")
        return

    action = str(module_args_list[0]).lower()

    if action == "info":
        print("\n" + "=" * 50)
        print("MODULES OVERVIEW")
        print("=" * 50)
        if not ACTIVE_MODULES:
            print("   No active or enabled MODULES on disk.")
        for name, mod in ACTIVE_MODULES.items():
            manifest = mod.get("MODULE_MANIFEST", {}) if isinstance(mod, dict) else {}
            meta = manifest.get("meta", {}) if isinstance(manifest, dict) else {}
            
            print(f" -> [{name.upper()}] - {manifest.get('display_name')}")
            print(f"    Author : {meta.get('author')} | Version: {meta.get('version')}")
            print(f"    Shortcut: [{manifest.get('menu_shortcut', 'N/A').upper()}] | Autostart: {manifest.get('autostart')}")
        print("=" * 50 + "\n")

    elif action == "install":
        if len(module_args_list) < 2:
            print("🔴 ERROR: Missing target module parameters.")
            return
        target_name = module_args_list[1].lower()
        
        manager_entry = ACTIVE_MODULES.get("manager")
        if isinstance(manager_entry, dict) and manager_entry.get("type") == "binary":
            import subprocess
            try:
                subprocess.run([manager_entry["path"], "--install", target_name], check=True)
            except Exception as e:
                print(f"🔴 ERROR: Standalone MODULE install failed: {e}")
        else:
            try:
                import modules.manager
                target_repo = project_saver_config.SYSTEM_CONFIG.get("manager_target_repository", "gowildchild/Project-Saver")
                modules.manager.install_module_from_cloud(target_name, target_repo)
            except ModuleNotFoundError:
                print("🔴 ERROR: The core 'manager' is missing from your local directory.")
                print("          Please manually drop 'manager' inside your modules/ folder to enable.")

    elif action == "uninstall":
        if len(module_args_list) < 2:
            print("🔴 ERROR: Missing required module parameters.")
            return
        target_name = module_args_list[1].lower()
        script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        
        # * [FIXED] ACCELERATE SCAN TO MAP BOTH RAW TEXT SCRIPTS AND COMPILED EXECUTABLES ON DISK
        target_py = os.path.join(script_base_dir, "modules", f"{target_name}.py")
        target_exe = os.path.join(script_base_dir, "modules", f"{target_name}.exe")
        
        if (os.path.exists(target_py) or os.path.exists(target_exe)) and target_name != "manager":
            try:
                if os.path.exists(target_py):
                    os.remove(target_py)
                    print(f"🟢 SUCCESS: MODULE '{target_name}' erased from disk.")
                if os.path.exists(target_exe):
                    os.remove(target_exe)
                    print(f"🟢 SUCCESS: MODULE '{target_name}.exe' erased from disk.")
            except Exception as e:
                print(f"🔴 ERROR: Failed to delete MODULE from disk: {e}")
        else:
            print("🔴 ERROR: Target MODULE not on disk or restricted.")


    elif action == "config":
        # Expects: --module config module_name key value
        if len(module_args_list) < 4:
            print("🔴 ERROR: Usage requires -> --module config [module_name] [key] [value]")
            return
        mod_name = module_args_list[1].lower()
        cfg_key = module_args_list[2].lower()
        new_val = module_args_list[3]
        
        full_lookup_key = f"{mod_name}_{cfg_key}"
        # We allow adding or updating configuration attributes safely
        project_saver_config.SYSTEM_CONFIG[full_lookup_key] = str(new_val)
        print(f"🟢 SUCCESS: Config state setting -> {full_lookup_key} = {new_val}")
        main_module_ref = sys.modules.get('__main__')
        parent_args = getattr(main_module_ref, 'CLI_ARGS', None) or cli_dict
        project_saver_config.save_config_file("project_saver.cfg", parent_args, current_version=app_version)

    elif action == "update":
        print("[*] Re-indexing modules update information.")
        bootstrap_and_discover_modules(cli_dict, app_version, port_num)
        print("🟢 SUCCESS: Local module database paths synchronized.")

    elif action == "start":
        if len(module_args_list) < 2:
            print("🔴 ERROR: Missing required target MODULE.")
            return
        target_name = module_args_list[1].lower()
        
        if target_name in ACTIVE_MODULES:
            module_object = ACTIVE_MODULES[target_name]
            if isinstance(module_object, dict) and module_object.get("type") == "binary":
                import subprocess
                try:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"[*] Executing standalone MODULE -> {target_name.upper()}")
                    main_module_ref = sys.modules.get('__main__')
                    active_profile = getattr(main_module_ref, 'active_cfg_profile', 'project_saver.cfg')
                    subprocess.run([module_object["path"], "--config", active_profile], check=True)
                except Exception as bin_err:
                    print(f"\n[-] Standalone MODULE execution crashed: {bin_err}")
                    time.sleep(2)
            
            # ─── FALLBACK MATRIX FOR RAW SCRIPT FILE OBJECT INTERACTION LOOPS ───
            elif hasattr(module_object, "execute_interactive_menu"):
                print(f"[*] Booting MODULE parameters: {target_name.upper()}")
                module_object.execute_interactive_menu(cli_dict, app_version, port_num)
        else:
            print(f"🔴 ERROR: Execution failed for MODULE '{target_name}', not installed or enabled.")


    else:
        print(f"🔴 ERROR: Unrecognized MODULE CLI command: '{action}'")
