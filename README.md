# 📡 War-Walking Device — Système de cartographie Wi-Fi (v1.0)
### -*English will follow*-
> **Projet d'intégration en Sciences, informatique et mathématiques (420-SF4-RE)**
>
> *Cégep de Saint-Jérôme — Présenté à M. Éric Gagné (Hiver / Printemps 2026)*
>
> **Auteur :** Félix Danakas Pruneau *(en collaboration avec Anthony)*

---

## 📋 Présentation du projet

Ce projet consiste en la création d'une version 1.0 d'un système de cartographie Wi-Fi désigné dans le milieu de la cybersécurité sous le nom de **« War-Walking Device »**. Plutôt que de développer une simple application logicielle, l'objectif était de concevoir de A à Z une **infrastructure matérielle complète d'audit réseau** s'apparentant à un serveur de commande et contrôle (**C2**).

Ce système autonome utilise un **Raspberry Pi 4** pour écouter de manière totalement passive les réseaux sans fil environnants ($\text{IEEE } 802.11$) dans un périmètre défini, sans jamais avoir besoin de s'y connecter. L'outil intercepte les signaux bruts (**ESSID**, **adresse MAC**, **protocole de sécurité**, **force du signal RSSI**), les croise en temps réel avec les coordonnées GPS d'un téléphone mobile et identifie les fabricants des équipements afin d'afficher le tout sur une interface cartographique claire et non encombrée.

---

## 🏗️ Architecture et ressources matérielles / logicielles

Le système sépare l'acquisition des données sur le terrain (le Raspberry Pi 4) de leur traitement analytique (l'ordinateur principal) à travers un réseau privé virtuel (**VPN**) et un **tunnel SSH** sécurisé :

```
+------------------------------------+          +------------------------------------+
|       NOEUD TERRAIN (Mobile)       |          |     RELAIS MOBILE & GPS (iOS)      |
|                                    |          |                                    |
|  [Antenne externe Alfa Network]    | HOTSPOT  |  [iPhone - Hotspot Prioritaire]    |
|     | (Mode Monitor 802.11)        | <------> |     |                              |
|     v                              |          |     | Navigateur Safari (HTML5)    |
|  [Raspberry Pi 4 - Kali Linux]     |          |     | Envoi GPS via tunnel TLS     |
|     - Mode sans écran (Headless)   |          +-----|------------------------------+
|     - Batterie externe (5V / 3A)   |                |
+-----------------|------------------+                | HTTPS / SSL (Port 4443)
                  |                                   | (cert.pem / key.pem)
                  | Tunnel SSH (via VPN)              |
                  v                                   v
+------------------------------------------------------------------------------------+
|                       ORDINATEUR PRINCIPAL / POSTE C2 (MacBook)                    |
|                                                                                    |
|  [MapListener.py — Serveur Python Multi-threadé (ThreadingHTTPServer)]             |
|     ├── Fusion des trames radio (RF) et des coordonnées GPS en temps réel          |
|     ├── Regroupement des réseaux virtuels (2.4 GHz / 5 GHz) par préfixe MAC        |
|     ├── Identification hors-ligne des constructeurs (Base IEEE OUI / arp-scan)     |
|     └── Calcul du centre de masse pondéré (RSSI) & détection immobile / mouvement  |
|                                                                                    |
|  Sorties :  [La « Boîte Noire » (.csv)]   |   [Temps réel (.json)] ---> [Carte Web]|
+------------------------------------------------------------------------------------+
```

### Arsenal matériel et logiciel
* **Station centrale d'acquisition :** Raspberry Pi 4 roulant sous **Kali Linux** en mode sans écran (*headless*), alimenté sur le terrain par une batterie externe fournissant au minimum $5\text{ V}$ et $3\text{ A}$.
* **Captation radio :** Antenne réseau externe **Alfa Network** basculée en mode *Monitor*.
* **Poste de commandement :** Ordinateur principal (**MacBook**) opérant le système à distance via un tunnel **SSH** sur **VPN** et exécutant le compilateur Python `MapListener.py`.
* **Module GPS & connectivité terrain :** **iPhone** générant un point d'accès Wi-Fi (*hotspot*) auquel le Raspberry Pi se connecte automatiquement en priorité dès sa mise sous tension, tout en transmettant sa position GPS via le navigateur **Safari**.
* **Environnement logiciel & sécurité :** Python (`ThreadingHTTPServer`, `http.server`, `ssl`), certificats cryptographiques locaux (`cert.pem`, `key.pem`) et base de données OSINT publique de l'**IEEE** (`ieee-oui.txt` issu du projet open source `arp-scan`).

---

## ⚙️ Présentation des modules réalisés

### 1. Module d'interception réseau (Antenne en mode Monitor)
* **Rôle :** Ce module agit comme les « oreilles » de l'infrastructure d'audit. Par l'injection de commandes Linux de bas niveau, il force l'interface physique de l'antenne Alfa Network à passer d'une écoute ciblée à une écoute globale (**mode Monitor**).
* **Fonctionnement :** Il aspire de manière furtive et passive l'ensemble des paquets Wi-Fi en transit dans l'air sur tous les canaux (ESSID, adresse MAC, puissance $\text{RSSI}$ en $\text{dBm}$ et niveau de sécurité : **Ouvert**, **WEP**, **WPA**, **WPA2**, **WPA3**) et les injecte dans le tunnel SSH vers l'ordinateur principal.

### 2. Module de télémétrie GPS (Serveur HTTPS local sécurisé)
* **Rôle :** Il agit comme un pont de communication chiffré pour récupérer la position physique exacte de l'opérateur mobile en temps réel.
* **Fonctionnement :** Suite à l'abandon de l'application tierce payante *GPS2IP Lite*, un serveur web Python multi-threadé (`ThreadingHTTPServer`) a été implémenté. Afin de contourner les politiques de sécurité strictes d'Apple et le pare-feu de Safari — qui bloquent l'envoi des coordonnées GPS vers un serveur local non sécurisé — des certificats SSL locaux (`cert.pem`, `key.pem`) ont été générés pour encapsuler le trafic dans un tunnel **TLS (HTTPS)** sur le port `4443`.

### 3. Module de renseignement OSINT (Dictionnaire IEEE hors-ligne)
* **Rôle :** Ce filtre d'enrichissement se place entre la captation brute et l'affichage cartographique afin d'identifier les fabricants des équipements réseau détectés.
* **Fonctionnement :** Le système analyse de manière entièrement déconnectée les premiers caractères hexadécimaux (**OUI**) des adresses MAC interceptées en les croisant avec le fichier `ieee-oui.txt` nettoyé par le projet GitHub *arp-scan*. Le radar dispose ainsi d'une base locale de plus de $50\,000$ identifiants réels (Apple, Cisco, Bell, Vidéotron, etc.) exploitable sans aucune connexion Internet.

### 4. Module d'intelligence géographique & « Boîte Noire » (`MapListener.py`)
* **Fusion et déduplication matérielle :** Le script `MapListener.py` fusionne les données radio avec les coordonnées GPS reçues et nettoie les doublons. Comme les routeurs modernes diffusent simultanément plusieurs réseaux virtuels ($2.4\text{ GHz}$, $5\text{ GHz}$, réseaux invités), le programme lit uniquement le préfixe matériel de l'adresse MAC afin de regrouper tous les signaux d'un même routeur physique en un seul point.
* **Triangulation par centre de masse (RSSI) :** Plutôt que de placer le point d'accès à l'endroit exact où se trouve l'utilisateur, l'algorithme calcule le centre physique de l'émission en utilisant la force du signal ($\text{RSSI}$) comme poids, tout en mémorisant les coordonnées GPS au moment où la puissance captée est maximale.
* **Résolution adaptative du « Spiderweb » :** Pour éviter l'empilement illisible des points en zone dense, le module différencie l'état de l'utilisateur :
  * *Utilisateur immobile :* Les points détectés se déploient visuellement en couronne autour de lui pour permettre de cliquer sur chaque réseau.
  * *Utilisateur en mouvement :* Les cibles se placent progressivement aux endroits triangulés selon l'intensité du signal.
* **Sorties et interface web :**
  * **La « Boîte Noire » (`.csv`) :** Fichier d'historique sauvegardant en continu toutes les cibles confirmées pour une analyse ultérieure.
  * **Carte interactive temps réel (`.json` / HTML) :** Affichage coloré selon la vulnérabilité du protocole de chiffrement, muni d'un **mécanisme de pause** permettant de geler l'actualisation lors de l'inspection d'une grappe (*cluster*).

---

## 🛠️ Défis techniques rencontrés et solutions apportées

| Obstacle rencontré | Cause technique | Solution mise en place |
| :--- | :--- | :--- |
| **Blocage du GPS par Safari / iOS** | L'abandon de *GPS2IP Lite* (payant) obligeait à passer par le navigateur, mais iOS exige HTTPS pour la géolocalisation. | Génération manuelle de certificats (`cert.pem`, `key.pem`) et mise en place d'un serveur Python multi-threadé en **HTTPS sur le port `4443`**. |
| **Nuage chaotique autour des maisons** | Chaque routeur physique diffusait plusieurs BSSID ($2.4\text{ GHz}$, $5\text{ GHz}$, réseau invité), éparpillant les points. | Modification de `MapListener.py` pour fusionner les signaux à partir du **préfixe matériel de l'adresse MAC**. |
| **Effet « Spiderweb » sur la carte** | La forte densité de réseaux superposait les marqueurs les uns sur les autres. | Création d'un algorithme basculant entre un **déploiement en couronne (à l'arrêt)** et une **triangulation RSSI (en mouvement)**. |
| **Instabilité visuelle lors des clics** | Le rafraîchissement temps réel du `.json` faisait « glitcher » l'interface pendant la lecture d'une grappe. | Implémentation d'un **mécanisme de pause** pour figer l'affichage lors de l'inspection. |

---

## 🔬 Apport des disciplines du programme SIM

Ce projet d'intégration mobilise directement les trois piliers du programme *Sciences, informatique et mathématiques* :

1. **Informatique :** Programmation orientée objet en Python, gestion de requêtes concurrentes avec `ThreadingHTTPServer`, administration système sous Kali Linux, architecture réseau sécurisée (tunnels SSH sur VPN) et gestion de certificats cryptographiques SSL/TLS.
2. **Physique :** Captation passive d'ondes radiofréquences, compréhension de la physique ondulatoire, de l'atténuation des signaux dans l'air et à travers les matériaux, ainsi que l'interprétation de la puissance du signal ($\text{RSSI}$ mesuré en $\text{dBm}$).
3. **Mathématiques :** Traitement des adresses MAC reposant sur le système **hexadécimal (base 16)**, analyse d'une **échelle logarithmique et non linéaire** pour l'atténuation du $\text{RSSI}$ en $\text{dBm}$, et calcul de **centre de masse pondéré** pour estimer la position des émetteurs.

---

## 🧪 Tests terrain, bilan critique et pistes d'amélioration

### Validation sur le terrain
* **Test d'architecture mobile :** Raspberry Pi alimenté par batterie dans un sac à dos, relié au *hotspot* de l'iPhone — transmission fluide des trames JSON en temps réel via le tunnel SSH.
* **Marche d'essai en quartier résidentiel :** Identification de la duplication des bandes $2.4\text{ GHz}$ / $5\text{ GHz}$ et validation du regroupement par préfixe MAC.
* **Déplacement dans le Cégep de Saint-Jérôme :** Suivi en direct du trajet de l'opérateur et actualisation simultanée de la carte sur le téléphone connecté au VPN.

### Forces et limites observées
* **Forces :** Autonomie opérationnelle complète. Le système ne dépend d'aucune API externe ni d'aucun abonnement payant ; tout le traitement s'effectue en local, le rendant furtif et intraçable pour un audit de sécurité (*Red Team*) ou la vérification des fuites de signaux Wi-Fi hors d'un périmètre physique.
* **Limites :** Dépendance énergétique et de routage envers le point d'accès de l'iPhone (nécessitant une couverture cellulaire pour maintenir le VPN), précision de la puce GPS du téléphone à proximité de grands bâtiments, et portée limitée à l'écoute passive (sans injection de paquets).

### Amélioration future (Roadmap v2.0)
* **Boîtier 100 % autonome :** Intégrer un **module GPS physique** directement sur les broches matérielles (GPIO) du Raspberry Pi 4 afin d'éliminer complètement la dépendance au *hotspot* de l'iPhone et la gestion des certificats SSL pour le navigateur.


---
## English documentation

# 📡 War-Walking Device — Wi-Fi Mapping System (v1.0)

> **Capstone Integration Project in Science, Computer Science, and Mathematics (SIM — 420-SF4-RE)**
>
> *Cégep de Saint-Jérôme — Submitted to Mr. Éric Gagné (Winter / Spring 2026)*
>
> **Author:** Félix Danakas Pruneau *(in collaboration with Anthony)*

## 📋 Project Overview

This project consists of creating version 1.0 of a Wi-Fi mapping system commonly referred to in the cybersecurity field as a **“War-Walking Device.”** Rather than developing a simple software application, the main objective was to design an end-to-end **complete hardware network auditing infrastructure** resembling a Command and Control (**C2**) server.

This autonomous system uses a **Raspberry Pi 4** to passively listen to surrounding wireless networks ($\text{IEEE } 802.11$) within a defined perimeter, without ever needing to connect to them. The tool intercepts raw signals (**ESSID**, **MAC address**, **security protocol**, **RSSI signal strength**), cross-references them in real time with GPS coordinates from a mobile phone, and identifies hardware manufacturers to display everything on a clean, uncluttered map interface.

## 🏗️ Architecture and Hardware / Software Resources

The system decouples field data acquisition (the Raspberry Pi 4) from analytical processing (the host computer) over a Virtual Private Network (**VPN**) and a secure **SSH tunnel**:

```
+------------------------------------+          +------------------------------------+
|       FIELD NODE (Mobile)          |          |     MOBILE RELAY & GPS (iOS)       |
|                                    |          |                                    |
|  [External Alfa Network Antenna]   | HOTSPOT  |  [iPhone - Priority Hotspot]       |
|     | (802.11 Monitor Mode)        | <------> |     |                              |
|     v                              |          |     | Safari Browser (HTML5)       |
|  [Raspberry Pi 4 - Kali Linux]     |          |     | GPS uplink via TLS tunnel    |
|     - Headless mode (no display)   |          +-----|------------------------------+
|     - External battery (5V / 3A)   |                | HTTPS / SSL (Port 4443)
+-----------------|------------------+                | (cert.pem / key.pem)
                  |                                   |
                  | SSH Tunnel (over VPN)             |
                  v                                   v
+------------------------------------------------------------------------------------+
|                        HOST COMPUTER / C2 STATION (MacBook)                        |
|                                                                                    |
|  [MapListener.py — Multi-threaded Python Server (ThreadingHTTPServer)]             |
|     ├── Real-time fusion of radio frequency (RF) frames and GPS coordinates        |
|     ├── Grouping of virtual networks (2.4 GHz / 5 GHz) by MAC address prefix       |
|     ├── Offline vendor identification (IEEE OUI / arp-scan local database)         |
|     └── Weighted center-of-mass calculation (RSSI) & stationary/moving detection   |
|                                                                                    |
|  Outputs:  [The "Black Box" (.csv)]    |    [Real-time (.json)] ---> [Web Map]     |
+------------------------------------------------------------------------------------+
```

### Hardware and Software Arsenal

* **Central Acquisition Station:** Raspberry Pi 4 running **Kali Linux** in headless mode, powered in the field by an external battery pack delivering at least $5\text{ V}$ and $3\text{ A}$.

* **Radio Capture:** External **Alfa Network** wireless adapter switched into *Monitor* mode.

* **Command Station:** Host computer (**MacBook**) operating the system remotely over an **SSH** tunnel via **VPN** and running the Python compiler `MapListener.py`.

* **GPS Module & Field Connectivity:** **iPhone** generating a Wi-Fi hotspot to which the Raspberry Pi automatically connects with top priority upon boot, while transmitting its GPS coordinates through the **Safari** browser.

* **Software & Security Environment:** Python (`ThreadingHTTPServer`, `http.server`, `ssl`), locally generated cryptographic certificates (`cert.pem`, `key.pem`), and the public **IEEE** OSINT database (`ieee-oui.txt` sourced from the open-source `arp-scan` project).

## ⚙️ Implemented Modules Overview

### 1. Network Interception Module (Antenna in Monitor Mode)

* **Role:** This module acts as the “ears” of the auditing infrastructure. By injecting low-level Linux commands, it forces the Alfa Network physical wireless interface to switch from targeted listening to global listening (**Monitor mode**).

* **Operation:** It stealthily and passively captures all Wi-Fi packets in transit across all channels (ESSID, MAC address, $\text{RSSI}$ signal strength in $\text{dBm}$, and security protocol: **Open**, **WEP**, **WPA**, **WPA2**, **WPA3**) and injects them into the SSH tunnel toward the host computer.

### 2. GPS Telemetry Module (Secure Local HTTPS Server)

* **Role:** Acts as an encrypted communication bridge to retrieve the mobile operator's exact physical location in real time.

* **Operation:** Following the abandonment of the paid third-party app *GPS2IP Lite*, a multi-threaded Python web server (`ThreadingHTTPServer`) was implemented. To bypass Apple's strict security policies and Safari's firewall—which block transmitting GPS coordinates to an unencrypted local server—local SSL certificates (`cert.pem`, `key.pem`) were generated to encapsulate traffic inside a **TLS (HTTPS)** tunnel on port `4443`.

### 3. OSINT Intelligence Module (Offline IEEE Dictionary)

* **Role:** This data-enrichment filter sits between raw packet capture and map rendering to identify the manufacturers of detected network devices.

* **Operation:** The system performs completely offline lookups of the first hexadecimal octets (**OUI**) of intercepted MAC addresses against the `ieee-oui.txt` file curated by the GitHub *arp-scan* project. This equips the radar with a local database of over $50,000$ real vendor identifiers (Apple, Cisco, Bell, Vidéotron, etc.) usable without any Internet connection.

### 4. Geospatial Intelligence Module & “Black Box” (`MapListener.py`)

* **Hardware Fusion & Deduplication:** The `MapListener.py` script merges incoming radio data with GPS coordinates and removes duplicates. Because modern routers simultaneously broadcast multiple virtual networks ($2.4\text{ GHz}$, $5\text{ GHz}$, guest networks), the program reads only the hardware prefix of the MAC address to consolidate all signals from a single physical router into one point.

* **Center-of-Mass Triangulation (RSSI):** Rather than placing an access point at the user's exact location, the algorithm computes the physical center of emission using signal strength ($\text{RSSI}$) as a weight, while recording the GPS coordinates where peak signal strength was observed.

* **Adaptive “Spiderweb” Resolution:** To prevent unreadable marker stacking in high-density areas, the module distinguishes between user motion states:

  * *Stationary user:* Detected access points visually fan out in a ring around the user so every network remains clickable.

  * *Moving user:* Targets progressively converge onto their triangulated positions based on signal intensity.

* **Outputs and Web Interface:**

  * **The “Black Box” (`.csv`):** Continuous history log saving all confirmed targets for post-mission analysis.

  * **Real-Time Interactive Map (`.json` / HTML):** Color-coded display categorized by encryption vulnerability, equipped with a **pause mechanism** to freeze live updates while inspecting a cluster.

## 🛠️ Technical Challenges and Solutions

| Obstacle Encountered | Technical Cause | Implemented Solution |
| :--- | :--- | :--- |
| **GPS Blocked by Safari / iOS** | Abandoning *GPS2IP Lite* (paid) required using the web browser, but iOS enforces HTTPS for geolocation. | Manually generated certificates (`cert.pem`, `key.pem`) and deployed a multi-threaded Python **HTTPS server on port `4443`**. |
| **Chaotic Cloud Around Houses** | Each physical router broadcast multiple BSSIDs ($2.4\text{ GHz}$, $5\text{ GHz}$, guest network), scattering markers. | Modified `MapListener.py` to merge signals using the **hardware MAC address prefix**. |
| **“Spiderweb” Effect on the Map** | High network density caused markers to stack directly on top of one another. | Built an adaptive algorithm switching between a **ring layout (when stationary)** and **RSSI triangulation (when moving)**. |
| **Visual Instability When Clicking** | Real-time `.json` refreshes caused UI glitches while inspecting a cluster. | Implemented a **pause mechanism** to freeze map updates during inspection. |

## 🔬 Integration of SIM Program Disciplines

This capstone project directly applies the three core pillars of the *Science, Computer Science, and Mathematics (SIM)* program:

1. **Computer Science:** Object-oriented programming in Python, concurrent request handling with `ThreadingHTTPServer`, system administration under Kali Linux, secure network architecture (SSH tunnels over VPN), and SSL/TLS cryptographic certificate management.

2. **Physics:** Passive capture of radio frequency waves, understanding wave physics, signal attenuation through air and building materials, and interpreting signal power ($\text{RSSI}$ measured in $\text{dBm}$).

3. **Mathematics:** Processing MAC addresses grounded in the **hexadecimal (base-16)** number system, analyzing a **logarithmic and non-linear scale** for $\text{RSSI}$ attenuation in $\text{dBm}$, and computing a **weighted center of mass** to estimate emitter locations.

## 🧪 Field Testing, Critical Assessment, and Future Improvements

### Field Validation

* **Mobile Architecture Test:** Battery-powered Raspberry Pi carried inside a backpack, tethered to the iPhone hotspot—smooth real-time transmission of JSON frames over the SSH tunnel.

* **Residential Neighborhood Walk Test:** Identified $2.4\text{ GHz}$ / $5\text{ GHz}$ band duplication and validated MAC prefix grouping.

* **Indoor Walk at Cégep de Saint-Jérôme:** Live tracking of the operator's path with simultaneous real-time map updates directly on the VPN-connected phone.

### Observed Strengths and Limitations

* **Strengths:** Complete operational autonomy. The system relies on no external APIs and no paid subscriptions; all processing runs locally, keeping it stealthy and untraceable for security auditing (*Red Team*) or verifying Wi-Fi signal leakage beyond a physical security perimeter.

* **Limitations:** Power and routing dependency on the iPhone hotspot (requiring cellular coverage to maintain the VPN), smartphone GPS accuracy degradation near large buildings, and scope limited to passive listening (no packet injection).

### Future Improvement (Roadmap v2.0)

* **100% Standalone Enclosure:** Integrate a **physical GPS module** directly onto the Raspberry Pi 4 hardware GPIO pins to completely eliminate reliance on the iPhone hotspot and browser SSL certificate management.
