import time
import sys
import json
import subprocess
import datetime
import os
import glob
import signal

# Configuration Tactique
INTERFACE = "wlan1" # <-- Ton antenne Alfa
PREFIXE_FICHIER = "/tmp/scan"
FICHIER_CSV = f"{PREFIXE_FICHIER}-01.csv"
FILTRE_RSSI_MIN = -100 # On ignore en dessous de ça

print("[*] Agent C2 v3.0 (Mode Promiscuous Pur) démarré.")
print("[*] Nettoyage des anciennes données tactiques...")

# 1. On supprime les vieux fichiers de scan pour partir à neuf
for f in glob.glob(f"{PREFIXE_FICHIER}*.csv"):
    try:
        os.remove(f)
    except:
        pass

# --- L'ARMEMENT DU MODE MONITOR ---
print(f"[*] Armement de {INTERFACE} en Mode Monitor (Écoute furtive complète)...")
# On force la carte en mode monitor pour que le Channel Hopping fonctionne sans interférence
os.system(f"sudo ip link set {INTERFACE} down")
os.system(f"sudo iwconfig {INTERFACE} mode monitor")
os.system(f"sudo ip link set {INTERFACE} up")
time.sleep(1) # Laisse 1 sec au kernel pour appliquer le changement

# 2. Lancement automatique de l'antenne
print(f"[*] Allumage des moteurs Wi-Fi sur l'interface {INTERFACE}...")

# Lancement de Airodump-ng avec forçage sudo
commande = ["sudo", "airodump-ng", INTERFACE, "--output-format", "csv", "--write", PREFIXE_FICHIER]
process_airodump = subprocess.Popen(commande, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(3)

def lire_donnees_wifi():
    print("[+] Radar Wi-Fi opérationnel. Aspiration du tableau en continu...")

    while True:
        try:
            if not os.path.exists(FICHIER_CSV):
                time.sleep(1)
                continue

            with open(FICHIER_CSV, 'r', encoding='utf-8', errors='ignore') as f:
                lignes = f.readlines()

            for ligne in lignes:
                ligne = ligne.strip()
                if not ligne or "Station MAC" in ligne or "BSSID" in ligne:
                    continue

                colonnes = [c.strip() for c in ligne.split(',')]

                if len(colonnes) >= 14:
                    mac = colonnes[0]
                    heure = datetime.datetime.now().strftime("%H:%M:%S")
                    try:
                        rssi = int(colonnes[8])
                    except:
                        continue

                    # On garde le filtre anti-fantôme pour ne pas crasher la carte Leaflet
                    if rssi < FILTRE_RSSI_MIN or rssi == -1:
                        continue

                    sec = colonnes[5]
                    # Nettoyage robuste du SSID pour éviter les erreurs de format CSV
                    ssid = colonnes[13].strip() if len(colonnes) > 13 and colonnes[13].strip() else "Inconnu"

                    donnees = {
                        "heure": heure,
                        "mac": mac,
                        "rssi": rssi,
                        "sec": sec,
                        "ssid": ssid,
                        "lat": None,
                        "lon": None
                    }

                    print(json.dumps(donnees), flush=True)

        except Exception as e:
            pass

        time.sleep(1)

def handler_arret(signum, frame):
    print("\n[*] Arrêt tactique de l'agent C2.")
    try:
        os.kill(process_airodump.pid, signal.SIGTERM)
        # Remise à la normale de la carte (Pour éviter que le Pi perde internet)
        os.system(f"sudo ip link set {INTERFACE} down")
        os.system(f"sudo iwconfig {INTERFACE} mode managed")
        os.system(f"sudo ip link set {INTERFACE} up")
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, handler_arret)

if __name__ == "__main__":
    lire_donnees_wifi()