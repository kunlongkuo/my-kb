#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Start a local web server for mobile phone access and show QR code."""

import http.server
import socketserver
import socket
import webbrowser
import urllib.parse
import sys

PORT = 8000

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def main():
    ip = get_local_ip()
    if ip == '127.0.0.1':
        print("警告: 無法偵測到區域網路 IP，手機可能無法連線。")
        print("請確保電腦已連線至 Wi-Fi 或有線網路。")
        print("-" * 50)
    
    # URL encoded paths
    path_trend = "wiki/金融投資/主動型ETF持股分析.html"
    path_rank = "wiki/金融投資/主動型ETF個股加減碼排行.html"
    
    url_trend = f"http://{ip}:{PORT}/{path_trend}"
    url_rank = f"http://{ip}:{PORT}/{path_rank}"
    
    print("\n🚀 區域網路 Web 伺服器啟動中...")
    print(f"💻 電腦端本機網址 (Local):")
    print(f"   - 個股持股分析: http://localhost:{PORT}/{path_trend}")
    print(f"   - 個股加減碼排行: http://localhost:{PORT}/{path_rank}")
    print("-" * 50)
    print(f"📱 手機端連線網址 (請確保手機與電腦連接在同一個 Wi-Fi 網路下):")
    print(f"   - 個股持股分析: \033[1;36m{url_trend}\033[0m")
    print(f"   - 個股加減碼排行: \033[1;36m{url_rank}\033[0m")
    print("-" * 50)
    
    # Generate QR Code URL via free API and open in computer browser
    qr_data = urllib.parse.quote(url_trend)
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}"
    
    print("🔮 正在電腦瀏覽器開啟 QR Code...")
    print("   請用手機相機或 LINE 掃描該 QR Code，即可直接在手機上開啟儀表板！")
    print("-" * 50)
    
    try:
        webbrowser.open(qr_api_url)
    except Exception as e:
        print(f"無法自動開啟瀏覽器，請手動複製網址或至瀏覽器輸入網址：{url_trend}")
    
    # Start the server
    handler = http.server.SimpleHTTPRequestHandler
    
    # Allow loose binding (re-use address)
    class TCPServerReusable(socketserver.TCPServer):
        allow_reuse_address = True
        
    try:
        with TCPServerReusable(("", PORT), handler) as httpd:
            print(f"📡 伺服器正在運行於 Port {PORT}... 按 Ctrl+C 可停止伺服器。")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 伺服器已停止。")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 啟動伺服器失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
