import sys
import json
import math
import random
import time
import os

historique_gps = []
routeurs = {}
dernier_affichage = time.time()

# Séquence pour vider l'écran proprement au démarrage
os.system('clear' if os.name == 'posix' else 'cls')

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
            if time.time() - dernier_affichage > 2.0:
                print("\033[H\033[J", end="")
                print(f"[{heure}] 📡 Wi-Fi capté : {ssid} ({rssi} dBm)")
                print("❌ ATTENTE DU SIGNAL SATELLITE (Vérifie GPS2IP ou va près d'une fenêtre)...")
                dernier_affichage = time.time()
            continue

        historique_gps.append([lat, lon])
        if len(historique_gps) > 500: historique_gps.pop(0)

        poids = 10 ** (rssi / 10.0)
        
        if mac not in routeurs:
            routeurs[mac] = {"ssid": ssid, "sec": sec, "somme_lat_w": 0.0, "somme_lon_w": 0.0, "somme_w": 0.0, "meilleur_rssi": -100, "lectures": 0}
            
        routeurs[mac]["somme_lat_w"] += lat * poids
        routeurs[mac]["somme_lon_w"] += lon * poids
        routeurs[mac]["somme_w"] += poids
        routeurs[mac]["lectures"] += 1
        
        # Le signal en temps réel (pour le tableau terminal)
        routeurs[mac]["rssi_actuel"] = rssi
        if rssi > routeurs[mac]["meilleur_rssi"]: 
            routeurs[mac]["meilleur_rssi"] = rssi

        export_data = {"gps_actuel": [lat, lon], "trajet": historique_gps, "cibles": []}

        for r_mac, r_data in routeurs.items():
            lat_p = r_data["somme_lat_w"] / r_data["somme_w"]
            lon_p = r_data["somme_lon_w"] / r_data["somme_w"]
            
            if r_data["lectures"] < 5:
                random.seed(r_mac)
                dist = max(5, abs(r_data["meilleur_rssi"]) - 30) * 1.5
                offset = dist / 111320.0
                angle = random.uniform(0, 2 * math.pi)
                lat_p += offset * math.cos(angle)
                lon_p += offset * math.sin(angle)

            export_data["cibles"].append({
                "mac": r_mac, "ssid": r_data["ssid"], "lat": lat_p, "lon": lon_p,
                "sec": r_data["sec"], "rssi": r_data["meilleur_rssi"], "rssi_actuel": r_data.get("rssi_actuel", -100), "lectures": r_data["lectures"]
            })

        with open("data.json", "w") as f:
            json.dump(export_data, f)
            
        # --- L'INTERFACE STYLE AIRODUMP-NG ---
        # On redessine le terminal maximum 1 fois par seconde pour éviter que ça clignote
        if time.time() - dernier_affichage > 1.0:
            # \033[H = Retour en haut à gauche, \033[J = Effacer jusqu'en bas
            print("\033[H\033[J", end="") 
            print(f"[{heure}] CH : * ][ BAT : -- ][ GPS : {lat:.5f}, {lon:.5f} ][ CIBLES : {len(routeurs)}")
            print("=" * 80)
            print(f"{'BSSID (MAC)':<20} {'PWR':<5} {'BEACONS':<8} {'ENC':<6} {'ESSID'}")
            print("-" * 80)
            
            # On trie les cibles par force de signal actuel (le plus fort en haut)
            cibles_triees = sorted(export_data["cibles"], key=lambda x: x["rssi_actuel"], reverse=True)
            
            # On affiche seulement les 20 plus proches pour que ça rentre dans l'écran
            for c in cibles_triees[:20]:
                print(f"{c['mac']:<20} {c['rssi_actuel']:<5} {c['lectures']:<8} {c['sec']:<6} {c['ssid']}")
                
            dernier_affichage = time.time()

except KeyboardInterrupt:
    print("\n[*] Arrêt du MapListener.")
