#!/bin/bash

# Fonction qui sera appelée quand tu fais Ctrl+C
cleanup() {
    echo -e "\n[*] Signal d'arrêt reçu (Ctrl+C). Nettoyage tactique..."
    echo "[+] Connexion SSH coupée."
    echo "[+] Système hors ligne. Bonne journée !"
    exit 0
}

trap cleanup SIGINT

echo "[*] Création du fichier data.json initial pour éviter l'erreur 404..."
echo '{"gps_actuel": [0, 0], "trajet": [], "cibles": []}' > data.json

echo "[*] Connexion au Drone (Raspberry Pi) et lancement du C2 Unifié..."
# On lance la connexion SSH. MapListener s'occupe de TOUT (Web + Radar)
ssh kali@100.126.11.58 "sudo python3 -u agent_c2.py" | python3 -u MapListener.py