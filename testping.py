import socket
import json
import time

server_ip = '192.168.1.17'  # ← IP de la machine où tourne gemma2_server.py
port = 8888

msg = {
    "type": "conversation_end",
    "timestamp": time.time(),
    "conversation_text": "Bonjour, peux-tu te présenter s'il te plaît ?"
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(msg, ensure_ascii=False).encode('utf-8'), (server_ip, port))
print("✅ Message envoyé à gemma2_server.py")
