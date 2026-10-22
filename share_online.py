"""
Instant Public Cloud Tunnel Launcher
Exposes the local Smart Warehouse web server to the public internet using Cloudflare Tunnel.
Bypasses Windows Firewall and University/College Wi-Fi AP Client Isolation.
Works on any phone, tablet, or laptop on mobile 4G/5G or any Wi-Fi.
"""

import os
import re
import sys
import subprocess
import time


import os
import re
import sys
import subprocess
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def main():
    print("=" * 75)
    print("  [ONLINE] STARTING INSTANT PUBLIC CLOUD TUNNEL (CLOUDFLARE)")
    print("=" * 75)
    print("  Connecting local warehouse server (http://localhost:5000) to public cloud...")

    exe_path = os.path.join(os.path.dirname(__file__), "cloudflared.exe")
    if not os.path.exists(exe_path):
        print(f"Error: {exe_path} not found.")
        sys.exit(1)

    cmd = [exe_path, "tunnel", "--url", "http://127.0.0.1:5000"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    tunnel_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com")

    for line in proc.stdout:
        match = url_pattern.search(line)
        if match:
            tunnel_url = match.group(0)
            break

    if tunnel_url:
        print()
        print("*" * 75)
        print("  >>> YOUR SMART WAREHOUSE IS NOW LIVE GLOBALLY! <<<")
        print("*" * 75)
        print()
        print("  OPEN THIS LINK ON YOUR MOBILE PHONE OR 2ND LAPTOP:")
        print(f"     >>>  {tunnel_url}  <<<")
        print()
        print("  [OK] Works on Mobile Data (4G/5G) or Any Wi-Fi")
        print("  [OK] No Firewall Configuration or Router Setup Needed")
        print("  [OK] Real-Time Synchronized with your Laptop")
        print("*" * 75)
        print("  Keep this window open while using the application.")
        print("  Press Ctrl+C to close the tunnel.")
        print("*" * 75)
        print()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down cloud tunnel...")
            proc.terminate()
    else:
        print("Failed to detect tunnel URL. Output:")
        print(proc.stdout.read())


if __name__ == "__main__":
    main()
