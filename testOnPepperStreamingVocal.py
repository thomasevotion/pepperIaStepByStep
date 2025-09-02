import qi
import argparse
import time
import numpy as np
import threading
import socket
import json


class VoiceToLLM(object):
    def __init__(self, session, llm_host="127.0.0.1", llm_port=8888):
        self.session = session
        self.memory = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.is_running = False

        # Pour LLM
        self.llm_host = llm_host
        self.llm_port = llm_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Socket pour recevoir les réponses LLM
        self.response_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.response_port = 8889
        
        # Prise de parole
        self.last_speech_state = 0
        self.words_buffer = []
        self.recording = False
        self.speech_start_time = 0
        self.silence_timeout = 1.5  # AUGMENTÉ pour éviter les coupures

    def start_detection(self):
        print("✅ Démarrage détection vocale + envoi LLM")
        
        # Bind du port pour recevoir les réponses
        self.response_sock.bind(('0.0.0.0', self.response_port))
        
        self.is_running = True
        
        # Thread monitoring vocal
        self.monitoring_thread = threading.Thread(target=self.monitor_audio_activity)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        # Thread pour recevoir les réponses LLM
        self.response_thread = threading.Thread(target=self.receive_llm_responses)
        self.response_thread.daemon = True
        self.response_thread.start()
        
        print("📡 Monitoring audio + streaming LLM + réception réponses actifs...")

    def monitor_audio_activity(self):
        while self.is_running:
            try:
                current_time = time.time()
                speech_detected = self.memory.getData("SpeechDetected")
                
                if speech_detected == 1 and not self.recording:
                    print(f"🗣️ PAROLE DÉTECTÉE! (Timestamp: {current_time:.2f})")
                    self.words_buffer = []
                    self.speech_start_time = current_time
                    self.recording = True

                # Pendant la parole
                if self.recording:
                    word_recognized = self.memory.getData("WordRecognized")
                    if (word_recognized and len(word_recognized) >= 2):
                        word = word_recognized[0].strip()
                        confidence = word_recognized[1]
                        if word and confidence > 0.4:
                            print(f"💬 MOT RECONNU: '{word}' (confiance: {confidence:.2f})")
                            # Ajoute au buffer tous les NEW mots (évite répétition immédiate)
                            if not self.words_buffer or word != self.words_buffer[-1][0]:
                                self.words_buffer.append((word, confidence))

                # Fin de parole (silence)
                if speech_detected == 0 and self.recording:
                    if (current_time - self.speech_start_time > self.silence_timeout):
                        self.send_to_llm()
                        self.recording = False

                time.sleep(0.05)
            except Exception as e:
                print(f"❌ Erreur monitoring: {e}")
                time.sleep(0.2)

    def send_to_llm(self):
        if not self.words_buffer:
            print("⏭️ Aucun mot à envoyer au LLM.")
            return

        # Assemble phrase à partir des mots confidence > 0.5
        phrase = " ".join([w[0] for w in self.words_buffer if w[1] > 0.5])
        
        # ✅ FILTRAGE DES MOTS PARASITES
        filtered_words = []
        for word in phrase.split():
            if word.lower() not in ["nao", "naoh", "now", "no", "a", "à", "ah", "oh"]:
                filtered_words.append(word)
        
        phrase = " ".join(filtered_words).strip()
        
        # ✅ ÉVITER L'ENVOI DE PHRASES VIDES OU TROP COURTES
        if len(phrase) < 3:
            print(f"⏭️ Phrase trop courte ou vide : '{phrase}' - ignorée")
            return
            
        print(f"✅ PHRASE CAPTÉE : '{phrase}'")
        msg = {
            "type": "conversation_end",
            "timestamp": time.time(),
            "conversation_text": phrase
        }
        try:
            print(f"📤 Envoi UDP LLM : {self.llm_host}:{self.llm_port} -> '{phrase}'")
            self.sock.sendto(json.dumps(msg, ensure_ascii=False).encode("utf-8"), (self.llm_host, self.llm_port))
        except Exception as e:
            print(f"❌ Erreur envoi LLM : {e}")

    def receive_llm_responses(self):
        """Écoute les réponses du LLM et les fait parler par Pepper"""
        while self.is_running:
            try:
                data, addr = self.response_sock.recvfrom(4096)
                response_data = json.loads(data.decode('utf-8'))
                
                if response_data.get('type') == 'llm_response':
                    llm_text = response_data.get('text', '')
                    if llm_text:
                        print(f"🧠➡️🗣️ PEPPER PARLE: {llm_text}")
                        self.tts.say(llm_text)
                        
            except Exception as e:
                print(f"❌ Erreur réception réponse LLM: {e}")
                time.sleep(0.1)

    def stop_detection(self):
        self.is_running = False
        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join(timeout=2)
        if hasattr(self, 'response_thread'):
            self.response_thread.join(timeout=2)
        self.sock.close()
        self.response_sock.close()
        print("🛑 Détection et streaming arrêtés")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, required=True)
    parser.add_argument("--port", type=int, default=9559)
    parser.add_argument("--llm_host", default="127.0.0.1")
    parser.add_argument("--llm_port", type=int, default=8888)
    args = parser.parse_args()

    connection_url = f"tcp://{args.ip}:{args.port}"
    app = qi.Application(['VoiceToLLM', '--qi-url=' + connection_url])
    app.start()
    session = app.session

    # 1. Active la vie autonome (posture, regard, awareness)
    try:
        autonomy = session.service("ALAutonomousLife")
        autonomy.setState("solitary")
        print("🤖 ALAutonomousLife en mode solitary (debout, regard, awareness)")
    except Exception as e:
        print(f"⚠️ Impossible de configurer ALAutonomousLife: {e}")

    # 2. Stoppe tous les comportements autonomes (dont le smalltalk)
    try:
        bm = session.service("ALBehaviorManager")
        behaviors = bm.getRunningBehaviors()
        for behavior in behaviors:
            bm.stopBehavior(behavior)
        print(f"🛑 {len(behaviors)} comportements autonomes stoppés (smalltalk inclus)")
    except Exception as e:
        print(f"⚠️ Impossible d'arrêter les comportements autonomes: {e}")

    print("🤖 Détecteur vocal + Streaming LLM événementiel")
    detector = VoiceToLLM(session, llm_host=args.llm_host, llm_port=args.llm_port)
    try:
        detector.start_detection()
        print("\n🎤 Parlez à Pepper, le LLM répondra dès la fin !")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé...")
    finally:
        detector.stop_detection()
