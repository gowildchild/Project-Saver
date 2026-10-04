# project_saver_config.py
import os
import sys
import secrets
import json
import configparser

# Master memory registry to track custom configuration parameters outside argparse
SYSTEM_CONFIG = {}
EXPECTED_TOKEN = ""

def load_config_file(filepath):
    args_list = []
    global SYSTEM_CONFIG, EXPECTED_TOKEN
    
    if not os.path.exists(filepath): 
        return args_list
        
    try:
        config = configparser.ConfigParser()
        config.read(filepath, encoding="utf-8")
        
        # 1. THE WILDCARD EXTRACTION LOOP
        for section in config.sections():
            section_lower = section.strip().lower()
            for key, val in config.items(section):
                if section_lower not in ['global', 'update', 'save', 'singlefile']:
                    sanitized_key = f"{section_lower}_{key.strip().lower()}".replace("-", "_").replace(" ", "_")
                    SYSTEM_CONFIG[sanitized_key] = val.strip()
                else:
                    SYSTEM_CONFIG[f"{section_lower}_{key.strip().lower()}"] = val.strip()

        # 2. Extract Token dynamically out of the modular singlefile block mapping context
        if config.has_option("singlefile", "token"):
            EXPECTED_TOKEN = config.get("singlefile", "token").strip()

        # 3. Convert ONLY the [global] parameters into command-line arguments for argparse
        if config.has_section("global"):
            for key, val in config.items("global"):
                key = key.strip().lower()
                val = val.strip()
                if val:
                    if key == "token":
                        continue
                    args_list.append(f"--{key}")
                    if val.lower() != "true": 
                        args_list.append(val)
                        
    except Exception as e:
        print(f"[-] Error loading configuration sections: {e}")
        
    return args_list


def save_config_file(filepath, args_namespace, current_version="v0.0.76", latest_version=None):
    try:
        config = configparser.ConfigParser()
        if os.path.exists(filepath):
            config.read(filepath, encoding="utf-8")
            
        # Properly initialize ALL required structural sections to prevent NoSectionError crashes
        if not config.has_section("global"):     config.add_section("global")
        if not config.has_section("update"):     config.add_section("update")
        if not config.has_section("save"):       config.add_section("save")
        if not config.has_section("singlefile"): config.add_section("singlefile")

        # Safely set the token inside the newly created [singlefile] section
        if EXPECTED_TOKEN:
            config.set("singlefile", "token", EXPECTED_TOKEN)
            
        args_dict = vars(args_namespace)
        if args_dict.get('export_folder'):    config.set("global", "export-folder", str(args_dict['export_folder']))
        if args_dict.get('export_format'):    config.set("global", "export-format", str(args_dict['export_format']))
        if args_dict.get('export_type'):      config.set("global", "export-type", str(args_dict['export_type']))
        if args_dict.get('remote_address'):   config.set("global", "remote-address", str(args_dict['remote_address']))
        if args_dict.get('chosen_editor'):    config.set("global", "chosen-editor", str(args_dict['chosen_editor']))
        if args_dict.get('auto') is not None: config.set("global", "auto", str(args_dict['auto']))

        config.set("update", "version_current", current_version)
        if latest_version:
            config.set("update", "version_newest", latest_version)

        # Enforce clean default entries under the [save] container block if they don't exist yet
        if not config.has_option("save", "export_format_autosave"):
            config.set("save", "export_format_autosave", "manual")
        if not config.has_option("save", "export_type_autosave"):
            config.set("save", "export_type_autosave", "manual")

        if not config.has_option("singlefile", "config_filename"):
            config.set("singlefile", "config_filename", "singlefile-project-saver-config.json")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Project Saver Configuration Profile\n")
            config.write(f)
                
        print(f"[+] Active configuration successfully written to sections: {filepath}")
    except Exception as e:
        print(f"[-] Could not export section configuration profile safely: {e}")



def resolve_or_create_security_token(config_path="project_saver.cfg", port_num=19763):
    """
    Checks for an existing token inside the active structural configuration database profile. 
    If missing, it creates a secure token and outputs a native SingleFile JSON extension file profile.
    """
    global EXPECTED_TOKEN
    token_key = ""

    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))    
    resolved_config_path = config_path if os.path.isabs(config_path) else os.path.join(script_base_dir, config_path)

    config = configparser.ConfigParser()
    if os.path.exists(resolved_config_path):
        try:
            config.read(resolved_config_path, encoding="utf-8")
            if config.has_option("singlefile", "token"):
                token_key = config.get("singlefile", "token").strip()
        except:
            pass

    # If no token is found in memory arrays or the configuration file, provision a fresh hex signature
    if not token_key:
        print("[*] Security setup: Generating a new randomized API Authorization Token...")
        token_key = secrets.token_hex(16)
        
        # Write out to the ini file using a native config section to prevent parsing header crashes
        if not config.has_section("singlefile"):
            config.add_section("singlefile")
        config.set("singlefile", "token", token_key)
        
        try:
            with open(resolved_config_path, "w", encoding="utf-8") as f:
                f.write(f"# Project Saver Configuration Profile\n")
                config.write(f)
        except Exception as e:
            print(f"[-] Could not write generated token out to configuration database: {e}")

    # Synchronize tracking references inside global state pools
    EXPECTED_TOKEN = token_key

    # AUTOMATIC SINGLEFILE CONFIG GENERATOR
    sf_filename = SYSTEM_CONFIG.get("singlefile_config_filename") or "singlefile-project-saver-config.json"
    singlefile_json_path = os.path.join(script_base_dir, sf_filename)
    
    singlefile_config_payload = {
        "profiles": {
            "Project Saver": {
                "_migratedDeferredContentOptions": True,
                "_migratedTemplateFormat": True,
                "autoSaveDelay": 1,
                "autoSaveLoad": False,
                "autoSaveLoadOrUnload": True,
                "autoSaveRemove": True,
                "autoSaveRepeat": False,
                "autoSaveRepeatDelay": 10,
                "autoSaveUnload": False,
                "backgroundSave": True,
                "autoSaveDiscard": True,
                "progressBarEnabled": True,
                "saveToRestFormApi": True,
                "saveToRestFormApiUrl": f"http://localhost:{port_num}",
                "saveToRestFormApiToken": EXPECTED_TOKEN,
                "saveToRestFormApiFileFieldName": "file",
                "saveToRestFormApiUrlFieldName": "url"
            }
        },
        "rules": [
            {
                "url": "^https?://.*",
                "profile": "Project Saver",
                "autoSaveProfile": "Project Saver"
            }
        ],
        "maxParallelWorkers": 24,
        "processInForeground": False
    }
    
    try:
        with open(singlefile_json_path, "w", encoding="utf-8") as json_file:
            json.dump(singlefile_config_payload, json_file, indent=2)
    except Exception as e:
        print(f"[-] Could not auto-generate SingleFile config profile configuration: {e}")
