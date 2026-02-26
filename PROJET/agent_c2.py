from scapy.all import *
import time
import os
import threading
import json
import sys

INTERFACE = "wlan1"
noms_reseaux_vus = []

def activer_mode_moniteur():
    # On ordonne à NetworkManager d'ignorer totalement l'antenne Alfa (wlan1)
    os.system(f"nmcli dev set {INTERFACE} managed no > /dev/null 2>&1")
    time.sleep(0.5)
    
    # On configure le mode moniteur
    os.system(f"ip link set {INTERFACE} down > /dev/null 2>&1")
    os.system(f"iw dev {INTERFACE} set type monitor > /dev/null 2>&1")
    os.system(f"ip link set {INTERFACE} up > /dev/null 2>&1")
    
    # Pause cruciale pour laisser la carte s'allumer
    time.sleep(1)

def hop_channels():
    channels = [1, 6, 11, 36, 40, 44, 48, 149, 153, 157, 161]
    while True:
        for ch in channels:
            os.system(f"iwconfig {INTERFACE} channel {ch} > /dev/null 2>&1")
            time.sleep(0.5)

def packet_handler(pkt):
    if pkt.haslayer(Dot11Beacon):
        try:
            ssid = pkt[Dot11Elt].info.decode(errors="ignore").strip()
            bssid = pkt[Dot11].addr2
            
            try:
                rssi = pkt.dBm_AntSignal
            except:
                rssi = -100

            if not ssid or "\x00" in ssid:
                ssid = "[RÉSEAU MASQUÉ]"

            if ssid in noms_reseaux_vus and ssid != "[RÉSEAU MASQUÉ]":
                return
            if ssid == "[RÉSEAU MASQUÉ]" and bssid in noms_reseaux_vus:
                return

            noms_reseaux_vus.append(ssid if ssid != "[RÉSEAU MASQUÉ]" else bssid)

            securite = "Ouvert"
            cap = pkt.sprintf("{Dot11Beacon:%Dot11Beacon.cap%}")
            
            if "privacy" in cap.lower():
                securite = "WEP" 
                
                elt = pkt[Dot11Elt]
                has_wpa = False
                has_rsn = False
                is_wpa3 = False
                
                while isinstance(elt, Dot11Elt):
                    if elt.ID == 48: 
                        has_rsn = True
                        if b'\x00\x0f\xac\x08' in elt.info:
                            is_wpa3 = True
                    elif elt.ID == 221 and elt.info.startswith(b'\x00P\xf2\x01'): 
                        has_wpa = True
                    elt = elt.payload

                if is_wpa3:
                    securite = "WPA3"
                elif has_rsn:
                    securite = "WPA2"
                elif has_wpa:
                    securite = "WPA"

            donnees = {
                "heure": time.strftime("%H:%M:%S"),
                "ssid": ssid,
                "mac": bssid,
                "rssi": rssi,
                "sec": securite
            }
            
            print(json.dumps(donnees))
            sys.stdout.flush()
                    
        except Exception:
            pass

if __name__ == "__main__":
    activer_mode_moniteur()
    
    t = threading.Thread(target=hop_channels)
    t.daemon = True
    t.start()
    
    try:
        sniff(iface=INTERFACE, prn=packet_handler, store=0)
    except KeyboardInterrupt:
        os._exit(0)
