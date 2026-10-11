import os
import sys
import time
import platform
import urllib.request
import json
import subprocess
import hashlib

def check_for_startup_update_and_run(version, repo_owner, repo_name, check_callback):
    """Pauses startup sequence for 30 seconds allowing an interactive, timed update check before daemon mode. """

    # We only use interactive keyboard prompts on Windows nodes natively
    is_windows = platform.system().lower() == "windows"
    if not is_windows:
        print("[*] Project Saver daemon initialized on local port 19763...")
        return

    # Import native Windows tracking library without external dependencies
    import msvcrt

    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    print("==================================================")
    print("⏰ PROJECT SAVER INITIALIZATION")
    print("==================================================")
    print(f"[*] Querying latest active release definitions from: {api_url}")
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Project-Saver-Startup-Engine'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest_version_tag = data.get("tag_name", "").strip()
            
            if latest_version_tag and latest_version_tag == version:
                #print(f"[+] Running the latest version {version}.")
                #print("[*] Startup complete. Advancing straight to active daemon mode...\n")
                return
                
            elif latest_version_tag and latest_version_tag != version:
                import project_saver_config
                #print(f"\n[🔄 NOTIFICATION]: A newer build [{latest_version_tag}] is available on GitHub.")
                #print(f"[*] Writing update availability flag into project_saver.cfg...")
                
                main_module_ref = sys.modules.get('__main__')
                parent_args = getattr(main_module_ref, 'CLI_ARGS', None)
                
                if parent_args:
                    # Update the config file parameters on disk but do NOT download the binary yet
                    project_saver_config.save_config_file("project_saver.cfg", parent_args, version, latest_version_tag)
                return 
    
    except Exception:
        print("[-] Network Status: Could not ping GitHub API. Proceeding in offline execution mode.")
        print("[+] Startup complete. Launching background listening socket loops...\n")


def check_and_perform_update(version, repo_owner, repo_name, mode_override: int = 0, resolve_token_callback=None):
    """
    Performs manual force upgrade downloads via --update with full SHA-256 manifest validation
    Bitmask stacking flags (0-15): 1 = Check Version, 2 = SHA-256 Integrity Check, 4 = Update (Hot-Swap), 8 = New Token and renew singlefile JSON config profile
                                   64 = Check Module Version, 128 = SHA-256 Integrity Module, 256 = Update Module, 512 = New Module Install
    """

    is_windows = platform.system().lower() == "windows" 
    expected_version = ""
    expected_hash = None
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    mod_url_json = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/refs/heads/modules/modules/manifest.json"
    if mode_override & 8:
        script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        cfg_file_path = os.path.join(script_base_dir, "project_saver.cfg")
        if os.path.exists(cfg_file_path):
            try: os.remove(cfg_file_path)
            except: pass
            
        if resolve_token_callback:
            resolve_token_callback("project_saver.cfg")
            print(f"\r[+] SUCCESS: Token successfully regenerated!")
        else:
            print(f"\r[+] Configuration file reset completed.")
        print("💡 Tip: Re-import your fresh singlefile configuration profile into your browser extension.")
        if mode_override == 8:
            return

    if not (mode_override & (1 | 2 | 4 | 64 | 128 | 256)):
        return


    if (mode_override & (64 | 128 | 256 | 512)):
        print(f"\n[*] Initializing secure modules branch upgrade check via: {mod_url_json}")
        try:
            script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
            modules_dir = os.path.join(script_base_dir, "modules")
            
            req = urllib.request.Request(mod_url_json, headers={'User-Agent': 'Project-Saver-Secure-Module-Updater'})
            with urllib.request.urlopen(req) as response:
                remote_manifest = json.loads(response.read().decode('utf-8'))
            
            # Isolate platform tracking dictionary boundaries from data schema
            platform_key = "windows" if is_windows else "linux"
            remote_modules = remote_manifest.get("platforms", {}).get(platform_key, {})
            
            import project_saver_modules
            modules_pool = project_saver_modules.ACTIVE_MODULES
            
            # Iterate through available component registries natively
            for mod_name, remote_meta in remote_modules.items():
                online_ver = remote_meta.get("version", "v0.0.0").strip()
                expected_mod_hash = remote_meta.get("sha256", "").strip().lower()
                binary_filename = remote_meta.get("binary_filename", f"{mod_name}.exe" if is_windows else mod_name)
                target_file_path = os.path.join(modules_dir, binary_filename)
                
                # Fetch active local version strings straight out of module memory boundaries
                local_mod_ref = modules_pool.get(mod_name.lower())
                manifest_block = local_mod_ref.get("MODULE_MANIFEST", {}) if isinstance(local_mod_ref, dict) else {}
                local_ver = manifest_block.get("meta", {}).get("version", "v0.0.0").strip()
                
                project_saver_config.SYSTEM_CONFIG[f"update_version_modules_current"] = local_ver
                project_saver_config.SYSTEM_CONFIG[f"update_version_modules_newest"] = online_ver
                
                # ─── A2. EVALUATE MODULE BITMASK: CHECK VERSION ONLY (Bit 64) ───
                if (mode_override & 64) and not (mode_override & 256):
                    if online_ver != local_ver:
                        print(f"[U] MODULE UPDATE AVAILABLE: [{mod_name.upper()}] {local_ver} < {online_ver}")
                    else:
                        print(f"[+] Module {mod_name.upper()} already running at the latest version: {local_ver}.")
                
                # ─── A3. EVALUATE MODULE BITMASK: CRYPTOGRAPHIC SHA-256 CHECK (Bit 128) ───
                mod_integrity_passed = False
                if (mode_override & 128) and os.path.exists(target_file_path):
                    sha256_algo = hashlib.sha256()
                    with open(target_file_path, "rb") as f_in:
                        for chunk in iter(lambda: f_in.read(4096), b""):
                            sha256_algo.update(chunk)
                    computed_mod_hash = sha256_algo.hexdigest().lower()
                    
                    if computed_mod_hash == expected_mod_hash:
                        print(f"    🟢 OK: SHA-256 integrity hash ok for module [{mod_name.upper()}].")
                        mod_integrity_passed = True
                    else:
                        print(f"    🔴 ERROR: SHA-256 integrity hash footprint mismatch for module [{mod_name.upper()}]!")
                
                # ─── A4. EVALUATE MODULE BITMASK: HOT-SWAP UPGRADE OVER THE WIRE (Bit 256) ───
                if mode_override & 256:
                    if (mode_override & 128) and not mod_integrity_passed and os.path.exists(target_file_path):
                        print(f"    ⚠️ ABORTED: Skipping hot-swap update for [{mod_name.upper()}].")
                        continue
                        
                    # Build absolute download branch paths based on remote mapping metadata instructions
                    dl_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/refs/heads/modules/modules/{binary_filename}"
                    
                    print(f"[*] Pre-Fetching module asset stream payload for [{mod_name.upper()}]...")
                    try:
                        req_dl = urllib.request.Request(dl_url, headers={'User-Agent': 'Project-Saver-Module-HotSwap'})
                        with urllib.request.urlopen(req_dl, timeout=10) as stream_dl:
                            payload_bytes = stream_dl.read()
                            
                        # Force clean filesystem overwrite directly to your modules subdirectory folder
                        with open(target_file_path, "wb") as f_out:
                            f_out.write(payload_bytes)
                        print(f"    🟢 SUCCESS: Module [{mod_name.upper()}] safely upgraded to: {online_ver}!")
                    except Exception as err_dl:
                        print(f"    🔴 FAILED to upgrade module over the wire: {err_dl}")
                        
            # Save newly established metrics version strings out to file profile disk layers
            main_module_ref = sys.modules.get('__main__')
            p_args = getattr(main_module_ref, 'CLI_ARGS', None) or {}
            project_saver_config.save_config_file("project_saver.cfg", p_args, current_version=version)
            
            # Re-index parameters workspace component registries tracks smoothly
            project_saver_modules.bootstrap_and_discover_modules({}, version, 19763)
            if not (mode_override & (1 | 2 | 4)):
                return "v0.0.0"
        except Exception as e:
            print(f"[-] Pluggable modules pipeline upgrade failed: {e}")
            if not (mode_override & (1 | 2 | 4)):
                return "v0.0.0"

    
    print(f"\n[*] Initializing SHA-256 integrity check via: {api_url}")
    
    try:
        current_exe_path = os.path.abspath(sys.executable)
        install_dir = os.path.dirname(current_exe_path)
        
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Project-Saver-Secure-Updater'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest = data.get("tag_name", "").strip()
            
            if latest == version and "--update" in sys.argv:
                print(f"[+] Already running the latest version {version}.")
                return

            if mode_override & 16:
                return latest

            # ─── 2. EVALUATE BITMASK: CHECK VERSION ONLY (Bit 1) ───
            # Only intercept and return early if bit 1 is set EXCLUSIVELY without update execution triggers
            if (mode_override & 1) and not (mode_override & 4):
                if latest == version:
                    print(f"[+] You are running the latest release ({version}).")
                else:
                    print(f"[U] UPDATE FOUND: Latest version is [{latest}]. Local version is [{version}].")
                if not (mode_override & (2 | 4)):
                    return latest

            download_url = None
            manifest_url = None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if (is_windows and name.endswith("-portable.exe")) or (not is_windows and "linux" in name.lower()):
                    download_url = asset.get("browser_download_url")
                if name == "manifest.txt":
                    manifest_url = asset.get("browser_download_url")
            
            if not download_url or not manifest_url:
                print("[-] Error: Missing distribution executable or master manifest in release.")
                return

            # ─── 3. EVALUATE BITMASK: VERIFY MANIFEST FILES (Bit 2) ───
            # Download and parse manifest fields if either manifest check (2) or execution update (4) bits are set
            if mode_override & 2 or mode_override & 4:
                print(f"[*] Pre-Fetching Project Saver MANIFEST for integrity verification...")
                with urllib.request.urlopen(manifest_url) as stream:
                    manifest_lines = stream.read().decode('utf-8').splitlines()
                    target_platform_found = False
                    for line in manifest_lines:
                        if is_windows and "WINDOWS" in line:
                            target_platform_found = True
                        elif not is_windows and "LINUX" in line:
                            target_platform_found = True
                            
                        if "Version Tag" in line:
                            expected_version = line.split(":")[1].strip().lower()
                            
                        if target_platform_found and "SHA-256 Checksum" in line:
                            expected_hash = line.split(":")[1].strip().lower()
                            break

            # ─── 4. EVALUATE BITMASK: EXECUTE DOWNSTREAM UPDATE PROCESS (Bit 4) ───
            if mode_override & 4:
                print(f"[*] Pre-Fetching Project Saver for integrity verification...")
                temp_download_name = "project_saver.new" if is_windows else f"project_saver_{latest}_linux"
                temp_download_path = os.path.join(install_dir, temp_download_name)
                
                # Download binary payload
                with urllib.request.urlopen(download_url) as stream:
                    with open(temp_download_path, "wb") as f: 
                        f.write(stream.read())

                if not expected_hash:
                    print("[-] Verification Error: Manifest format is malformed or invalid.")
                    try: os.remove(temp_download_path)
                    except: pass
                    return

                print("[*] Verifying Project Saver integrity SHA-256 hash...")
                sha256_hash = hashlib.sha256()
                with open(temp_download_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                computed_hash = sha256_hash.hexdigest().lower()

                print(f"    -> Expected Hash: {expected_hash}")
                print(f"    -> Computed Hash: {computed_hash}")

                if computed_hash != expected_hash:
                    print("\n[!] SECURITY ISSUE: SHA-256 Integrity Hash Mismatch!")
                    print("    The downloaded upgrade executable failed security checksum validation.")
                    print("    Upgrade aborted automatically to protect this machine.")
                    try: os.remove(temp_download_path)
                    except: pass
                    return

                verification_status = "[+] SHA-256 Integrity Verification Passed"

                if is_windows:
                    old_exe_path = os.path.join(install_dir, "project_saver.old")
                    if os.path.exists(old_exe_path):
                        try: os.remove(old_exe_path)
                        except Exception: pass

                    verification_status += ", Performing safe hot-swap update..."
                    print(f"{verification_status}")
                    if current_exe_path.lower().endswith("python.exe") or not getattr(sys, 'frozen', False):
                        current_exe_path = os.path.join(install_dir, "project_saver.exe")
                    os.rename(current_exe_path, old_exe_path)
                    os.rename(temp_download_path, current_exe_path)
                    time.sleep(3)
                    cleanup_cmd = f"timeout /t 2 >nul && del \"{old_exe_path}\""
                    subprocess.Popen(cleanup_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    final_linux_path = os.path.join(install_dir, "project_saver")
                    if os.path.exists(final_linux_path):
                        os.remove(final_linux_path)
                    os.rename(temp_download_path, final_linux_path)
                    os.chmod(final_linux_path, 0o755)

                print("[+] SUCCESS: Secure upgrade to latest version completed...")
                print(f"[+] Please restart Project Saver to run {expected_version if expected_version else latest}!")
                sys.exit(0)
                
            return latest
            
    except Exception as e:
        print(f"[-] Secure upgrade failed: {e}")
        return None
