import qi
import argparse
import time

class EventHandler(object):
    def __init__(self):
        pass
    
    def on_people_list(self, key, value, message):
        print("Liste des personnes changée:", value)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, required=True)
    parser.add_argument("--port", type=int, default=9559)
    args = parser.parse_args()

    # Connexion au robot Pepper via qi
    connection_url = "tcp://{}:{}".format(args.ip, args.port)
    app = qi.Application(['pepper_presence', '--qi-url=' + connection_url])
    app.start()
    session = app.session

    # Vérifier et activer les services nécessaires
    try:
        people_perception = session.service("ALPeoplePerception")
        print("ALPeoplePerception trouvé et activé")
        
        basic_awareness = session.service("ALBasicAwareness")
        basic_awareness.setEnabled(True)
        print("ALBasicAwareness activé")
        
        # Service pour contrôler les LEDs
        leds = session.service("ALLeds")
        print("ALLeds activé")
        
    except Exception as e:
        print("Erreur lors de l'activation des services:", e)

    # Abonnement via événement
    handler = EventHandler()
    session.registerService("EventHandler", handler)
    memory = session.service("ALMemory")
    memory.subscribeToEvent("PeoplePerception/PeopleList", "EventHandler", "on_people_list")

    print("Abonnements actifs. Test manuel toutes les 2 secondes...")
    
    # Variable pour suivre l'état précédent
    previous_people_detected = False
    
    try:
        while True:
            # VERIFICATION MANUELLE des données ALMemory
            try:
                people_list = memory.getData("PeoplePerception/PeopleList")
                current_people_detected = bool(people_list)
                
                if people_list:
                    print("*** MANUEL: Personnes détectées:", people_list)
                    for person_id in people_list:
                        distance = memory.getData(f"PeoplePerception/Person/{person_id}/Distance")
                        visible = memory.getData(f"PeoplePerception/Person/{person_id}/IsVisible")
                        print(f"  - Personne {person_id}: distance={distance:.2f}m, visible={visible}")
                    
                    # Changer les yeux en VERT quand quelqu'un est détecté
                    if not previous_people_detected:
                        leds.setIntensity("FaceLeds", 1.0)  # Intensité maximale
                        leds.fadeRGB("FaceLeds", 0, 255, 0, 0.5)  # Vert (R=0, G=255, B=0)
                        print("👀 YEUX VERTS - Personne détectée !")
                        
                else:
                    print("*** MANUEL: Aucune personne dans PeopleList")
                    
                    # Changer les yeux en ROUGE quand personne n'est détecté
                    if previous_people_detected:
                        leds.setIntensity("FaceLeds", 1.0)
                        leds.fadeRGB("FaceLeds", 255, 0, 0, 0.5)  # Rouge (R=255, G=0, B=0)
                        print("👀 YEUX ROUGES - Aucune personne")
                
                # Mettre à jour l'état précédent
                previous_people_detected = current_people_detected
                        
            except Exception as e:
                print("Erreur lecture manuelle:", e)
            
            time.sleep(2)
    except KeyboardInterrupt:
        # Remettre les yeux en blanc avant de quitter
        leds.fadeRGB("FaceLeds", 255, 255, 255, 1.0)  # Blanc
        memory.unsubscribeToEvent("PeoplePerception/PeopleList", "EventHandler")
        print("Arrêté proprement - yeux remis en blanc.")
