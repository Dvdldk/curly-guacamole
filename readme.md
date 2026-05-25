# Station Météo BME680 + Pico Display

Une station météo complète avec capteur BME680 pour mesurer la température, l'humidité, la pression atmosphérique et la qualité de l'air intérieur (IAQ).

---

## 📋 Fonctionnalités

- **Mesures en temps réel** : Température, humidité, pression, IAQ
- **Affichage graphique** : Barres de progression colorées avec min/max
- **Stockage des données** : Sauvegarde automatique en CSV toutes les 5 minutes
- **Statistiques** : Affichage des min/max/moyennes sur 24h, 7j, 30j
- **Menu interactif** : Navigation hiérarchique avec boutons A/B/X/Y
- **Mode veille** : Économise la batterie après 30 secondes d'inactivité
- **Réglage de l'heure** : Configuration manuelle de la date et de l'heure
- **Export des données** : Récupération du fichier CSV via Thonny

---

## 🎨 Améliorations Apportées

### Esthétique & Lisibilité
- **Palette de couleurs optimisée** : Contraste amélioré pour une meilleure lisibilité
- **Barres de progression** : Avec dégradé de couleurs pour l'IAQ (vert → rouge)
- **Hiérarchie visuelle** : Titres, sous-titres et texte distincts
- **Écran de démarrage** : Splash screen professionnel
- **Feedback utilisateur** : Messages clairs et légendes des boutons

### Ergonomie
- **Navigation intuitive** : Menu hiérarchique avec sous-menus
- **Légende des boutons** : Affichée en bas de chaque écran
- **Écrans de confirmation** : Pour les actions critiques (effacer données)
- **Saisie guidée** : Configuration de l'heure avec surlignage du champ actif

### Fiabilité
- **Validation des données** : Vérification des plages de valeurs du capteur
- **Sauvegarde atomique** : Écriture dans un fichier temporaire avant renommage
- **Réparation CSV** : Détection et correction automatique des lignes corrompues
- **Gestion des erreurs centralisée** : Messages clairs à l'écran
- **Mode factice** : Fonctionnement même sans capteur physique

### Performances
- **Cache des données** : Mise à jour toutes les 1 minute
- **Cache des statistiques** : Pré-calcul toutes les 10 minutes
- **Rafraîchissement conditionnel** : Ne rafraîchit que si les données changent

---

## 📁 Structure du Projet

curly-guacamole/
├── main.py          # Boucle principale et gestion globale
├── display.py       # Gestion de l'affichage (UI)
├── sensor.py        # Lecture et validation des données du capteur
├── storage.py       # Stockage CSV avec sauvegarde atomique
├── menu.py          # Navigation et actions du menu
├── utils.py         # Fonctions utilitaires (couleurs, temps, etc.)
└── README.md        # Documentation

---

## 🔧 Matériel Requis

| Composant | Broche | Description |
|-----------|--------|-------------|
| Raspberry Pi Pico | - | Microcontrôleur |
| Pico Display | SPI | Écran 240x135 |
| BME680 Breakout | I2C (SDA:4, SCL:5) | Capteur environnemental |
| Bouton A | 12 | Incrémenter / Sélection rapide |
| Bouton B | 13 | Décrémenter / Sélection rapide |
| Bouton X | 14 | Valider / Sélectionner |
| Bouton Y | 15 | Menu / Retour |
| Rétroéclairage | 20 | PWM pour la luminosité |

---

## 🚀 Installation

1. **Copier les fichiers** sur votre Raspberry Pi Pico :
   ```bash
   # Depuis Thonny ou en ligne de commande
   # Copier tous les fichiers .py et README.md

   Installer les bibliothèques requises :
      picographics
      pimoroni_i2c
      breakout_bme68x

✅ Ces bibliothèques sont normalement incluses avec les exemples Pimoroni pour le Raspberry Pi Pico.
