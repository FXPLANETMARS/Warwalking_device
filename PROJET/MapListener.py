import sys
import json
import folium
import random
import math

# Point de départ temporaire
START_LAT = 45.7775
START_LON = -74.0020

print("[*] MapListener démarré. En attente du fix GPS...")

m = folium.Map(location=[START_LAT, START_LON], zoom_start=18, tiles="CartoDB positron")

# --- NOUVEAU : LE CALQUE DE TON TRAJET ---
groupe_trajet = folium.FeatureGroup(name="🔵 Mon Trajet (GPS)", show=True)

groupe_ouvert = folium.FeatureGroup(name="🟢 Ouvert", show=True)
groupe_wep = folium.FeatureGroup(name="🟡 WEP", show=True)
groupe_wpa = folium.FeatureGroup(name="🟠 WPA", show=True)
groupe_wpa2 = folium.FeatureGroup(name="🔴 WPA2", show=True)
groupe_wpa3 = folium.FeatureGroup(name="🟣 WPA3", show=True)

m.add_child(groupe_trajet)
m.add_child(groupe_ouvert)
m.add_child(groupe_wep)
m.add_child(groupe_wpa)
m.add_child(groupe_wpa2)
m.add_child(groupe_wpa3)
m.add_child(folium.LayerControl(collapsed=False))

m.save("carte_tactique.html")

# Mémoire pour ne pas redessiner le même routeur 100 fois si on reste sur place
reseaux_places = set()

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
            print(f"[⌛ RECHERCHE SATELLITES] {ssid} ({rssi} dBm) capté, attente du GPS...")
            continue

        # 1. Mettre à jour le centre de la carte pour qu'elle te suive en temps réel !
        m.location = [lat, lon]

        # 2. Dessiner TES traces de pas (Point Bleu)
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.8,
            popup=f"Position à {heure}"
        ).add_to(groupe_trajet)

        # 3. Placer le routeur autour de toi (S'il n'est pas déjà sur la carte)
        if mac not in reseaux_places:
            if sec == "Ouvert": couleur, groupe_cible = "green", groupe_ouvert
            elif sec == "WEP": couleur, groupe_cible = "orange", groupe_wep
            elif sec == "WPA": couleur, groupe_cible = "lightred", groupe_wpa
            elif sec == "WPA2": couleur, groupe_cible = "red", groupe_wpa2
            elif sec == "WPA3": couleur, groupe_cible = "purple", groupe_wpa3
            else: couleur, groupe_cible = "gray", groupe_ouvert
                
            print(f"[📍 {sec:^6}] {heure} | {ssid} ({rssi} dBm) | Lat: {lat:.4f}")
            
            # --- MATHÉMATIQUES DU RADAR ---
            # Plus le signal est faible (ex: -90), plus on pousse le point loin du point bleu (jusqu'à ~90 mètres)
            # Plus le signal est fort (ex: -30), plus on le met près de toi (minimum 7 mètres)
            distance_metres = max(5, abs(rssi) - 30) * 1.5 
            offset_degres = distance_metres / 111320.0 # Conversion en degrés de latitude
            angle = random.uniform(0, 2 * math.pi) # Direction aléatoire (360 degrés)
            
            lat_wifi = lat + offset_degres * math.cos(angle)
            lon_wifi = lon + offset_degres * math.sin(angle)
            
            folium.Marker(
                location=[lat_wifi, lon_wifi],
                popup=f"<b>{ssid}</b><br>MAC: {mac}<br>Signal capté: {rssi} dBm<br>Sécurité: <b>{sec}</b>",
                icon=folium.Icon(color=couleur, icon="wifi", prefix='fa')
            ).add_to(groupe_cible)
            
            # On le note comme "placé" pour garder la carte propre
            reseaux_places.add(mac)
        
        m.save("carte_tactique.html")
        
except KeyboardInterrupt:
    print("\n[*] Arrêt du MapListener. Carte finale sauvegardée.")
