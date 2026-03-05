import sys
import json
import time
import os
import csv

historique_gps = []
routeurs = {}
dernier_affichage = time.time()

os.system('clear' if os.name == 'posix' else 'cls')
print("[*] Initialisation du système de mémoire...")

# ---> LA MÉMOIRE PERSISTANTE (Chargement de l'historique) <---
try:
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            anciennes_donnees = json.load(f)
            # On réinjecte les anciennes cibles dans le cerveau du programme
            for c in anciennes_donnees.get("cibles", []):
                prefixe_mac = c["mac"][:-1]
                routeurs[prefixe_mac] = {
                    "mac_affichage": c["mac"],
                    "ssid": c["ssid"], 
                    "sec": c["sec"], 
                    "meilleur_rssi": c["rssi"], 
                    "lectures": c["lectures"],
                    "lat": c["lat"],
                    "lon": c["lon"]
                }
        print(f"[+] Mémoire restaurée : {len(routeurs)} réseaux rechargés sur la carte !")
    else:
        print("[-] Aucune donnée précédente trouvée. Démarrage à zéro.")
except Exception as e:
    print(f"[!] Erreur lors du chargement de la mémoire : {e}")

# Petite pause pour te laisser lire le statut, puis on efface pour le radar
time.sleep(2)

try:
    while True:
        ligne = sys.stdin.readline()
        if not ligne: break
        ligne = ligne.strip()
        if not ligne: continue
        
        try:
            donnees = json.loads(ligne)
        except:
            continue
        
        heure = donnees.get("heure", "00:00:00")
        ssid = donnees.get("ssid", "Inconnu")
        mac = donnees.get("mac", "Inconnu")
        rssi = donnees.get("rssi", -100)
        sec = donnees.get("sec", "Inconnu")
        lat = donnees.get("lat")
        lon = donnees.get("lon")
        
        if lat is None or lon is None:
            continue

        # La ligne bleue du trajet ne garde que la marche actuelle (plus propre visuellement)
        historique_gps.append([lat, lon])
        if len(historique_gps) > 500: historique_gps.pop(0)

        # L'Empilement Absolu : on regroupe par machine physique
        prefixe_mac = mac[:-1]

        if prefixe_mac not in routeurs:
            routeurs[prefixe_mac] = {
                "mac_affichage": mac,
                "ssid": ssid, 
                "sec": sec, 
                "meilleur_rssi": -100, 
                "lectures": 0,
                "lat": lat,
                "lon": lon
            }
            
        routeurs[prefixe_mac]["lectures"] += 1
        routeurs[prefixe_mac]["rssi_actuel"] = rssi

        # La Gravité : On met à jour la position GPS SEULEMENT si on s'est rapproché
        if rssi > routeurs[prefixe_mac]["meilleur_rssi"]: 
            routeurs[prefixe_mac]["meilleur_rssi"] = rssi
            routeurs[prefixe_mac]["lat"] = lat
            routeurs[prefixe_mac]["lon"] = lon

        export_data = {"gps_actuel": [lat, lon], "trajet": historique_gps, "cibles": []}

        for pref, r_data in routeurs.items():
            export_data["cibles"].append({
                "mac": r_data["mac_affichage"], "ssid": r_data["ssid"], "lat": r_data["lat"], "lon": r_data["lon"],
                "sec": r_data["sec"], "rssi": r_data["meilleur_rssi"], "rssi_actuel": r_data.get("rssi_actuel", -100), "lectures": r_data["lectures"]
            })

        # 1. Mise à jour de la carte web
        with open("data.json", "w") as f:
            json.dump(export_data, f)
            
        # 2. La Boîte Noire (Mise à jour du fichier Excel avec tout l'historique fusionné)
        with open("scan_historique.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["BSSID (MAC)", "Nom (SSID)", "Sécurité", "Force Max (dBm)", "Nb Lectures", "Latitude", "Longitude"])
            for c in export_data["cibles"]:
                writer.writerow([c["mac"], c["ssid"], c["sec"], c["rssi"], c["lectures"], c["lat"], c["lon"]])

        # 3. L'interface Terminal (Radar Live)
        if time.time() - dernier_affichage > 1.0:
            print("\033[H\033[J", end="") 
            print(f"[{heure}] 📡 LIVE RADAR ][ GPS : {lat:.5f}, {lon:.5f} ][ CIBLES TOTALES : {len(routeurs)}")
            print("=" * 80)
            print(f"{'BSSID (MAC)':<20} {'PWR':<5} {'BEACONS':<8} {'ENC':<6} {'ESSID'}")
            print("-" * 80)
            cibles_triees = sorted(export_data["cibles"], key=lambda x: x["rssi_actuel"], reverse=True)
            for c in cibles_triees[:20]:
                print(f"{c['mac']:<20} {c['rssi_actuel']:<5} {c['lectures']:<8} {c['sec']:<6} {c['ssid']}")
            dernier_affichage = time.time()

except KeyboardInterrupt:
    print("\n[*] Repli tactique. Données sécurisées à vie dans scan_historique.csv")