import sys
import json
import time
import os
import csv
import threading
import ssl
import http.server
import urllib.request
import math  # <--- NOUVEAU : Pour le cercle tactique

# --- 1. GLOBALES POUR LE GPS ---
gps_actuel = {"lat": None, "lon": None}

# --- 2. LE SERVEUR UNIFIÉ ---
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
                except: pass

                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b"OK")
            except:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args): pass

def lancer_serveur_unifie():
    httpd = http.server.ThreadingHTTPServer(('0.0.0.0', 4443), UnifiedHandler)
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        httpd.serve_forever()
    except Exception as e: print(f"[!] Erreur SSL : {e}")

threading.Thread(target=lancer_serveur_unifie, daemon=True).start()

if not os.path.exists("data.json"):
    with open("data.json", "w") as f: json.dump({"gps_actuel": [0, 0], "trajet": [], "cibles": []}, f)

# --- 4. LE MOTEUR OSINT TACTIQUE (AUTO-DOWNLOAD) ---
dictionnaire_oui = {}
fichier_osint = "ieee-oui.txt"

print("=" * 60)
print("[*] SÉQUENCE DE DÉMARRAGE DU MOTEUR OSINT...")
print("=" * 60)

# 1. Téléchargement automatique si le fichier est absent ou trop petit
if not os.path.exists(fichier_osint) or os.path.getsize(fichier_osint) < 100000:
    print("[*] Base OSINT (IEEE) absente. Téléchargement en cours (1.5 Mo)...")
    try:
        url = "https://raw.githubusercontent.com/royhills/arp-scan/master/ieee-oui.txt"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            with open(fichier_osint, "w", encoding="utf-8") as f:
                f.write(response.read().decode('utf-8'))
        print("[+] Téléchargement OSINT réussi avec succès !")
    except Exception as e:
        print(f"[!] ERREUR DE TÉLÉCHARGEMENT : {e}")

# 2. Lecture du fichier
if os.path.exists(fichier_osint):
    try:
        with open(fichier_osint, "r", encoding="utf-8", errors="ignore") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "<html" in ligne.lower(): 
                    continue
                
                morceaux = ligne.split(None, 1)
                if len(morceaux) >= 2:
                    cle = morceaux[0].replace(":", "").replace("-", "").upper()[:6]
                    dictionnaire_oui[cle] = morceaux[1].strip()
                    
        print(f"[+] Base OSINT chargée : {len(dictionnaire_oui)} fabricants prêts.")
    except Exception as e:
        print(f"[-] Erreur de lecture : {e}")
        
# --- 5. LE MOTEUR PRINCIPAL (Fusion par Réseau/SSID) ---
historique_gps = []
reseaux = {} # On ne l'appelle plus "routeurs", mais "reseaux"
dernier_affichage = time.time()

try:
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            anciennes_donnees = json.load(f)
            for c in anciennes_donnees.get("cibles", []):
                cle = c.get("ssid", "Inconnu")
                # Restauration de la mémoire
                reseaux[cle] = {
                    "ssid": cle, "macs": set(), "sec": c.get("sec", "Inconnu"),
                    "meilleur_rssi": c.get("rssi", -100), "lectures": c.get("lectures", 0),
                    "lat": c.get("lat", 0.0), "lon": c.get("lon", 0.0), 
                    "fabricants": set([c.get("fabricant", "Inconnu")]), "total_poids": 0
                }
except: pass

print("\n[*] Lancement du Radar Tactique dans 2 secondes...")
time.sleep(2)

try:
    while True:
        ligne = sys.stdin.readline()
        if not ligne: break
        ligne = ligne.strip()
        if not ligne: continue
        
        try: donnees = json.loads(ligne)
        except: continue
        
        heure = donnees.get("heure", "00:00:00")
        ssid = str(donnees.get("ssid", "Inconnu"))
        mac = str(donnees.get("mac", "Inconnu"))
        rssi = donnees.get("rssi", -100)
        sec = str(donnees.get("sec", "Inconnu"))
        lat, lon = gps_actuel["lat"], gps_actuel["lon"]
        if lat is None or lon is None: continue

        fabricant = str(dictionnaire_oui.get(mac.replace(":", "").replace("-", "").upper()[:6], "Inconnu"))

        if not historique_gps or historique_gps[-1] != [lat, lon]: historique_gps.append([lat, lon])
        if len(historique_gps) > 500: historique_gps.pop(0)

        # LA CLÉ INTELLIGENTE : On groupe par Nom de réseau. Si pas de nom, on groupe par antenne physique.
        cle_principale = ssid if (ssid != "Inconnu" and ssid != "") else f"Réseau Caché ({mac[:-1]}X)"

        if cle_principale not in reseaux:
            reseaux[cle_principale] = {
                "ssid": cle_principale, "macs": {mac}, "sec": sec, 
                "meilleur_rssi": -100, "lectures": 0, "lat": lat, "lon": lon, 
                "fabricants": {fabricant} if fabricant != "Inconnu" else set(), "total_poids": 0
            }
        else:
            reseaux[cle_principale]["macs"].add(mac)
            if fabricant != "Inconnu": reseaux[cle_principale]["fabricants"].add(fabricant)
            
        reseaux[cle_principale]["lectures"] += 1
        reseaux[cle_principale]["rssi_actuel"] = rssi

        # CALCUL DU CENTRE DE MASSE (Ajustement de position basé sur la force du signal)
        poids_actuel = (100 + rssi) ** 4
        if reseaux[cle_principale]["total_poids"] == 0:
            reseaux[cle_principale]["lat"], reseaux[cle_principale]["lon"] = lat, lon
            reseaux[cle_principale]["total_poids"] = poids_actuel
        else:
            vp = reseaux[cle_principale]["total_poids"]
            np = vp + poids_actuel
            reseaux[cle_principale]["lat"] = ((reseaux[cle_principale]["lat"] * vp) + (lat * poids_actuel)) / np
            reseaux[cle_principale]["lon"] = ((reseaux[cle_principale]["lon"] * vp) + (lon * poids_actuel)) / np
            reseaux[cle_principale]["total_poids"] = np

        if rssi > reseaux[cle_principale]["meilleur_rssi"]: reseaux[cle_principale]["meilleur_rssi"] = rssi

        # --- DÉTECTION DE MOUVEMENT (L'IA Tactique) ---
        est_stationnaire = True
        if len(historique_gps) > 5:
            lats = [p[0] for p in historique_gps]
            lons = [p[1] for p in historique_gps]
            # Si on a marché sur plus de ~20 mètres, on désactive le mode stationnaire
            if (max(lats) - min(lats)) > 0.0002 or (max(lons) - min(lons)) > 0.0002:
                est_stationnaire = False

        export_data = {"gps_actuel": [lat, lon], "trajet": historique_gps, "cibles": []}
        
        cibles_list = list(reseaux.values())
        total_cibles = len(cibles_list)

        for i, r in enumerate(cibles_list):
            fabs = [f for f in r["fabricants"] if f]
            fab_str = " | ".join(fabs) if fabs else "Inconnu"
            
            # --- CALCUL DE LA POSITION VISUELLE ---
            if est_stationnaire and lat is not None and total_cibles > 0:
                # MODE SENTINELLE : Déploie les points en un cercle géométrique parfait
                angle = (i / total_cibles) * 2 * math.pi
                rayon = 0.00025  # ~25 mètres de distance autour de ton point bleu
                lat_visuel = lat + (rayon * math.cos(angle))
                lon_visuel = lon + (rayon * math.sin(angle))
            else:
                # MODE TRAQUE : Les points s'accrochent à leur position triangulée réelle
                lat_visuel = r["lat"]
                lon_visuel = r["lon"]

            export_data["cibles"].append({
                "ssid": r["ssid"], 
                "mac": f"{len(r['macs'])} Antenne(s)", 
                "lat": lat_visuel, "lon": lon_visuel, "sec": r["sec"], 
                "rssi": r["meilleur_rssi"], "rssi_actuel": r.get("rssi_actuel", -100), 
                "lectures": r["lectures"], "fabricant": fab_str
            })

        with open("data.json", "w") as f: json.dump(export_data, f)
            
        if time.time() - dernier_affichage > 1.0:
            print("\033[H\033[J", end="") 
            print(f"[{heure}] 📡 MODE ESSID ][ GPS: {lat:.5f}, {lon:.5f} ][ RÉSEAUX UNIQUES: {len(reseaux)} ]")
            print("=" * 80)
            print(f"{'RÉSEAU (SSID)':<25} {'TAILLE':<12} {'PWR':<5} {'BEACONS':<8} {'ENC':<6}")
            print("-" * 80)
            for c in sorted(export_data["cibles"], key=lambda x: x["rssi_actuel"], reverse=True)[:20]:
                print(f"{str(c['ssid'])[:25]:<25} {str(c['mac'])[:12]:<12} {c['rssi_actuel']:<5} {c['lectures']:<8} {str(c['sec'])[:6]:<6}")
            dernier_affichage = time.time()

except KeyboardInterrupt:
    print("\n[*] Système hors ligne. Données sécurisées.")