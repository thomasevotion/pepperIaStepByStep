import socket, json, threading, time, requests, re, os

class UltraFastPhi3Server:
    def __init__(self, port=8888, pepper_port=8889):
        self.port = port
        self.pepper_port = pepper_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pepper_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ollama_url = "http://192.168.1.17:11434/api/generate"
        self.model = "phi3:mini"
        self.context = []
        self.max_ctx = 1

    def start_server(self):
        self.sock.bind(('0.0.0.0', self.port))
        print(f"🚀 SERVEUR PHI3:MINI ULTRA-RAPIDE")
        print(f"📡 Port: {self.port} | Cible: ~1s par réponse")
        print(f"⚡ Streaming + optimisations GPU + filtrage intelligent")
        
        # Warm-up intensif
        self.warm_up_model()
        
        threading.Thread(target=self._recv, daemon=True).start()

    def warm_up_model(self):
        """Warm-up agressif pour charger Phi3 en GPU"""
        try:
            print(f"🔥 Warm-up intensif Phi3:mini...")
            for i in range(3):
                requests.post(self.ollama_url, json={
                    "model": self.model,
                    "prompt": f"Test {i+1}",
                    "stream": False,
                    "options": {"num_predict": 1}
                }, timeout=20)
            print("✅ Phi3:mini chargé et optimisé en GPU")
        except Exception as e:
            print(f"❌ Erreur warm-up: {e}")

    def _recv(self):
        while True:
            data, addr = self.sock.recvfrom(4096)
            msg = json.loads(data.decode('utf-8'))
            if msg.get("type") == "conversation_end":
                prompt = msg["conversation_text"].strip()
                print(f"📨 Prompt: '{prompt}'")
                resp = self._generate_ultra_fast(prompt)
                self._send(resp)

    def _generate_ultra_fast(self, prompt):
        """Génération ultra-optimisée avec filtrage intelligent"""
        
        # ✅ VÉRIFICATION PROMPT VIDE EN PREMIER
        if not prompt or len(prompt.strip()) < 2:
            print(f"⚠️ Prompt vide ou trop court : '{prompt}' - ignoré")
            return "Pouvez-vous répéter s'il vous plaît ?"
        
        # ✅ FILTRAGE AVANCÉ DES PROMPTS PARASITES
        forbidden_words = ["nao", "naoh", "now", "no", "a", "à", "ah", "oh", "hum", "euh"]
        words = prompt.lower().split()
        if len(words) == 1 and words[0] in forbidden_words:
            print(f"⚠️ Mot parasite détecté : '{prompt}' - ignoré")
            return "Je vous écoute, que puis-je faire pour vous ?"
        
        # Prompt ultra-minimal
        sys_msg = """Tu es Pepper, robot événementiel d'Evotion (société lyonnaise). Réponds en 1 phrase courte et directe. Tu ne connais pas la météo ni l'heure."""
        
        # Construction prompt minimal
        full = f"{sys_msg}\nQ: {prompt}\nR:"
        
        start = time.time()
        try:
            resp = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": full,
                    "stream": True,
                    "options": {
                        "temperature": 0.3,     # Déterministe
                        "top_p": 0.7,          # Focalisé
                        "top_k": 20,           # Rapide
                        "repeat_penalty": 1.0,
                        "num_predict": 20,      # Court
                        "num_ctx": 512,         # Contexte minimal
                        "stop": ["Q:", "Humain:", "\n\n", "R:"]
                    }
                },
                stream=True, timeout=30
            )
            
            # Streaming ultra-rapide
            answer = ""
            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    answer += chunk.get("response", "")
            
            # Nettoyage amélioré
            answer = re.sub(r'^(R|Réponse|Assistant):\s*', '', answer).strip()
            
            # Éviter les réponses vides ou parasites
            if not answer or answer in [".", "!", "?", "...", ""] or len(answer) < 3:
                answer = "Je suis là pour vous aider."
            
            # Assurer ponctuation finale
            if answer and not answer[-1] in '.!?':
                answer += '.'
                
            dt = time.time() - start
            print(f"⚡ PHI3 ({dt:.2f}s): '{answer}'")
            
            return answer
            
        except Exception as e:
            print(f"❌ Erreur génération: {e}")
            return "Désolé, problème technique. Pouvez-vous répéter ?"

    def _send(self, text):
        msg = json.dumps({
            "type": "llm_response", 
            "text": text,
            "model": "phi3:mini"
        }, ensure_ascii=False).encode('utf-8')
        
        wsl_ip = "172.25.227.111"
        print(f"📤 → {wsl_ip}:{self.pepper_port}")
        self.pepper_sock.sendto(msg, (wsl_ip, self.pepper_port))

    def stop_server(self):
        self.sock.close()
        self.pepper_sock.close()

if __name__ == "__main__":
    # Optimisations GPU maximales
    os.environ["OLLAMA_FLASH_ATTENTION"] = "1"
    os.environ["OLLAMA_KV_CACHE_TYPE"] = "q4_0"
    os.environ["OLLAMA_NUM_PARALLEL"] = "1"
    
    print("🚀 PHI3:MINI ULTRA-RAPIDE SERVER")
    print("   ⚡ Cible: <2s après warm-up")
    print("   🎯 20 tokens max par réponse")
    print("   🛡️ Filtrage intelligent des parasites")
    
    server = UltraFastPhi3Server()
    
    try:
        server.start_server()
        print("\n✅ Phi3:mini prêt - vitesse maximale + filtrage!")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt serveur ultra-rapide")
        server.stop_server()
