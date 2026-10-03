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


def save_config_file(filepath, args_namespace):
    import configparser
    try:
        config = configparser.ConfigParser()
        if os.path.exists(filepath):
            config.read(filepath, encoding="utf-8")
            
        # * [FIXED] Properly initialize ALL required structural sections to prevent NoSectionError crashes
        if not config.has_section("global"):     config.add_section("global")
        if not config.has_section("update"):     config.add_section("update")
        if not config.has_section("save"):       config.add_section("save")
        if not config.has_section("singlefile"): config.add_section("singlefile")

        # * [FIXED] Safely set the token inside the newly created [singlefile] section
        if EXPECTED_TOKEN:
            config.set("singlefile", "token", EXPECTED_TOKEN)
            
        args_dict = vars(args_namespace)
        if args_dict.get('export_folder'):    config.set("global", "export-folder", str(args_dict['export_folder']))
        if args_dict.get('export_format'):    config.set("global", "export-format", str(args_dict['export_format']))
        if args_dict.get('export_type'):      config.set("global", "export-type", str(args_dict['export_type']))
        if args_dict.get('remote_address'):   config.set("global", "remote-address", str(args_dict['remote_address']))
        if args_dict.get('chosen_editor'):    config.set("global", "chosen-editor", str(args_dict['chosen_editor']))
        if args_dict.get('auto') is not None: config.set("global", "auto", str(args_dict['auto']))

        config.set("update", "version_current", VERSION)
        if LATEST_AVAILABLE_VERSION:
            config.set("update", "version_newest", LATEST_AVAILABLE_VERSION)

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


def resolve_or_create_security_token(config_path="project_saver.cfg"):
    """
    Checks for an existing token in the active config file. 
    If missing, it creates a new secure token and builds the SingleFile JSON asset automatically.
    """
    global EXPECTED_TOKEN
    token_key = ""

    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))    
    resolved_config_path = config_path if os.path.isabs(config_path) else os.path.join(script_base_dir, config_path)


	
    # 1. Attempt to check if a token already exists inside an active config file
    if SYSTEM_CONFIG.get("singlefile_token"):
        token_key = SYSTEM_CONFIG["singlefile_token"].strip()
    elif os.path.exists(resolved_config_path):
        with open(resolved_config_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("token="):
                    token_key = line.split("=", 1)[1].strip()
                    break

    # 2. If no token is found, generate a fresh secure token key string
    if not token_key:
        print("[*] Security setup: Generating a new randomized API Authorization Token...")
        token_key = secrets.token_hex(16) # Creates a highly secure 32-character hex key string
        
        # Append it cleanly to the default local configuration file profile
        try:
            with open(resolved_config_path, "a", encoding="utf-8") as f:
                f.write(f"\ntoken={token_key}\n")
        except:
            pass

    # 3. Lock it into global application state memory fields
    EXPECTED_TOKEN = token_key

    # 4. AUTOMATIC SINGLEFILE CONFIG GENERATOR
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
                "saveToRestFormApiUrl": f"http://localhost:{PORT}",
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
