import socket
import json
import threading
import time
import requests
import re
import os


class OptimizedGemma2Server(object):
    def __init__(self, port=8888, pepper_port=8889):
        self.port = port
        self.pepper_port = pepper_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pepper_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.is_running = False
        
        # Configuration Ollama ultra-optimisée
        self.ollama_url = "http://192.168.1.17:11434/api/generate"
        self.model_name = "gemma2:9b"
        
        # Buffer conversation
        self.current_conversation = []
        self.conversation_active = False
        
        # Optimisations conversationnelles - RÉDUIT
        self.conversation_context = []
        self.max_context_length = 2  # Réduit de 8 à 2


    def start_server(self):
        try:
            self.sock.bind(('0.0.0.0', self.port))
            self.is_running = True

            print(f"🧠 SERVEUR GEMMA2:9B ULTRA-OPTIMISÉ")
            print(f"📡 Réception Pepper: port {self.port}")
            print(f"🚀 Ollama Gemma2:9B sur RTX 4070")
            print(f"⚡ Streaming + optimisations GPU activées")

            # Warm-up et vérification Ollama
            self.check_ollama_status()

            self.receiver_thread = threading.Thread(target=self.receive_voice_data)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()

        except Exception as e:
            print(f"❌ Erreur démarrage: {e}")


    def check_ollama_status(self):
        """Warm-up du modèle + vérification"""
        try:
            print(f"🔥 Warm-up Gemma2:9B...")
            # Requête de warm-up pour charger le modèle en GPU
            response = requests.post(self.ollama_url, json={
                "model": self.model_name,
                "prompt": "Hi",
                "stream": False,
                "options": {"num_predict": 1}
            }, timeout=15)

            print(f"Réponse warm-up HTTP Code : {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Gemma2:9B chargé et optimisé en GPU")
            else:
                print(f"⚠️  Problème warm-up: {response.status_code} {response.text}")

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
        """Traitement STREAMING ultra-optimisé avec Gemma2:9B"""
        try:
            # Extraire le texte
            if self.current_conversation and isinstance(self.current_conversation[-1], dict) and 'conversation_text' in self.current_conversation[-1]:
                conversation_text = self.current_conversation[-1]['conversation_text']
            else:
                detected_words = []
                for chunk in self.current_conversation:
                    words = chunk.get('words')
                    if words and isinstance(words, str):
                        detected_words.append(words)
                conversation_text = " ".join(detected_words).strip()
            
            print(f"🧠 GEMMA2 PROMPT envoyé : '{conversation_text}'")

            if not conversation_text.strip():
                return "Je n'ai pas bien compris. Pouvez-vous répéter ?"

            # Prompt ultra-concis
            system_prompt = "Assistant pro événementiel. 1 phrase max, direct."
            
            # Context ultra-réduit (1 seul échange précédent)
            context = ""
            if self.conversation_context:
                h, a = self.conversation_context[-1]  # SEULEMENT LE DERNIER
                context = f"\nDernier échange:\nH: {h}\nA: {a}\n"

            full_prompt = f"{system_prompt}{context}\nHumain: {conversation_text}\nAssistant:"
            print(f"🧠 PROMPT FINAL:\n{full_prompt}\n")

            # Appel à Ollama EN STREAMING
            start_time = time.time()
            response = requests.post(self.ollama_url, json={
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": True,  # STREAMING ACTIVÉ
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_predict": 35,     # RÉDUIT À 35 TOKENS
                    "num_ctx": 2048,       # CONTEXTE RÉDUIT
                    "stop": ["Humain:", "H:", ".", "!"]  # STOP AGRESSIF
                }
            }, timeout=30, stream=True)

            # Lecture streaming ligne par ligne
            gemma_response = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    delta = chunk.get("response", "")
                    gemma_response += delta

            processing_time = time.time() - start_time
            
            # Nettoyage final
            gemma_response = self.clean_response(gemma_response.strip())
            self.conversation_context.append((conversation_text, gemma_response))
            if len(self.conversation_context) > self.max_context_length:
                self.conversation_context.pop(0)
                
            print(f"⚡ GEMMA2 STREAMING ({processing_time:.2f}s): '{gemma_response}'")
            return gemma_response

        except requests.Timeout:
            print("⏱️ Timeout Ollama !")
            return "Désolé, je réfléchis trop lentement."
        except Exception as e:
            print(f"❌ Erreur Gemma2: {e}")
            return "Je n'ai pas pu traiter votre demande."


    def clean_response(self, response):
        response = re.sub(r'^(Assistant|A):\s*', '', response)
        response = re.sub(r'^(Réponse|Response):\s*', '', response)
        response = response.replace('*', '').replace('#', '')
        # Garde seulement la première phrase
        sentences = response.split('. ')
        if sentences:
            response = sentences[0] + '.'
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
            
            wsl_ip = "172.25.227.111"
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
    # Optimisations GPU pour Ollama
    os.environ["OLLAMA_FLASH_ATTENTION"] = "1"
    os.environ["OLLAMA_KV_CACHE_TYPE"] = "q4_0"
    os.environ["OLLAMA_NUM_PARALLEL"] = "1"
    
    print("🚀 SERVEUR GEMMA2:9B ULTRA-OPTIMISÉ")
    print("   ⚡ RTX 4070 + Streaming + GPU optimisé")
    print("   🎯 Réponses < 2.5s après warm-up")
    print("   🧠 Gemma2:9B streaming + cache optimisé")
    
    server = OptimizedGemma2Server()
    
    try:
        server.start_server()
        print("\n✅ Gemma2:9B prêt avec optimisations streaming!")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt Gemma2...")
    finally:
        server.stop_server()
