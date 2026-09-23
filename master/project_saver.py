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

VERSION = "v0.0.77-julliet"
PORT = 19763
EXPECTED_TOKEN = ""
CONSOLE_LOCK = threading.Lock()
REPO_OWNER = "gowildchild"
REPO_NAME = "Project-Saver"

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
    if os.path.exists(resolved_config_path):
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
    singlefile_json_path = os.path.join(script_base_dir, "singlefile-project-saver-config.json")
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

class RestApiHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        auth_header = self.headers.get('Authorization', '')
        token = auth_header.replace("Bearer ", "").strip() if auth_header else ""
        
        if token != EXPECTED_TOKEN:
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
            f"📄 Title: {page_title if len(page_title) <= 84 else f'{page_title[:84]}..'}",
            f"🌐 Origin: {page_url if len(page_url) <= 84 else f'{page_url[:84]}..'}"
        ]
        
        print() # Print empty line break for clean display
        render_better_box(intercept_log, title_str="\033[93mNetwork Interception Notice\033[0m", box_width_override=86)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "saved"}')
        self.wfile.flush()

        # FIXED: Processes page archiving sequentially on the main loop without thread clutter
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
        print("[*] Project Saver daemon initialized on local port 19763...")
        return

    # Import native Windows tracking library without external dependencies
    import msvcrt

    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    print("==================================================")
    print("⏰ PROJECT SAVER INITIALIZATION")
    print("==================================================")
    print(f"[*] Querying latest active release definitions from: {api_url}")
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Project-Saver-Startup-Engine'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest_version_tag = data.get("tag_name", "").strip()
            
            if latest_version_tag and latest_version_tag == VERSION:
                print(f"[+] Running the latest version {VERSION}.")
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


def check_and_perform_update(mode_override: int = 0):
    """
    Performs manual force upgrade downloads via --update with full SHA-256 manifest validation
    Bitmask stacking flags (0-15):
      1 = Check Version
      2 = Check Update (Manifest Parsing / Fetch expected hash)
      4 = Update (Hot-Swap / Download & Replace Executable)
      8 = New token + renew singlefile JSON configuration profile
    """
    import platform
    import os
    import sys
    import urllib.request
    import json
    import subprocess
    import hashlib

    is_windows = platform.system().lower() == "windows" 
    expected_version = ""
    expected_hash = None
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    
    # ─── 1. EVALUATE BITMASK: TOKEN AND CONFIGURATION GENERATION (Bit 8) ───
    if mode_override & 8:
        script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        cfg_file_path = os.path.join(script_base_dir, "project_saver.cfg")
        if os.path.exists(cfg_file_path):
            try: os.remove(cfg_file_path)
            except: pass
        resolve_or_create_security_token("project_saver.cfg")
        print(f"[+] SUCCESS: Token regenerated! New active access key token is: {EXPECTED_TOKEN}")
        print("💡 Tip: Re-import your fresh singlefile configuration profile into your browser extension.")
        if mode_override == 8:
            return

    # Skip network queries if no update or version bits are stacked
    if not (mode_override & 1 or mode_override & 2 or mode_override & 4):
        return

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
                print(f"[+] Already running the latest version {VERSION}.")
                return
            
            # ─── 2. EVALUATE BITMASK: CHECK VERSION ONLY (Bit 1) ───
            # Only intercept and return early if bit 1 is set EXCLUSIVELY without update execution triggers
            if (mode_override & 1) and not (mode_override & 4):
                if latest == VERSION:
                    print(f"[+] You are running the latest release ({VERSION}).")
                else:
                    print(f"[U] UPDATE FOUND: Latest version is [{latest}]. Local version is [{VERSION}].")
                if mode_override == 1:
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
                print("[-] Error: Missing distribution executable or master manifest.txt in release.")
                return

            # ─── 3. EVALUATE BITMASK: VERIFY MANIFEST FILES (Bit 2) ───
            # Download and parse manifest fields if either manifest check (2) or execution update (4) bits are set
            if mode_override & 2 or mode_override & 4:
                print(f"[*] Fetching delivery assets for integrity verification...")
                with urllib.request.urlopen(manifest_url) as stream:
                    manifest_lines = stream.read().decode('utf-8').splitlines()
                    for line in manifest_lines:
                        if "Version Tag" in line:
                            expected_version = line.split(":")[1].strip().lower()
                        if "SHA-256 Checksum" in line:
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

                # Cryptographic Validation Loop
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

                print("[+] SUCCESS: Secure upgrade to latest version completed...")
                print(f"[+] Please restart Project Saver to run {expected_version if expected_version else latest}!")
                sys.exit(0)
                
            return latest
            
    except Exception as e:
        print(f"[-] Secure upgrade failed: {e}")
        return None


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
    # threading.Thread(target=check_for_updates_silently, daemon=True).start()

    server_address = ('', PORT)
    httpd = HTTPServer(server_address, RestApiHandler)

    #server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    #server_thread.start()	

    cli_dict = vars(CLI_ARGS)
    startup_log = [
        f"Server Listening:   http://localhost:{PORT}",
        f"Security Token:     {EXPECTED_TOKEN}",
        "---",
        f"📂 [E]xport Folder:   {os.path.abspath(cli_dict.get('export-folder'))}",
        f"⚙️ [P]rofile Mode:    {str(cli_dict.get('export-type')).upper()}",
        f"🗒️ [F]ormats Enabled: {str(cli_dict.get('export-format')).upper()}",
        "---",
        f"💡 [I]mport Config:   Open folder containing singlefile-project-saver-config.json configuration.",
        f"   [R]enew Token:      Regenerate randomized API access authorization key.",
        f"   [U]pdate:           Verify integrity hash and update application (1x=check, 2x=update).",
        f"   [Q]uit Application: Requires 3 consecutive taps with the shoes to escape Kansas."
		
    ]

    render_better_box(startup_log, title_str=f"Project Saver {VERSION}", box_width_override=60)
        
    execute_interactive_dashboard_monitor(httpd)


def execute_interactive_dashboard_monitor(httpd_server_reference):
    """Processes server traffic and terminal hotkeys sequentially without high-speed loop cascades."""
    import sys
    import os
    import subprocess
    import time

    quit_press_counter = 0
    update_press_counter = 0
    latest_discovered_version = None
    cli_dict = vars(CLI_ARGS)
    script_base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

    while True:
        try:
            # 1. Process exactly ONE incoming web request payload if SingleFile is waiting.
            # Timeout = 0.1 seconds means it checks for network traffic briefly and moves on.
            httpd_server_reference.timeout = 0.1
            httpd_server_reference.handle_request()

            # 2. Render the static interface status line safely
            if quit_press_counter > 0:
                sys.stdout.write(f"\r⚠️ Press [Q]uit again [{quit_press_counter}/3] times to escape Kansas...")
            elif update_press_counter == 1:
                v_msg = f" {latest_discovered_version}" if latest_discovered_version else ""
                sys.stdout.write(f"\rPress [U]pdate again to execute automated upgrade to{v_msg}...")
            else:
                sys.stdout.write("\r[?] Ready for hotkey: ")
            sys.stdout.flush()

            # 3. Standard blocking input check using hardware polling
            user_triggered_key = ""
            if os.name == 'nt':
                import msvcrt
                if msvcrt.kbhit():
                    user_triggered_key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                    # Hard flush any trailing scan codes from multi-byte key presses instantly
                    while msvcrt.kbhit():
                        msvcrt.getch()
                else:
                    time.sleep(0.1)
                    continue
            else:
                import select
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not ready:
                    continue
                user_triggered_key = sys.stdin.readline().strip().lower()

            # ─── HOTKEY MATRIX ACTIONS ───
            if user_triggered_key == 'e':
                export_path = os.path.abspath(cli_dict.get('export-folder'))
                print(f"\n[E] Export folder opened: {export_path}")
                if not os.path.exists(export_path):
                    os.makedirs(export_path, exist_ok=True)
                if os.name == 'nt':
                    subprocess.Popen(f'explorer.exe "{export_path}"')
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', export_path])
                else:
                    subprocess.Popen(['xdg-open', export_path])

            elif user_triggered_key == 'i':
                print(f"\n[I] Import SingleFile JSON config folder opened: {script_base_dir}")
                if os.name == 'nt':
                    subprocess.Popen(f'explorer.exe "{script_base_dir}"')
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', script_base_dir])
                else:
                    subprocess.Popen(['xdg-open', script_base_dir])

            elif user_triggered_key == 'r':
                print("\n[R] Re-creating secure token...")
                check_and_perform_update(mode_override=8)

            elif user_triggered_key == 'f':
                print(f"\n[F] Formats active profile values: {str(cli_dict.get('export-format')).upper()}")

            elif user_triggered_key == 'p':
                print(f"\n[P] Parsing profile strategy layout mode: {str(cli_dict.get('export-type')).upper()}")

            elif user_triggered_key == 'u':
                update_press_counter += 1
                if update_press_counter == 1:
                    latest_discovered_version = check_and_perform_update(mode_override=1)
                    if not latest_discovered_version or latest_discovered_version == VERSION:
                        update_press_counter = 0
                elif update_press_counter >= 2:
                    print("\n[*] Update Started: Initializing secure system upgrade sequence...")
                    check_and_perform_update(mode_override=4)
                    os._exit(0)
                continue

            elif user_triggered_key == 'q':
                quit_press_counter += 1
                if quit_press_counter >= 3:
                    print("\n[-] Shutting down: Project Saver API Server Daemon. Goodbye!")
                    os._exit(0)
                continue

            if user_triggered_key not in ['q', 'u'] and user_triggered_key != "":
                quit_press_counter = 0
                update_press_counter = 0

        except KeyboardInterrupt:
            print("\n[-] Shutting down Project Saver API Server Daemon cleanly.")
            os._exit(0)


			

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
        check_and_perform_update(mode_override=7)
        sys.exit(0)

    if cli_dict.get("config-save"):
        save_config_file(cli_dict["config-save"], CLI_ARGS)
        sys.exit(0)

    # Initialize the authentication token validation sequence using the verified config filename
    resolve_or_create_security_token(active_cfg_profile)

    run_server()

