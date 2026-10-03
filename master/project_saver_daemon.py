import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.parser import BytesParser
from bs4 import BeautifulSoup

# Import our shared system modules natively
from . import project_saver_ui
from . import project_saver_config
from project_saver_archive import process_html_content

# Module-level variables populated during instantiation
VERSION = ""
PORT = 19763
CLI_ARGS = None
LATEST_AVAILABLE_VERSION = None
execute_interactive_dashboard_monitor = None

class RestApiHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        auth_header = self.headers.get('Authorization', '')
        token = auth_header.replace("Bearer ", "").strip() if auth_header else ""
        
        # * [FIXED] References the token parameter securely out of project_saver_config
        if token != project_saver_config.EXPECTED_TOKEN:
            alert_log = [
                "⚠️  SECURITY ALERT: Unauthorized Request Blocked!",
                "---",
                f"Source IP Network: {self.client_address[0]}",
                "Reason: Transmission Authorization Token Mismatch.",
                f"Token: {token} Expected: {project_saver_config.EXPECTED_TOKEN}",
            ]
            project_saver_ui.render_better_box(alert_log, title_str="Security Warning", box_width_override=70)
            self.send_response(401)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length)
        cli_dict = vars(CLI_ARGS)

        # 1. CLIENT-SIDE RELAY FORWARDER SYSTEM
        # * [FIXED] Updated to look up the correct underscore keys dynamically from argparse
        if cli_dict.get("remote_address"):
            print(f"[*] Relaying capture payload to remote destination server: {cli_dict['remote_address']}")
            try:
                req = urllib.request.Request(cli_dict["remote_address"], data=body_bytes, headers=dict(self.headers))
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
        
        intercept_log = [
            f"📄 Title: {page_title if len(page_title) <= 84 else f'{page_title[:84]}..'}",
            f"🌐 Origin: {page_url if len(page_url) <= 84 else f'{page_url[:84]}..'}"
        ]
        
        print() 
        project_saver_ui.render_better_box(intercept_log, title_str="\033[93mNetwork Interception Notice\033[0m", box_width_override=86)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "saved"}')
        self.wfile.flush()

        # FIXED: Processes parameters with full underscore notation compatibility
        process_html_content(
            html_string=html_content, 
            page_title=page_title, 
            source_origin=page_url,
            export_folder=cli_dict.get("export_folder"),
            export_format=cli_dict.get("export_format"),
            export_type=cli_dict.get("export_type"),
            auto_timeout=CLI_ARGS.auto,
            editor_override=cli_dict.get("chosen_editor"),
            app_version=VERSION
        )


def check_for_updates_silently():
    """Safety placeholder to resolve historic background loop definitions."""
    pass


def run_server():
    """Starts the terminal titles, parses version saving matrices, and executes network tracking loops."""
    project_saver_ui.set_terminal_title("Project Saver", VERSION, "Server Running")
    
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, RestApiHandler)
    
    cli_dict = vars(CLI_ARGS)

    # * [FIXED] References project_saver_config to write out settings accurately and clears out tab spaces
    if LATEST_AVAILABLE_VERSION and LATEST_AVAILABLE_VERSION != VERSION:
        project_saver_config.save_config_file("project_saver.cfg", CLI_ARGS, VERSION, LATEST_AVAILABLE_VERSION) 
        
    project_saver_ui.refresh_dashboard_view(cli_dict, VERSION, PORT)
    execute_interactive_dashboard_monitor(httpd)
