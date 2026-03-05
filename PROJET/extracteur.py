import json
import csv

print("[*] Ouverture de la boîte noire...")

try:
    with open("data.json", "r") as f:
        data = json.load(f)

    with open("scan_historique.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["BSSID (MAC)", "Nom (SSID)", "Sécurité", "Force Max (dBm)", "Nb Lectures", "Latitude", "Longitude"])
        
        for c in data["cibles"]:
            writer.writerow([c["mac"], c["ssid"], c["sec"], c["rssi"], c["lectures"], c["lat"], c["lon"]])

    print(f"[+] Succès total ! {len(data['cibles'])} réseaux ont été exportés vers scan_historique.csv")
    
except FileNotFoundError:
    print("[!] Erreur : Le fichier data.json n'est pas dans ce dossier.")
