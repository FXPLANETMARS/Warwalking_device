#!/bin/bash

# Fonction qui gère le Ctrl+C
cleanup() {
    echo -e "\n[*] Signal d'arrêt reçu (Ctrl+C). Nettoyage tactique..."
    echo "[+] Système hors ligne. Bonne journée !"
    exit 0
}

trap cleanup SIGINT

echo "[*] Démarrage du Serveur Unifié (Web + API) et connexion au Drone..."
ssh kali@100.126.11.58 "sudo python3 -u agent_c2.py" | python3 -u MapListener.py