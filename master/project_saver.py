import os
import re
import sys
import time
import json
import secrets
import argparse
import threading
import platform
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.parser import BytesParser
from bs4 import BeautifulSoup

from project_saver_archive import process_html_content

VERSION = "v0.0.71"
PORT = 19763
EXPECTED_TOKEN = ""
REPO_OWNER = "gowildchild"
REPO_NAME = "Project-Saver"

def resolve_or_create_security_token(config_path="project_saver.cfg"):
    """
    Checks for an existing token in the active config file. 
    If missing, it creates a new secure token and builds the SingleFile JSON asset automatically.
    """
    global EXPECTED_TOKEN
    token_key = ""

    # 1. Attempt to check if a token already exists inside an active config file
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
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
            with open(config_path, "a", encoding="utf-8") as f:
                f.write(f"\ntoken={token_key}\n")
        except:
            pass

    # 3. Lock it into global application state memory fields
    EXPECTED_TOKEN = token_key

    # 4. AUTOMATIC SINGLEFILE BROWSER CONFIG GENERATOR
    # Dynamically inject this exact token string into the configuration json file profile asset
    singlefile_json_path = "singlefile-project-saver-config.json"
    singlefile_config_payload = {
        "profiles": {
            "Project Saver": {
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
                "autoSaveProfile": "__Disabled_Settings__"
            }
        ]
    }
    
    try:
        with open(singlefile_json_path, "w", encoding="utf-8") as json_file:
            json.dump(singlefile_config_payload, json_file, indent=2)
    except Exception as e:
        print(f"[-] Could not auto-generate SingleFile config profile configuration: {e}")

class RestApiHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        auth_header = self.headers.get('Authorization', '')
        token = auth_header.replace("Bearer ", "").strip() if auth_header else ""
        
        if token != EXPECTED_TOKEN:
            # Render unauthorized connection warning logs inside the clean box engine
            alert_log = [
                "⚠️  SECURITY ALERT: Unauthorized Request Blocked!",
                "---",
                f"Source IP Network: {self.client_address[0]}",
                "Reason: Transmission Authorization Token Mismatch.",
				f"Token: {token} Expected: {EXPECTED_TOKEN}",
            ]
            render_better_box(alert_log, title_str="Security Warning", box_width_override=70)
            self.send_response(401)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length)

        # Convert namespace to a dictionary to extract clean dash keys natively
        cli_dict = vars(CLI_ARGS)

        # 1. CLIENT-SIDE RELAY FORWARDER SYSTEM
        if cli_dict.get("remote-address"):
            print(f"[*] Relaying capture payload to remote destination server: {cli_dict['remote-address']}")
            try:
                req = urllib.request.Request(cli_dict["remote-address"], data=body_bytes, headers=dict(self.headers))
                with urllib.request.urlopen(req) as response:
                    self.send_response(response.status)
                    for k, v in response.getheaders(): 
                        self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(response.read())
                    return
            except Exception as e:
                print(f"[-] Forwarding transaction failed over the network: {e}")
                self.send_response(502)
                self.end_headers()
                return

        # 2. LOCAL DAEMON EXTRACTION ENGINE
        headers_input = f"Content-Type: {self.headers.get('Content-Type')}\n\n".encode('utf-8')
        msg = BytesParser().parsebytes(headers_input + body_bytes)

        html_content = ""
        page_url = "Natively Captured"

        if msg.is_multipart():
            for part in msg.walk():
                content_disp = str(part.get('Content-Disposition', ''))
                if 'name="file"' in content_disp:
                    payload_bytes = part.get_payload(decode=True)
                    if payload_bytes:
                        html_content = payload_bytes.decode('utf-8', errors='ignore')
                elif 'name="url"' in content_disp:
                    payload_bytes = part.get_payload(decode=True)
                    if payload_bytes:
                        page_url = payload_bytes.decode('utf-8', errors='ignore')

        if not html_content:
            self.send_response(400)
            self.end_headers()
            return

        soup = BeautifulSoup(html_content, "html.parser")
        page_title = soup.title.string.strip() if soup.title else "AI_Chat_Session"
        
        # ─── THE NEW INTERCEPTED VISUAL BOX ENGINE LOGGER ───
        intercept_log = [
            "\033[93m📥 Intercepted Web Stream Archive payload from browser!\033[0m",
            "---",
            f"📄 Title: {page_title if len(page_title) <= 52 else f'{page_title[:49]}...'}",
            f"🌐 Origin: {page_url if len(page_url) <= 52 else f'{page_url[:49]}...'}"
        ]
        print() # Print empty line break for clean display
        render_better_box(intercept_log, title_str="Network Interception Notice", box_width_override=65)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "saved"}')
        self.wfile.flush()

        process_html_content(
            html_string=html_content, 
            page_title=page_title, 
            source_origin=page_url,
            export_folder=cli_dict.get("export-folder"),
            export_format=cli_dict.get("export-format"),
            export_type=cli_dict.get("export-type"),
            auto_timeout=CLI_ARGS.auto,
            editor_override=cli_dict.get("chosen-editor"),
            app_version=VERSION
        )


def check_for_updates_silently():
    """Safety placeholder to resolve historic background loop definitions."""
    pass

def set_terminal_title(title_text, run_version, run_text):
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(f"{title_text} {run_version} - {run_text}")
    else:
        sys.stdout.write(f"\x1b]2;{title_text} {run_version} - {run_text}\x07")
        sys.stdout.flush()

def render_better_box(raw_lines_list: list, title_str: str = "Project Saver", box_width_override: int = 0):
    def get_visual_width(text_line: str) -> int:
        clean = re.sub(r'\033\[[0-9;]*m', '', str(text_line))
        width = 0
        for char in clean:
            o = ord(char)
            if o in (0xfe0f, 0x200d): continue
            if (0x1f300 <= o <= 0x1f9ff) or (0x2600 <= o <= 0x27bf) or (0x2b50 <= o <= 0x2b55): width += 2
            elif 0x4e00 <= o <= 0x9fff: width += 2
            else: width += 1
        return width

    filtered_lines = [line for line in raw_lines_list if str(line).strip() != "---"]
    max_len = max((get_visual_width(line) for line in filtered_lines), default=len(title_str))
    target_width = box_width_override if box_width_override > 0 else 76
    box_width = max(target_width, max_len + 4)

    header_left = f"──┤ {title_str} ├"
    header_dash_fill = max(4, box_width - get_visual_width(header_left))
    print(f"┌{header_left}{'─' * header_dash_fill}┐")
    for line in raw_lines_list:
        clean_line = str(line).rstrip()
        if clean_line.strip() == "---":
            print(f"├{'─' * box_width}┤")
        else:
            current_width = get_visual_width(clean_line)
            padding_spaces = " " * (box_width - current_width - 2)
            print(f"│ {clean_line}{padding_spaces} │")
    print("└" + "─" * box_width + "┘")

def check_for_startup_update_and_run():
    """Pauses startup sequence for 30 seconds allowing an interactive, timed update check before daemon mode."""
    import platform
    import time
    import sys
    import urllib.request
    import json

    # We only use interactive keyboard prompts on Windows nodes natively
    is_windows = platform.system().lower() == "windows"
    if not is_windows:
        print("[*] Project Saver core daemon processing initialized on local port 19763...")
        return

    # Import native Windows tracking library without external dependencies
    import msvcrt

    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    print("==================================================")
    print("⏰ PROJECT SAVER INITIALIZATION SEQUENCE")
    print("==================================================")
    print(f"[*] Querying latest active release definitions from: {api_url}")
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Project-Saver-Startup-Engine'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest_version_tag = data.get("tag_name", "").strip()
            
            if latest_version_tag and latest_version_tag == VERSION:
                print("[+] Running the latest version profile framework.")
                print("[*] Advancing straight to active daemon mode...\n")
                return
                
            # Intercept block: A newer release exists on the cloud
            print(f"\n📢 UPDATE AVAILABLE: A newer release [{latest_version_tag}] is ready!")
            countdown = 30
            print(f"[?] Press [Y] within {countdown} seconds to execute the automated upgrade sequence.")
            print("[*] Press [N] or do nothing to bypass and advance straight to daemon mode.")
            print("--------------------------------------------------")
            
            start_time = time.time()
            user_triggered = False
            
            while time.time() - start_time < countdown:
                elapsed = int(time.time() - start_time)
                remaining = countdown - elapsed
                sys.stdout.write(f"\r    -> Advancing to daemon execution mode in: [{remaining:02d}s] (Press Y to intercept) ")
                sys.stdout.flush()
                
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                    if key == 'y':
                        user_triggered = True
                        break
                    elif key == 'n':
                        print("\n\n[*] Update scan bypassed by user selection.")
                        break
                time.sleep(0.1)
                
            if user_triggered:
                print("\n\n[*] Intercept triggered! Invoking secure manifest update sequence...")
                check_and_perform_update()
            else:
                print("\n\n[+] Countdown finalized. Launching background listening socket loops...")
                
    except Exception:
        # Fails completely silently to prevent crash spikes if network links are dead on boot/offline nodes
        print("[-] Network Status: Could not ping GitHub API. Proceeding in offline execution mode.")
        print("[+] Launching background listening socket loops...\n")


def check_and_perform_update():
    """Performs manual force upgrade downloads via --update with full SHA-256 manifest validation."""
    import platform
    import os
    import sys
    import urllib.request
    import json
    import subprocess
    import hashlib

    is_windows = platform.system().lower() == "windows"
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    print(f"[*] Initializing secure system upgrade check via: {api_url}")
    
    try:
        current_exe_path = os.path.abspath(sys.executable)
        install_dir = os.path.dirname(current_exe_path)
        
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Project-Saver-Secure-Updater'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest = data.get("tag_name", "").strip()
            
            # If triggered manually via CLI but already matching, exit early safely
            if latest == VERSION and "--update" in sys.argv:
                print("[+] Already running the latest version profile framework.")
                return
            
            download_url = None
            manifest_url = None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if (is_windows and name.endswith("-portable.exe")) or (not is_windows and "linux" in name.lower()):
                    download_url = asset.get("browser_download_url")
                if name == "manifest.txt":
                    manifest_url = asset.get("browser_download_url")
            
            if not download_url or not manifest_url:
                print("[-] Error: Missing distribution executable or master manifest.txt in release.")
                return

            print(f"[*] Fetching delivery assets for integrity verification...")
            temp_download_name = "project_saver.new" if is_windows else f"project_saver_{latest}_linux"
            temp_download_path = os.path.join(install_dir, temp_download_name)
            
            # 1. Download the new binary payload
            with urllib.request.urlopen(download_url) as stream:
                with open(temp_download_path, "wb") as f: 
                    f.write(stream.read())
            
            # 2. Download the unified manifest.txt file strings into runner memory
            expected_hash = None
            with urllib.request.urlopen(manifest_url) as stream:
                manifest_lines = stream.read().decode('utf-8').splitlines()
                # Locate the very first SHA-256 Checksum string in the document (corresponds to asset 1)
                for line in manifest_lines:
                    if "SHA-256 Checksum" in line:
                        expected_hash = line.split(":")[1].strip().lower()
                        break

            if not expected_hash:
                print("[-] Verification Error: Manifest format is malformed or invalid.")
                os.remove(temp_download_path)
                return

            # 3. NATIVE CRYPTOGRAPHIC SHA-256 CALCULATION LOOP
            print("[*] Evaluating security footprint hash keys...")
            sha256_hash = hashlib.sha256()
            with open(temp_download_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            computed_hash = sha256_hash.hexdigest().lower()

            print(f"    -> Expected Hash: {expected_hash}")
            print(f"    -> Computed Hash: {computed_hash}")

            if computed_hash != expected_hash:
                print("\n[🚨] SECURITY BARRICADE: SHA-256 Integrity Hash Mismatch!")
                print("    The downloaded upgrade executable failed security checksum validation.")
                print("    Upgrade aborted automatically to protect this machine.")
                os.remove(temp_download_path)
                return
            
            print("[+] Cryptographic Verification Passed: Binary file code matches perfectly.")

            # 4. ATOMIC HOT-SWAP REPLACEMENT CHOREOGRAPHY
            if is_windows:
                old_exe_path = os.path.join(install_dir, "project_saver.old")
                if os.path.exists(old_exe_path):
                    try: os.remove(old_exe_path)
                    except Exception: pass
                
                print("[*] Performing safe atomic hot-swap file replacements...")
                os.rename(current_exe_path, old_exe_path)
                os.rename(temp_download_path, current_exe_path)
                
                cleanup_cmd = f"timeout /t 2 >nul && del \"{old_exe_path}\""
                subprocess.Popen(cleanup_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                final_linux_path = os.path.join(install_dir, "project_saver")
                if os.path.exists(final_linux_path):
                    os.remove(final_linux_path)
                os.rename(temp_download_path, final_linux_path)
                os.chmod(final_linux_path, 0o755)

            print("[🎉] SUCCESS: Secure system upgrade complete. Please restart Project Saver to run the new version!")
            sys.exit(0)
            
    except Exception as e:
        print(f"[-] Secure upgrade block failed: {e}")

def save_config_file(filepath, args_namespace):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Project Saver {VERSION} Configuration Profile\n")
            
            # Securely preserve your authorization token
            if EXPECTED_TOKEN:
                f.write(f"token={EXPECTED_TOKEN}\n")
            
            # Convert namespace to a dictionary to check raw dash keys directly
            args_dict = vars(args_namespace)
            
            # Pure dash-only configuration lookup and output
            if args_dict.get('export-folder'):
                f.write(f"export-folder={args_dict['export-folder']}\n")
            if args_dict.get('export-format'):
                f.write(f"export-format={args_dict['export-format']}\n")
            if args_dict.get('export-type'):
                f.write(f"export-type={args_dict['export-type']}\n")
            if args_dict.get('remote-address'):
                f.write(f"remote-address={args_dict['remote-address']}\n")
            if args_dict.get('chosen-editor'):
                f.write(f"chosen-editor={args_dict['chosen-editor']}\n")
            if args_dict.get('auto') is not None:
                f.write(f"auto={args_dict['auto']}\n")
                
        print(f"[+] Active configuration written to profile: {filepath}")
    except Exception as e:
        print(f"[-] Could not export configuration profile: {e}")


def load_config_file(filepath):
    args_list = []
    if not os.path.exists(filepath): 
        return args_list
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): 
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key, val = key.strip().lower(), val.strip()
                if val:
                    # Skip internal variables like token so argparse doesn't break
                    if key == "token":
                        continue
                    # Appends exactly what is written in the file (e.g., --export-folder)
                    args_list.append(f"--{key}")
                    if val.lower() != "true": 
                        args_list.append(val)
    return args_list
	
def run_server():
    set_terminal_title("Project Saver", VERSION, "Server Running")
    
    # Launches the silent background check thread for new GitHub releases
    threading.Thread(target=check_for_updates_silently, daemon=True).start()

    server_address = ('', PORT)
    httpd = HTTPServer(server_address, RestApiHandler)

    cli_dict = vars(CLI_ARGS)
    startup_log = [
        f"Server Listening:    http://localhost:{PORT}",
        f"Security Token:      {EXPECTED_TOKEN}",
        "---",
        f"📂 Target Folder:    {os.path.abspath(cli_dict.get('export-folder'))}",
        f"⚙️ Profile Mode:    {str(cli_dict.get('export-type')).upper()}",
        f"🗒️ Formats Enabled: {str(cli_dict.get('export-format')).upper()}",
        "---",
        "💡 Quick Action:    Import singlefile-project-saver-config.json straight into SingleFile Options."
    ]
    # Enforces a solid structural margin to display the long hash strings beautifully
    render_better_box(startup_log, title_str=f"Project Saver {VERSION}", box_width_override=65)
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[-] Shutting down Project Saver API Server Daemon cleanly.")

if __name__ == "__main__":
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)

    parser = argparse.ArgumentParser(
        description="Project Saver Server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    if platform.system().lower() == "windows":
        default_export_dir = os.path.join(os.environ["USERPROFILE"], "Documents", "Project-Saver", "export")
    else:
        default_export_dir = os.path.join(os.path.expanduser("~"), "Documents", "Project-Saver", "export")
		
    parser.add_argument("--export-folder", default=argparse.SUPPRESS, help=f"Target base folder path where files will be written. (Default: {default_export_dir})")
    parser.add_argument("--export-format", default=argparse.SUPPRESS, help="Comma-separated dumping targets: markdown, html, pdf. (Default: markdown)")
    parser.add_argument("--export-type", default=argparse.SUPPRESS, choices=["auto", "code", "web"], help="Parsing layout configuration profile strategy. (Default: auto)")
    parser.add_argument("--remote-address", default=argparse.SUPPRESS, help="Turns runtime engine into proxy router. (Default: None)")
    parser.add_argument("--auto", type=int, nargs='?', const=5, default=None, help="Enables automated execution timeout duration.")
    parser.add_argument("--config", default="", help="Load options from a custom configuration text file.")
    parser.add_argument("--config-save", default="", help="Save setup flags into configuration profile text file.")
    parser.add_argument("--about", action="store_true", help="Displays developer credits and exit.")
    parser.add_argument("--update", action="store_true", help="Queries GitHub downloads update binary and exit.")
    parser.add_argument("--chosen-editor", default=argparse.SUPPRESS, choices=["system_default", "obsidian", "vscode", "marktext"], help="Preferred markdown viewer/editor launcher link tool. (Default: system_default)")

    temp_args = sys.argv[1:]
    
    # ─── 2. DYNAMICALLY ISOLATE THE ACTIVE CONFIGURATION FILENAME ───
    active_cfg_profile = "project_saver.cfg"
    if "--config" in temp_args:
        try:
            c_idx = temp_args.index("--config")
            if c_idx + 1 < len(temp_args):
                active_cfg_profile = temp_args[c_idx + 1]
        except Exception:
            pass

    # ─── 3. COMBINE ARRAYS IN CORRECT OVERRIDE PRIORITY LAYER ORDER ───
    # Configuration options are evaluated first, terminal entries come LAST to explicitly override them
    loaded_file_args = load_config_file(active_cfg_profile) if os.path.exists(active_cfg_profile) else []
    combined_args = loaded_file_args + temp_args
    CLI_ARGS = parser.parse_args(combined_args)
    cli_dict = vars(CLI_ARGS)

    # ─── 4. APPLY DEFAULT FALLBACKS TO PURE DASH KEYS ───
    if "export-folder" not in cli_dict or not cli_dict["export-folder"]:
        cli_dict["export-folder"] = default_export_dir
        
    if "export-format" not in cli_dict or not cli_dict["export-format"]: 
        cli_dict["export-format"] = "markdown"
        
    if "export-type" not in cli_dict or not cli_dict["export-type"]: 
        cli_dict["export-type"] = "auto"
        
    if "chosen-editor" not in cli_dict or not cli_dict["chosen-editor"]: 
        cli_dict["chosen-editor"] = "system_default"
        
    if "remote-address" not in cli_dict or cli_dict["remote-address"] is None: 
        cli_dict["remote-address"] = ""

    # ─── 5. EXECUTE OPERATIONAL TASKS USING SAFE DIRECTORY LOOKUPS ───
    if cli_dict.get("about"):
        about_data = [
            f"Project Saver {VERSION} - Local & Remote Web Scraping Daemon",
            "---",
            "🛠️ Developer: Gunther Voet",
            "📜 License: Open Source (AGPL-3.0 license)",
            "🌐 Repository: https://github.com/gowildchild/Project-Saver/",
            "---",
            "Designed to cleanly archive browser sessions, code repositories",
            "and web documentation directly into structured Markdown files,",
            "raw backups, or professional PDF layouts."
        ]
        render_better_box(about_data, title_str="About \"Project Saver\"", box_width_override=70)
        sys.exit(0)

    if cli_dict.get("update"):
        check_and_perform_update()
        sys.exit(0)

    if cli_dict.get("config-save"):
        save_config_file(cli_dict["config-save"], CLI_ARGS)
        sys.exit(0)

    # Initialize the authentication token validation sequence using the verified config filename
    resolve_or_create_security_token(active_cfg_profile)

    run_server()

