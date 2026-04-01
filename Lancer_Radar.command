#!/bin/bash

# Fonction qui sera appelée quand tu fais Ctrl+C
cleanup() {
    echo "\n[*] Signal d'arrêt reçu (Ctrl+C). Nettoyage tactique..."
    # On tue le serveur web qui tourne en arrière-plan
    kill $WEB_PID 2>/dev/null
    echo "[+] Serveur web arrêté."
    echo "[+] Connexion SSH coupée."
    echo "[+] Système hors ligne. Bonne journée !"
    exit 0
}

# On attache la fonction cleanup au signal SIGINT (Ctrl+C)
trap cleanup SIGINT

echo "[*] Création du fichier data.json initial pour éviter l'erreur 404..."
echo '{"gps_actuel": [0, 0], "trajet": [], "cibles": []}' > data.json

echo "[*] Démarrage du serveur HTTPS sur le port 4443..."
python3 lanceur_web.py &
WEB_PID=$!
sleep 1 # On lui laisse 1 seconde pour démarrer

echo "[*] Connexion au Drone (Raspberry Pi) et lancement du MapListener..."
# Lance la connexion. L'esperluette n'est pas là, donc ça reste au premier plan.
ssh kali@100.126.11.58 "sudo python3 -u agent_c2.py" | python3 -u MapListener.py
