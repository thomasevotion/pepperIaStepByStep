import socket
import json
import time

def send_test_message(server_host="192.168.1.17", server_port=8888, test_phrase="Bonjour, peux-tu te présenter ?"):
    """Envoie une phrase de test directement au serveur Gemma2"""
    
    try:
        # Créer socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Message au format attendu par le serveur
        test_message = {
            "type": "conversation_end",
            "timestamp": time.time(),
            "conversation_text": test_phrase
        }
        
        # Encoder en JSON
        json_data = json.dumps(test_message, ensure_ascii=False)
        payload = json_data.encode('utf-8')
        
        print(f"📤 Envoi test vers {server_host}:{server_port}")
        print(f"💬 Phrase test: '{test_phrase}'")
        print(f"📦 Payload: {json_data}")
        
        # Envoyer
        start_time = time.time()
        sock.sendto(payload, (server_host, server_port))
        
        print(f"✅ Message envoyé en {time.time() - start_time:.3f}s")
        print("⏳ Attendre la réponse du serveur LLM...")
        
        sock.close()
        
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")

if __name__ == "__main__":
    import sys
    
    # Phrases de test prédéfinies
    test_phrases = [
        "Bonjour, peux-tu te présenter ?",
        "Quel temps fait-il aujourd'hui ?", 
        "Comment ça va ?",
        "Que peux-tu faire pour moi ?",
        "Parle-moi de cet événement",
        "As-tu des informations sur les activités ?",
        "Aide-moi s'il te plaît",
        "Merci beaucoup"
    ]
    
    print("🧪 TESTEUR SERVEUR GEMMA2")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        # Phrase personnalisée en argument
        phrase = " ".join(sys.argv[1:])
        send_test_message(test_phrase=phrase)
    else:
        # Menu interactif
        print("Phrases de test disponibles:")
        for i, phrase in enumerate(test_phrases, 1):
            print(f"{i}. {phrase}")
        print("0. Phrase personnalisée")
        
        try:
            choice = int(input("\nChoisir une phrase (1-8 ou 0): "))
            
            if choice == 0:
                custom_phrase = input("Tapez votre phrase: ")
                send_test_message(test_phrase=custom_phrase)
            elif 1 <= choice <= len(test_phrases):
                send_test_message(test_phrase=test_phrases[choice-1])
            else:
                print("❌ Choix invalide")
                
        except ValueError:
            print("❌ Veuillez entrer un nombre valide")
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du test")
