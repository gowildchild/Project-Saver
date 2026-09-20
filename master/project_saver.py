import os
import re
import sys
import time
import json
import secrets
import argparse
import threading
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.parser import BytesParser
from bs4 import BeautifulSoup

from project_saver_archive import process_html_content

VERSION = "v0.0.42"
PORT = 8000
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
        "endpoint": f"http://localhost:{PORT}",
        "serverToken": EXPECTED_TOKEN,
        "bodyFilenameField": "file",
        "bodyUrlField": "url",
        "destination": "server",
        "autoSave": "none"
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
                "Reason: Transmission Authorization Token Mismatch."
            ]
            render_better_box(alert_log, title_str="Security Warning", box_width_override=70)
            self.send_response(401)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length)

        # 1. CLIENT-SIDE RELAY FORWARDER SYSTEM
        if CLI_ARGS.remote_address:
            print(f"[*] Relaying capture payload to remote destination server: {CLI_ARGS.remote_address}")
            try:
                req = urllib.request.Request(CLI_ARGS.remote_address, data=body_bytes, headers=dict(self.headers))
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
            export_folder=CLI_ARGS.export_folder,
            export_format=CLI_ARGS.export_format,
            export_type=CLI_ARGS.export_type,
            auto_timeout=CLI_ARGS.auto,
            editor_override=CLI_ARGS.chosen_editor
        )

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

def check_for_updates_silently():
    """Queries GitHub API inside a non-blocking daemon thread to log update status alerts."""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Project-Saver-Startup-Engine'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest_version_tag = data.get("tag_name", "").strip()
            if latest_version_tag and latest_version_tag != VERSION:
                alert_box = [
                    f"📢 UPDATE AVAILABLE: A newer release [{latest_version_tag}] is ready!",
                    "---",
                    "To automatically update your application system,",
                    "terminate this server instance and execute the command:",
                    "--> project_saver.exe --update"
                ]
                print()
                render_better_box(alert_box, title_str="System Update Notice", box_width_override=65)
    except:
        pass  # Fails silently to prevent crash spikes if network links are dead on boot

def check_and_perform_update():
    """Performs manual force execution upgrade downloads via --update."""
    import platform
    is_windows = platform.system().lower() == "windows"
    local_binary_name = "project_saver.exe" if is_windows else "project_saver"
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    print(f"[*] Initializing manual system upgrade check via: {api_url}")
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Project-Saver-Manual-Updater'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest = data.get("tag_name", "").strip()
            if latest == VERSION:
                print("[+] Already running the latest version profile framework."); return
            
            download_url = None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if (is_windows and name.endswith(".exe")) or (not is_windows and "linux" in name.lower()):
                    download_url = asset.get("browser_download_url"); break
            
            if not download_url:
                print("[-] Could not isolate matching pre-compiled distribution bundle."); return

            print(f"[*] Downloading {latest} binary upgrade...")
            with urllib.request.urlopen(download_url) as stream:
                with open(local_binary_name, "wb") as f: f.write(stream.read())
            print("[+] Success: Upgrade complete! Restart application daemon to load.")
    except Exception as e:
        print(f"[-] Manual upgrade block failed: {e}")

def load_config_file(filepath):
    args_list = []
    if not os.path.exists(filepath): return args_list
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if val:
                    args_list.append(f"--{key}")
                    if val.lower() != "true": args_list.append(val)
    return args_list

def save_config_file(filepath, args_namespace):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Project Saver {VERSION} Configuration Profile\n")
            f.write(f"export-folder={args_namespace.export_folder}\n")
            f.write(f"export-format={args_namespace.export_format}\n")
            f.write(f"export-type={args_namespace.export_type}\n")
            f.write(f"remote-address={args_namespace.remote_address}\n")
            f.write(f"chosen-editor={args_namespace.chosen_editor}\n")
            if args_namespace.auto is not None: f.write(f"auto={args_namespace.auto}\n")
        print(f"[+] Active configuration written to profile: {filepath}")
    except Exception as e:
        print(f"[-] Could not export configuration profile: {e}")

def run_server():
    set_terminal_title("Project Saver", VERSION, "Server Running")
    
    # Launches the silent background check thread for new GitHub releases
    threading.Thread(target=check_for_updates_silently, daemon=True).start()

    server_address = ('', PORT)
    httpd = HTTPServer(server_address, RestApiHandler)
    
    # ─── THE INTEGRATED DAEMON STATUS readout BLOCK ───
    startup_log = [
        f"Server Listening:    http://localhost:{PORT}",
        f"Security Token:      {EXPECTED_TOKEN}",
		"---",
        f"📂 Target Folder:    {CLI_ARGS.export_folder or 'Default Environment Root'}",
        f"⚙️  Profile Mode:    {CLI_ARGS.export_type.upper()}",
        f"🗒️  Formats Enabled: {CLI_ARGS.export_format.upper()}",
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
    parser = argparse.ArgumentParser(description="Project Saver Server.")
    parser.add_argument("--export-folder", default="", help="Target base folder path where files will be written.")
    parser.add_argument("--export-format", default="markdown", help="Comma-separated dumping targets: markdown, html, pdf.")
    parser.add_argument("--export-type", default="auto", choices=["auto", "code", "web"], help="Parsing layout configuration profile strategy.")
    parser.add_argument("--remote-address", default="", help="Turns runtime engine into proxy router.")
    parser.add_argument("--auto", type=int, nargs='?', const=5, default=None, help="Enables automated execution timeout duration.")
    parser.add_argument("--config", default="", help="Load options from a custom configuration text file.")
    parser.add_argument("--config-save", default="", help="Save setup flags into configuration profile text file.")
    parser.add_argument("--about", action="store_true", help="Displays developer credits and exit.")
    parser.add_argument("--update", action="store_true", help="Queries GitHub downloads update binary and exit.")
    parser.add_argument("--chosen-editor", default="system_default", choices=["system_default", "obsidian", "vscode", "marktext"], help="Preferred markdown viewer/editor launcher link tool.")

    temp_args = sys.argv[1:]
    loaded_file_args = []
    if "--config" in temp_args:
        try:
            c_idx = temp_args.index("--config")
            loaded_file_args = load_config_file(temp_args[c_idx + 1])
        except IndexError: pass

    combined_args = loaded_file_args + temp_args
    CLI_ARGS = parser.parse_args(combined_args)

    if CLI_ARGS.about:
        about_data = [
            f"Project Saver {VERSION} - Local & Remote Web Scraping Daemon",
            "---",
            "🛠️ Developer: Gunther Voet",
            "📜 License: Open Source (MIT License)",
            "🌐 Repository: https://github.com/gowildchild/Project-Saver/",
            "---",
            "Designed to cleanly archive browser sessions, code repositories",
            "and web documentation directly into structured Markdown files,",
            "raw backups, or professional PDF layouts."
        ]
        render_better_box(about_data, title_str="About \"Project Saver\"", box_width_override=70)
        sys.exit(0)

    if CLI_ARGS.update:
        check_and_perform_update(); sys.exit(0)

    if CLI_ARGS.config_save:
        save_config_file(CLI_ARGS.config_save, CLI_ARGS); sys.exit(0)

    # ─── TRIGGER DYNAMIC SECURITY ENGINE ───
    # Dynamically reads the active configuration filename or falls back to your local file profile
    active_cfg_profile = CLI_ARGS.config if CLI_ARGS.config else "project_saver.cfg"
    resolve_or_create_security_token(active_cfg_profile)

    run_server()
