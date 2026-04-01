import sys
import json
import time
import os
import csv
import threading
import ssl
import http.server
import urllib.request

# --- 1. GLOBALES POUR LE GPS ---
gps_actuel = {"lat": None, "lon": None}

# --- 2. LE SERVEUR UNIFIÉ (WEB + API GPS) SUR LE MÊME PORT ---
class UnifiedHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/update_gps':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                gps_actuel["lat"] = data.get("lat")
                gps_actuel["lon"] = data.get("lon")
                
                sys.stdout.write("🎯")
                sys.stdout.flush()
                
                try:
                    with open("data.json", "r") as f:
                        fichier_carte = json.load(f)
                    
                    fichier_carte["gps_actuel"] = [gps_actuel["lat"], gps_actuel["lon"]]
                    
                    with open("data.json", "w") as f:
                        json.dump(fichier_carte, f)
                except Exception as e:
                    pass

                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b"OK")
            except Exception as e:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def lancer_serveur_unifie():
    port = 4443
    serveur_adresse = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(serveur_adresse, UnifiedHandler)
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        httpd.serve_forever()
    except Exception as e:
        print(f"[!] Erreur SSL Serveur Web : {e}")

thread_serveur = threading.Thread(target=lancer_serveur_unifie, daemon=True)
thread_serveur.start()

# --- 3. FIX ERREUR 404 ---
if not os.path.exists("data.json"):
    with open("data.json", "w") as f:
        json.dump({"gps_actuel": [0, 0], "trajet": [], "cibles": []}, f)

# --- 4. LE MOTEUR OSINT TACTIQUE (Évasion Pare-Feu) ---
dictionnaire_oui = {}
fichier_osint = "mac-vendor.txt"

print("=" * 60)
print("[*] SÉQUENCE DE DÉMARRAGE DU C2...")
print("=" * 60)

# Fonction d'évasion pour contourner les portails captifs et pare-feux
def telecharger_osint_securise():
    urls_tactiques = [
        # Stratégie 1 : CDN jsDelivr. Les pare-feux n'osent pas bloquer ça sinon tout casse.
        "https://cdn.jsdelivr.net/gh/royhills/arp-scan@master/mac-vendor.txt",
        # Stratégie 2 : GitHack (Proxy miroir alternatif pour GitHub)
        "https://raw.githack.com/royhills/arp-scan/master/mac-vendor.txt",
        # Stratégie 3 : Le miroir officiel brut de Wireshark
        "https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf"
    ]
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    for url in urls_tactiques:
        domaine = url.split('/')[2]
        print(f"[*] Tentative d'infiltration OSINT via : {domaine}...")
        try:
            # On se déguise parfaitement
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                contenu_brut = response.read()
                texte = contenu_brut.decode('utf-8', errors='ignore')
                
                # SÉCURITÉ : Si le Cégep nous envoie une fausse page HTML, on la rejette !
                if "<html" in texte.lower() or len(texte) < 50000:
                    print("[-] Pare-feu détecté (Fausse page Web ou fichier bloqué). Changement de cible...")
                    continue
                
                with open(fichier_osint, "w", encoding="utf-8") as f:
                    f.write(texte)
                print(f"[+] Téléchargement OSINT réussi et vérifié via {domaine} !")
                return True
        except Exception as e:
            print(f"[-] Échec sur cette source : {e}")
    return False

# Nettoyage si le fichier actuel est une fausse page Web
if os.path.exists(fichier_osint) and os.path.getsize(fichier_osint) < 50000:
    print("[-] Fichier OSINT corrompu/bloqué détecté. Destruction...")
    os.remove(fichier_osint)

if not os.path.exists(fichier_osint):
    print("[*] Base OSINT absente. Lancement du script d'évasion automatisé...")
    reussite = telecharger_osint_securise()
    if not reussite:
        print("[!] Échec total : Impossible de contourner le pare-feu du réseau.")

# Lecture de la base de données
try:
    with open(fichier_osint, "r", encoding="utf-8", errors="ignore") as f:
        for ligne in f:
            ligne = ligne.strip()
            # On ignore les commentaires et on se protège des balises HTML résiduelles
            if not ligne or ligne.startswith("#") or "<" in ligne: continue
            
            # On sépare au premier espace ou tabulation
            morceaux = ligne.split(None, 1) 
            if len(morceaux) >= 2:
                cle_propre = morceaux[0].replace(":", "").replace("-", "").upper()[:6]
                dictionnaire_oui[cle_propre] = str(morceaux[1]).strip()
                
    print(f"[+] Base OSINT chargée : {len(dictionnaire_oui)} fabricants prêts.")
except Exception as e:
    print(f"[-] Erreur de lecture de la base (Fichier absent ?) : {e}")

# --- 5. LE MOTEUR PRINCIPAL (Le Radar et Triangulation) ---
historique_gps = []
routeurs = {}
dernier_affichage = time.time()

try:
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            anciennes_donnees = json.load(f)
            for c in anciennes_donnees.get("cibles", []):
                prefixe_mac = c["mac"][:-1]
                routeurs[prefixe_mac] = {
                    "mac_affichage": c["mac"], 
                    "ssid": str(c.get("ssid", "Inconnu")), 
                    "sec": str(c.get("sec", "Inconnu")), 
                    "meilleur_rssi": c.get("rssi", -100), 
                    "lectures": c.get("lectures", 0),
                    "lat": c.get("lat", 0.0), 
                    "lon": c.get("lon", 0.0), 
                    "fabricant": str(c.get("fabricant", "Inconnu")),
                    "total_poids": 0
                }
        print(f"[+] Mémoire tactique restaurée : {len(routeurs)} réseaux rechargés !")
except Exception as e:
    print(f"[!] Erreur mémoire : {e}")

print("\n[*] Lancement du Radar Tactique dans 3 secondes...")
time.sleep(3)

try:
    while True:
        ligne = sys.stdin.readline()
        if not ligne: break
        ligne = ligne.strip()
        if not ligne: continue
        
        try:
            donnees = json.loads(ligne)
        except: continue
        
        heure = donnees.get("heure", "00:00:00")
        ssid = str(donnees.get("ssid", "Inconnu"))
        mac = str(donnees.get("mac", "Inconnu"))
        rssi = donnees.get("rssi", -100)
        sec = str(donnees.get("sec", "Inconnu"))
        
        lat = gps_actuel["lat"]
        lon = gps_actuel["lon"]
        
        if lat is None or lon is None:
            continue

        mac_propre = mac.replace(":", "").replace("-", "").upper()
        prefixe_mac_complet = mac_propre[:6]
        fabricant = str(dictionnaire_oui.get(prefixe_mac_complet, "Inconnu"))

        if not historique_gps or historique_gps[-1] != [lat, lon]:
            historique_gps.append([lat, lon])
        if len(historique_gps) > 500: historique_gps.pop(0)

        prefixe_mac = mac[:-1]

        if prefixe_mac not in routeurs:
            routeurs[prefixe_mac] = {
                "mac_affichage": mac, "ssid": ssid, "sec": sec, 
                "meilleur_rssi": -100, "lectures": 0, "lat": lat, "lon": lon, "fabricant": fabricant,
                "total_poids": 0
            }
            
        routeurs[prefixe_mac]["lectures"] += 1
        routeurs[prefixe_mac]["rssi_actuel"] = rssi
        
        if fabricant != "Inconnu":
            routeurs[prefixe_mac]["fabricant"] = fabricant

        poids_actuel = (100 + rssi) ** 4
        
        if routeurs[prefixe_mac].get("total_poids", 0) == 0:
            routeurs[prefixe_mac]["lat"] = lat
            routeurs[prefixe_mac]["lon"] = lon
            routeurs[prefixe_mac]["total_poids"] = poids_actuel
        else:
            vieux_poids = routeurs[prefixe_mac]["total_poids"]
            nouveau_total_poids = vieux_poids + poids_actuel
            routeurs[prefixe_mac]["lat"] = ((routeurs[prefixe_mac]["lat"] * vieux_poids) + (lat * poids_actuel)) / nouveau_total_poids
            routeurs[prefixe_mac]["lon"] = ((routeurs[prefixe_mac]["lon"] * vieux_poids) + (lon * poids_actuel)) / nouveau_total_poids
            routeurs[prefixe_mac]["total_poids"] = nouveau_total_poids

        if rssi > routeurs[prefixe_mac]["meilleur_rssi"]:
            routeurs[prefixe_mac]["meilleur_rssi"] = rssi

        export_data = {"gps_actuel": [lat, lon], "trajet": historique_gps, "cibles": []}

        for pref, r_data in routeurs.items():
            export_data["cibles"].append({
                "mac": r_data["mac_affichage"], "ssid": r_data["ssid"], "lat": r_data["lat"], "lon": r_data["lon"],
                "sec": r_data["sec"], "rssi": r_data["meilleur_rssi"], "rssi_actuel": r_data.get("rssi_actuel", -100), 
                "lectures": r_data["lectures"], "fabricant": r_data["fabricant"]
            })

        with open("data.json", "w") as f:
            json.dump(export_data, f)
            
        if time.time() - dernier_affichage > 1.0:
            print("\033[H\033[J", end="") 
            print(f"[{heure}] 📡 LIVE RADAR ][ GPS : {lat:.5f}, {lon:.5f} ][ CIBLES : {len(routeurs)} ][ OSINT : {len(dictionnaire_oui)} ]")
            print("=" * 80)
            print(f"{'BSSID (MAC)':<20} {'FABRICANT':<17} {'PWR':<5} {'BEACONS':<8} {'ENC':<6} {'ESSID'}")
            print("-" * 80)
            cibles_triees = sorted(export_data["cibles"], key=lambda x: x["rssi_actuel"], reverse=True)
            
            for c in cibles_triees[:20]:
                mac_affiche = str(c.get('mac', ''))
                # On nettoie un peu le nom du fabricant pour l'affichage CLI
                fab_affiche = str(c.get('fabricant', 'Inconnu')).split('#')[0].strip()[:15]
                rssi_affiche = c.get('rssi_actuel', -100)
                lect_affiche = c.get('lectures', 0)
                sec_affiche = str(c.get('sec', ''))[:6]
                ssid_affiche = str(c.get('ssid', ''))[:20]
                
                print(f"{mac_affiche:<20} {fab_affiche:<17} {rssi_affiche:<5} {lect_affiche:<8} {sec_affiche:<6} {ssid_affiche}")
            
            dernier_affichage = time.time()

except KeyboardInterrupt:
    print("\n[*] Repli tactique. Sauvegarde d'urgence de la mémoire...")
    
    export_final = {"gps_actuel": [gps_actuel["lat"], gps_actuel["lon"]], "trajet": historique_gps, "cibles": []}
    for pref, r_data in routeurs.items():
        export_final["cibles"].append({
            "mac": r_data["mac_affichage"], "ssid": r_data["ssid"], "lat": r_data["lat"], "lon": r_data["lon"],
            "sec": r_data["sec"], "rssi": r_data["meilleur_rssi"], "rssi_actuel": r_data.get("rssi_actuel", -100), 
            "lectures": r_data["lectures"], "fabricant": r_data["fabricant"]
        })
        
    with open("data.json", "w") as f:
        json.dump(export_final, f)
        
    with open("scan_historique.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["BSSID (MAC)", "Fabricant", "Nom (SSID)", "Sécurité", "Force Max (dBm)", "Nb Lectures", "Latitude", "Longitude"])
        for c in export_final["cibles"]:
            writer.writerow([c["mac"], c["fabricant"], c["ssid"], c["sec"], c["rssi"], c["lectures"], c["lat"], c["lon"]])
            
    print("[+] Données sécurisées avec succès. Système hors ligne.")