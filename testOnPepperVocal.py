import qi
import argparse
import time
import numpy as np
import threading

class WorkingVoiceDetector(object):
    def __init__(self, session):
        self.session = session
        self.memory = session.service("ALMemory")
        self.is_running = False
        
        # État de détection
        self.last_sound_time = 0
        self.last_speech_state = 0
        self.last_emotion_data = None
        self.sound_activity_count = 0

    def start_detection(self):
        """Démarre la détection avec les vraies clés ALMemory"""
        try:
            print("✅ Démarrage détection vocale avec données réelles")
            
            self.is_running = True
            self.monitoring_thread = threading.Thread(target=self.monitor_audio_activity)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            print("📡 Monitoring audio actif...")
            
        except Exception as e:
            print(f"❌ Erreur démarrage: {e}")

    def monitor_audio_activity(self):
        """Surveille l'activité audio en temps réel"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # 1. Vérifier la détection de parole
                speech_detected = self.memory.getData("SpeechDetected")
                if speech_detected != self.last_speech_state:
                    if speech_detected == 1:
                        print(f"🗣️  PAROLE DÉTECTÉE! (Timestamp: {current_time:.2f})")
                    else:
                        print(f"🔇 Fin de parole détectée")
                    self.last_speech_state = speech_detected
                
                # 2. Analyser la localisation sonore
                sound_located = self.memory.getData("ALSoundLocalization/SoundLocated")
                if sound_located and len(sound_located) >= 2:
                    timestamp = sound_located[0]  # [frame, time_us]
                    position = sound_located[1]   # [x, y, z, confidence]
                    
                    if len(position) >= 4:
                        x, y, z, confidence = position[:4]
                        
                        # Nouveau son détecté si timestamp différent
                        if timestamp != self.last_sound_time and confidence > 0.3:
                            self.last_sound_time = timestamp
                            self.sound_activity_count += 1
                            
                            # Calculer direction approximative
                            angle = np.arctan2(y, x) * 180 / np.pi
                            distance = np.sqrt(x*x + y*y + z*z)
                            
                            print(f"🎵 SON LOCALISÉ: Angle={angle:.1f}°, Distance={distance:.2f}m, Conf={confidence:.2f}")
                
                # 3. Analyser les émotions vocales
                emotion_data = self.memory.getData("ALVoiceEmotionAnalysis/EmotionRecognized")
                if emotion_data != self.last_emotion_data and emotion_data:
                    if len(emotion_data) >= 2:
                        emotion_values = emotion_data[1]  # Liste des valeurs émotionnelles
                        if emotion_values and max(emotion_values) > 0:
                            emotions = ["Neutre", "Joie", "Colère", "Surprise", "Tristesse"]
                            max_emotion_idx = emotion_values.index(max(emotion_values))
                            max_emotion = emotions[max_emotion_idx] if max_emotion_idx < len(emotions) else "Inconnue"
                            confidence_emo = max(emotion_values)
                            
                            print(f"😊 ÉMOTION DÉTECTÉE: {max_emotion} (intensité: {confidence_emo})")
                    
                    self.last_emotion_data = emotion_data
                
                # 4. Vérifier la reconnaissance de mots
                word_recognized = self.memory.getData("WordRecognized")
                if word_recognized and len(word_recognized) >= 2:
                    word = word_recognized[0]
                    confidence = word_recognized[1]
                    
                    if word and word != '' and confidence > 0.3:
                        print(f"💬 MOT RECONNU: '{word}' (confiance: {confidence:.2f})")
                
                # Debug périodique
                if self.sound_activity_count % 50 == 0 and self.sound_activity_count > 0:
                    print(f"📊 Activité totale: {self.sound_activity_count} sons détectés")
                
                time.sleep(0.05)  # 50ms entre vérifications
                
            except Exception as e:
                print(f"❌ Erreur monitoring: {e}")
                time.sleep(0.2)

    def stop_detection(self):
        self.is_running = False
        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join(timeout=2)
        print("🛑 Détection vocale arrêtée")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, required=True)
    parser.add_argument("--port", type=int, default=9559)
    args = parser.parse_args()

    # Connexion à Pepper
    connection_url = f"tcp://{args.ip}:{args.port}"
    app = qi.Application(['WorkingVoiceDetector', '--qi-url=' + connection_url])
    app.start()
    session = app.session

    print("🤖 Détecteur vocal fonctionnel pour événementiel")
    print("   ✅ Détection de parole")
    print("   ✅ Localisation des sons") 
    print("   ✅ Analyse émotionnelle")
    print("   ✅ Reconnaissance de mots")
    
    # Création du détecteur
    voice_detector = WorkingVoiceDetector(session)
    
    try:
        voice_detector.start_detection()
        
        print("\n🎤 Parlez à Pepper pour tester la détection...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé...")
    finally:
        voice_detector.stop_detection()
