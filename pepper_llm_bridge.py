#!/usr/bin/env python
# -*- coding: utf-8 -*-
import qi
import argparse
import time
import threading
import socket
import json

class PepperLLMBridge(object):
    def __init__(self, session, llm_host, llm_port):
        self.session = session
        self.asr = session.service("ALSpeechRecognition")
        self.memory = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.llm_host = llm_host
        self.llm_port = llm_port

        # Configuration ASR - définir quelques mots pour activer la reconnaissance
        vocabulary = ["bonjour", "salut", "comment", "tu", "vas", "merci", "au", "revoir", 
                     "quel", "temps", "fait", "il", "que", "peux", "faire", "pour", "moi"]
        self.asr.setLanguage("French")
        self.asr.setVocabulary(vocabulary, True)  # word spotting activé
        self.asr.subscribe("PepperBridge")

        # Socket UDP pour réception LLM
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(("0.0.0.0", 8889))

        # Socket UDP pour envoi LLM  
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.is_running = False
        self.last_words = []

    def start(self):
        self.is_running = True
        
        # Thread pour recevoir réponses LLM
        t = threading.Thread(target=self._recv_loop)
        t.daemon = True
        t.start()
        
        # Thread pour surveiller WordRecognized
        t2 = threading.Thread(target=self._word_monitor)
        t2.daemon = True
        t2.start()
        
        print("✅ Bridge ASR→LLM démarré")

    def _word_monitor(self):
        while self.is_running:
            try:
                current = self.memory.getData("WordRecognized")
                if current and len(current) >= 2 and current[1] > 0.5:
                    # Nouveau mot détecté si différent du précédent
                    if current != self.last_words:
                        word = current[0].strip()
                        confidence = current[1]
                        print("📤 Mot reconnu: '{}' ({:.2f})".format(word, confidence))
                        
                        # Envoi au LLM
                        msg = {
                            "type": "conversation_end",
                            "timestamp": time.time(),
                            "conversation_text": word
                        }
                        self.send_sock.sendto(
                            json.dumps(msg).encode("utf-8"),
                            (self.llm_host, self.llm_port)
                        )
                        self.last_words = current
                        
                time.sleep(0.1)
            except Exception as e:
                print("❌ Erreur word monitor:", e)
                time.sleep(0.5)

    def _recv_loop(self):
        while self.is_running:
            try:
                data, _ = self.recv_sock.recvfrom(8192)
                msg = json.loads(data.decode("utf-8"))
                if msg.get("type") == "llm_response":
                    text = msg.get("text", "").strip()
                    if text:
                        print("🗣️ LLM→Pepper:", text)
                        self.tts.say(text)
            except Exception as e:
                print("❌ Erreur reception:", e)
                time.sleep(0.1)

    def stop(self):
        self.is_running = False
        try:
            self.asr.unsubscribe("PepperBridge")
        except:
            pass
        self.recv_sock.close()
        self.send_sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--llm_host", required=True)
    parser.add_argument("--llm_port", type=int, default=8888)
    args = parser.parse_args()

    session = qi.Session()
    session.connect(args.ip)

    bridge = PepperLLMBridge(session, args.llm_host, args.llm_port)
    try:
        bridge.start()
        print("🎤 En attente de la parole...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()
