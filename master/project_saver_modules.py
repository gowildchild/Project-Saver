# ==========================================================================
# Project Saver Engine: Pluggable Module Registry & Dynamic Interface Router
# Copyright (c) 2026 by Gunther Voet. All Rights Reserved.
# ==========================================================================
import os
import sys
import time
import importlib.util

# Master memory allocation dictionary mapping all active, enabled modules
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
    
    # Locate or create the target module directory structure next to the entry script
    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    modules_dir = os.path.join(script_base_dir, "modules")
    
    if not os.path.exists(modules_dir):
        try:
            os.makedirs(modules_dir, exist_ok=True)
            # Create an empty init file to handle structural package context constraints safely
            with open(os.path.join(modules_dir, "__init__.py"), "w") as f: f.write("")
        except:
            return

    # Add modules directory context to python search paths dynamically
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)

    for file_entry in os.listdir(modules_dir):
        if file_entry.endswith(".py") and file_entry != "__init__.py":
            module_name = file_entry[:-3]
            try:
                # Dynamic import routing using standard importlib machinery
                spec = importlib.util.spec_from_file_location(module_name, os.path.join(modules_dir, file_entry))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                # Verify structural manifest integrity footprints exist
                if hasattr(mod, "MODULE_MANIFEST"):
                    manifest = mod.MODULE_MANIFEST
                    meta = manifest.get("meta", {})
                    
                    # Core constraints validation filter checklist gates
                    if not meta.get("enabled", True): continue
                    if not meta.get("available", True): continue
                    
                    # Automatically populate INI defaults under [module_name] if they don't exist yet
                    defaults = manifest.get("defaults", {})
                    for def_key, def_val in defaults.items():
                        cfg_key = f"{module_name.lower()}_{def_key.lower()}"
                        if cfg_key not in project_saver_config.SYSTEM_CONFIG:
                            project_saver_config.SYSTEM_CONFIG[cfg_key] = str(def_val)
                    
                    # Register into live memory pools context tracking tables
                    ACTIVE_MODULES[manifest["name"]] = mod
                    
                    shortcut = manifest.get("menu_shortcut", "").lower()
                    if shortcut:
                        SHORTCUT_MAP[shortcut] = manifest["name"]
                        
                    # Execute active autostart callbacks if bitwise parameters lock true
                    if manifest.get("autostart", False) and hasattr(mod, "register_module_callbacks"):
                        mod.register_module_callbacks(server_ref)
                        
            except Exception as e:
                print(f"[-] Failed to dynamic load module [{module_name}]: {e}")


def route_interactive_shortcut(hotkey_char, cli_dict, app_version, port_num):
    """
    Checks if a key matches an active module shortcut.
    If true, instantly passes complete console thread control to that module.
    """
    target_module_name = SHORTCUT_MAP.get(str(hotkey_char).lower())
    if target_module_name and target_module_name in ACTIVE_MODULES:
        module_object = ACTIVE_MODULES[target_module_name]
        if hasattr(module_object, "execute_interactive_menu"):
            try:
                # Hand over context execution loop tracking
                module_object.execute_interactive_menu(cli_dict, app_version, port_num)
                return True # Route cleared, screen needs repaint on return
            except Exception as e:
                print(f"\n[-] Execution blew up inside module [{target_module_name}]: {e}")
                time.sleep(2)
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
        print("🔴 ERROR: Missing action sub-command parameters layout matrix.")
        return

    # Isolate primary action keyword string (info, install, config, etc.)
    action = str(module_args_list[0]).lower()

    if action == "info":
        print("\n" + "=" * 50)
        print("📦 PLUGGABLE EXTENSION REGISTRY INVENTORY OVERVIEW")
        print("=" * 50)
        if not ACTIVE_MODULES:
            print("   (No active or enabled module scripts discovered locally.)")
        for name, mod in ACTIVE_MODULES.items():
            manifest = getattr(mod, "MODULE_MANIFEST", {})
            meta = manifest.get("meta", {})
            print(f" -> [{name.upper()}] - {manifest.get('display_name')}")
            print(f"    Author : {meta.get('author')} | Version: {meta.get('version')}")
            print(f"    Shortcut: [{manifest.get('menu_shortcut', 'N/A').upper()}] | Autostart: {manifest.get('autostart')}")
        print("=" * 50 + "\n")

    elif action == "install":
        if len(module_args_list) < 2:
            print("🔴 ERROR: Missing required target module name parameter string string.")
            return
        target_name = module_args_list[1].lower()
        # Imports your manager function dynamically over the wire
        import modules.manager
        target_repo = project_saver_config.SYSTEM_CONFIG.get("manager_target_repository", "gowildchild/Project-Saver")
        modules.manager.install_module_from_cloud(target_name, target_repo)

    elif action == "uninstall":
        if len(module_args_list) < 2:
            print("🔴 ERROR: Missing required target module filename parameter string.")
            return
        target_name = module_args_list[1].lower()
        script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        target_path = os.path.join(script_base_dir, "modules", f"{target_name}.py")
        
        if os.path.exists(target_path) and target_name != "manager":
            try:
                os.remove(target_path)
                print(f"🟢 SUCCESS: Module extension file '{target_name}.py' erased from local disk storage.")
            except Exception as e:
                print(f"🔴 ERROR: Failed to clear module off storage device: {e}")
        else:
            print("🔴 ERROR: Target module does not exist locally or is restricted.")

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
        print(f"🟢 SUCCESS: Config state mapped -> {full_lookup_key} = {new_val}")
        
        # Commits memory modifications back down onto the hard disk profile natively
        project_saver_config.save_config_file("project_saver.cfg", cli_dict, app_version)

    elif action == "update":
        print("[*] Re-indexing framework update sequence arrays...")
        bootstrap_and_discover_modules(cli_dict, app_version, port_num)
        print("🟢 SUCCESS: Local module database paths synchronized cleanly.")

    elif action == "start":
        if len(module_args_list) < 2:
            print("🔴 ERROR: Missing required target module execution name selection string.")
            return
        target_name = module_args_list[1].lower()
        
        if target_name in ACTIVE_MODULES:
            module_object = ACTIVE_MODULES[target_name]
            if hasattr(module_object, "execute_interactive_menu"):
                print(f"[*] Booting module target parameter block matrix: {target_name.upper()}")
                
                # If optional config overrides or modes are passed (e.g. --module start shutdown timed)
                # they pass down cleanly inside the sys.argv pipeline parameters automatically
                module_object.execute_interactive_menu(cli_dict, app_version, port_num)
            else:
                print(f"🔴 ERROR: Module '{target_name}' contains no interactive loop hook handler.")
        else:
            print(f"🔴 ERROR: Execution failed. Module '{target_name}' is not currently installed or enabled.")

    else:
        print(f"🔴 ERROR: Unrecognized module CLI command option action keyword string: '{action}'")
