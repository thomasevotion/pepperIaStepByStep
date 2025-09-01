import socket
import json
import threading
import time
import requests
import re

class OptimizedGemma2Server(object):
    def __init__(self, port=8888, pepper_port=8889):
        self.port = port
        self.pepper_port = pepper_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pepper_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.is_running = False
        
        # Configuration Ollama optimisée
        self.ollama_url = "http://192.168.1.17:11434/api/generate"
        self.model_name = "gemma2:9b"
        
        # Buffer conversation
        self.current_conversation = []
        self.conversation_active = False
        
        # Optimisations conversationnelles
        self.conversation_context = []
        self.max_context_length = 8

    def start_server(self):
        try:
            self.sock.bind(('0.0.0.0', self.port))
            self.is_running = True

            print(f"🧠 SERVEUR GEMMA2:9B ULTRA-OPTIMISÉ")
            print(f"📡 Réception Pepper: port {self.port}")
            print(f"🚀 Ollama Gemma2:9B sur RTX 4070")
            print(f"⚡ Réponses conversationnelles ultra-rapides")

            # Vérification Ollama
            self.check_ollama_status()

            self.receiver_thread = threading.Thread(target=self.receive_voice_data)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()

        except Exception as e:
            print(f"❌ Erreur démarrage: {e}")

    def check_ollama_status(self):
        """Vérification qu'Ollama et Gemma2 sont prêts"""
        try:
            print(f"🔎 Test de connexion à Ollama : {self.ollama_url}")
            response = requests.post(self.ollama_url, json={
                "model": self.model_name,
                "prompt": "Bonjour",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 50
                }
            }, timeout=10)

            print(f"Réponse connexion Ollama HTTP Code : {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Gemma2:9B prêt et optimisé\nRéponse : {response.json()}")
            else:
                print(f"⚠️  Problème Ollama: {response.status_code} {response.text}")

        except Exception as e:
            print(f"❌ Ollama non accessible: {e}")
            print("💡 Lancez: ollama serve")

    def receive_voice_data(self):
        while self.is_running:
            try:
                data, addr = self.sock.recvfrom(4096)
                print(f"\n📥 Reçu UDP depuis {addr} : {data!r}")
                voice_data = json.loads(data.decode('utf-8'))
                print(f"➡️ Données reçues : {voice_data}")
                self.process_voice_data(voice_data, addr)
            except Exception as e:
                print(f"❌ Erreur réception : {e}")

    def process_voice_data(self, voice_data, sender_addr):
        try:
            msg_type = voice_data.get('type')
            print(f"🔎 Type de message : {msg_type}")
            
            if msg_type == 'conversation_start':
                self.conversation_active = True
                self.current_conversation = []
                print(f"🎤 NOUVELLE CONVERSATION")
                
            elif msg_type == 'speech_chunk' and self.conversation_active:
                self.current_conversation.append(voice_data)
                words = voice_data.get('words')
                print(f"📝 Chunk reçu: {words}")
                
            elif msg_type == 'conversation_end':
                print(f"✅ TRAITEMENT GEMMA2:9B (fin de phrase détectée)")
                
                # Log les données reçues pour debug
                print(f"--- Données conversation complète :")
                print(json.dumps(self.current_conversation, indent=2, ensure_ascii=False))
                print(f"--- conversation_text (direct) reçu: {voice_data.get('conversation_text', '<absent>')}")
                
                # Ajout immédiat du texte si fourni par le message direct
                if 'conversation_text' in voice_data:
                    self.current_conversation.append(voice_data)
                
                if self.current_conversation:
                    llm_response = self.process_with_gemma2()
                    self.send_response_to_pepper(llm_response, sender_addr[0])
                self.conversation_active = False
                
        except Exception as e:
            print(f"❌ Erreur traitement : {e}")

    def process_with_gemma2(self):
        """Traitement ultra-optimisé avec Gemma2:9B"""
        try:
            # Extraire le texte, supporte conversation_text direct
            if self.current_conversation and isinstance(self.current_conversation[-1], dict) and 'conversation_text' in self.current_conversation[-1]:
                conversation_text = self.current_conversation[-1]['conversation_text']
            else:
                # fallback mots chunks si jamais utile
                detected_words = []
                for chunk in self.current_conversation:
                    words = chunk.get('words')
                    if words and isinstance(words, str):
                        detected_words.append(words)
                conversation_text = " ".join(detected_words).strip()
            
            print(f"🧠 GEMMA2 PROMPT envoyé : '{conversation_text}'")

            if not conversation_text.strip():
                print("🚨 conversation_text vide, envoi réponse défaut")
                return "Je n'ai pas bien compris. Pouvez-vous répéter ?"

            system_prompt = (
                "Tu es un assistant professionnel dans un événement. "
                "Réponds de manière concise, claire et professionnelle. "
                "Maximum 2 phrases courtes. Sois naturel et aidant."
            )

            context = ""
            if self.conversation_context:
                context = "\n".join([f"H: {h}\nA: {a}" for h, a in self.conversation_context[-3:]])
                context = f"\nContexte récent:\n{context}\n"

            full_prompt = (
                f"{system_prompt}{context}\n"
                f"Humain: {conversation_text}\n"
                f"Assistant:"
            )

            print(f"🧠 PROMPT FINAL:\n{full_prompt}\n")

            # Appel à Ollama
            start_time = time.time()
            response = requests.post(self.ollama_url, json={
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_ctx": 4096,
                    "num_predict": 100,
                    "stop": ["Humain:", "H:"]
                }
            }, timeout=30)

            processing_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                print(f"🧠 Réponse RAW Ollama JSON:\n{result}\n")
                gemma_response = result.get('response', '').strip()
                gemma_response = self.clean_response(gemma_response)
                self.conversation_context.append((conversation_text, gemma_response))
                if len(self.conversation_context) > self.max_context_length:
                    self.conversation_context.pop(0)
                print(f"⚡ GEMMA2 RÉPOND ({processing_time:.2f}s): '{gemma_response}'")
                return gemma_response
            else:
                print(f"❌ Erreur Ollama: {response.status_code} {response.text}")
                return "Je rencontre un problème technique. Pouvez-vous réessayer ?"

        except requests.Timeout:
            print("⏱️ Timeout Ollama !")
            return "Désolé, je réfléchis trop lentement. Pouvez-vous répéter ?"
        except Exception as e:
            print(f"❌ Erreur Gemma2: {e}")
            return "Je n'ai pas pu traiter votre demande. Reformulez s'il vous plaît."

    def clean_response(self, response):
        response = re.sub(r'^(Assistant|A):\s*', '', response)
        response = re.sub(r'^(Réponse|Response):\s*', '', response)
        response = response.replace('*', '').replace('#', '')
        sentences = response.split('. ')
        if len(sentences) > 2:
            response = '. '.join(sentences[:2]) + '.'
        return response.strip()

    def send_response_to_pepper(self, llm_response, pepper_ip):
        try:
            response_data = {
                'type': 'llm_response',
                'text': llm_response,
                'timestamp': time.time(),
                'model': 'gemma2:9b'
            }
            json_data = json.dumps(response_data, ensure_ascii=False)
            payload = json_data.encode('utf-8')
            
            # ✅ CORRECTION : Envoie vers WSL, pas vers Pepper physique
            wsl_ip = "172.25.227.111"  # Ton IP WSL
            print(f"🟢 Envoi réponse LLM à {wsl_ip}:{self.pepper_port} (WSL)")
            self.pepper_sock.sendto(payload, (wsl_ip, self.pepper_port))
            
        except Exception as e:
            print(f"❌ Erreur envoi: {e}")

    def stop_server(self):
        self.is_running = False
        self.sock.close()
        self.pepper_sock.close()
        print("🛑 Serveur Gemma2 arrêté")

if __name__ == "__main__":
    print("🚀 SERVEUR GEMMA2:9B ULTRA-OPTIMISÉ")
    print("   ⚡ RTX 4070 + i9 = Conversations ultra-rapides")
    print("   🎯 Spécialisé événementiel professionnel")
    print("   🧠 Gemma2:9B > Llama 3.1 8B pour conversations")
    
    server = OptimizedGemma2Server()
    
    try:
        server.start_server()
        print("\n✅ Gemma2:9B prêt pour conversations professionnelles!")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt Gemma2...")
    finally:
        server.stop_server()
