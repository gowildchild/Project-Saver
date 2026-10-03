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
