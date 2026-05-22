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



⌨️ Commandes et Navigation
Écran Principal


  
    
      Bouton
      Action
    
  
  
    
      Y
      Ouvrir le menu principal
    
    
      X
      Rafraîchir les données du capteur
    
    
      A
      Afficher les statistiques 24h
    
    
      B
      Afficher les statistiques 7 jours
    
  
Dans le Menu


  
    
      Bouton
      Action
    
  
  
    
      X
      Sélectionner un élément
    
    
      Y
      Retour au menu précédent
    
    
      A
      Monter dans la liste
    
    
      B
      Descendre dans la liste
    


Saisie de l'Heure


  
    
      Bouton
      Action
    
  
  
    
      A
      Incrémenter la valeur (+1)
    
    
      B
      Décrémenter la valeur (-1)
    
    
      X
      Passer au champ suivant / Valider
    
    
      Y
      Annuler et revenir au menu
    
  
📊 Données Stockées
Les données sont sauvegardées dans le fichier data.csv avec le format suivant :
csv
Copier

timestamp,temperature,humidity,pressure,gas,iaq
2026-01-01 12:00,22.5,45.0,1013.25,150000,100
2026-01-01 12:05,22.6,44.8,1013.10,148000,95
  
    
      Champ
      Unité
      Description
    
  
  
    
      timestamp
      -
      Date et heure de la mesure
    
    
      temperature
      °C
      Température ambiante
    
    
      humidity
      %
      Humidité relative
    
    
      pressure
      hPa
      Pression atmosphérique
    
    
      gas
      Ω
      Résistance du gaz (VOC)
    
    
      iaq
      -
      Indice de Qualité de l'Air (0-500)
    


🔄 Intervalles de Fonctionnement

    
      Fonction
      Intervalle
      Description
    
  
  
    
      Affichage
      5 secondes
      Rafraîchissement des données à l'écran
    
    
      Sauvegarde CSV
      5 minutes
      Enregistrement des données dans le fichier
    
    
      Mode veille
      30 secondes
      Activation après inactivité
    
    
      Cache des stats
      10 minutes
      Mise à jour des statistiques en mémoire
    
    
      Cache des données
      1 minute
      Mise à jour du cache CSV
    
  

🛠️ Personnalisation
Modifier les Intervalles
Dans le fichier main.py, modifiez les constantes suivantes :
python
Copier

# Dans la classe WeatherStation.__init__()
self.DISPLAY_INTERVAL = 5 * 1000      # 5 secondes (en ms)
self.SAVE_INTERVAL = 300 * 1000        # 5 minutes (en ms)
self.SLEEP_TIMEOUT = 30 * 1000         # 30 secondes (en ms)



Changer les Couleurs
Dans le fichier utils.py, modifiez le dictionnaire COLORS :
python
Copier

COLORS = {
    "BG": rgb565(10, 10, 20),      # Fond noir profond
    "TEXT": rgb565(240, 240, 255), # Texte blanc légèrement bleuté
    "TITLE": rgb565(100, 200, 255), # Bleu clair pour les titres
    "TEMP": rgb565(0, 180, 255),    # Bleu pour la température
    "HUM": rgb565(0, 220, 255),     # Cyan pour l'humidité
    "PRESS": rgb565(255, 150, 0),   # Orange pour la pression
    # ... (autres couleurs)
}



Ajouter des Capteurs
Pour ajouter un nouveau capteur, étendez la classe SensorManager dans sensor.py :
python
Copier

class SensorManager:
    def __init__(self):
        # Initialisation des capteurs
        self.bme = BreakoutBME68X(...)  # Capteur existant
        self.new_sensor = NewSensor(...)  # Nouveau capteur

    def read_data(self):
        # Lire les données de tous les capteurs
        bme_data = self.bme.read_data()
        new_data = self.new_sensor.read_data()
        return {**bme_data, **new_data}




📊 Interprétation de l'IAQ
L'Indice de Qualité de l'Air (IAQ) est calculé à partir de la résistance du gaz (VOC) :


  
    
      IAQ
      Qualité
      Couleur
      Recommandation
    
  
  
    
      0-50
      Excellente
      🟢 Vert
      Air très pur
    
    
      51-100
      Bonne
      🟢 Vert clair
      Air de bonne qualité
    
    
      101-150
      Moyenne
      🟡 Jaune
      Qualité acceptable
    
    
      151-200
      Médiocre
      🟠 Orange
      Ventilation recommandée
    
    
      201-250
      Mauvaise
      🔴 Rouge
      Aérer la pièce
    
    
      251-350
      Très mauvaise
      🔴 Rouge foncé
      Éviter l'exposition
    
    
      351-500
      Dangereuse
      ⚫ Noir
      Quitter les lieux
    
  



🐛 Gestion des Erreurs
Le système gère automatiquement les erreurs courantes :


  
    
      Erreur
      Comportement
    
  
  
    
      Capteur déconnecté
      Passe en mode factice avec valeurs par défaut
    
    
      Fichier CSV corrompu
      Réparation automatique en supprimant les lignes invalides
    
    
      Espace disque plein
      Nettoyage automatique des anciennes données (garde 90%)
    
    
      Erreur d'affichage
      Message d'erreur clair à l'écran
    
    
      Erreur de lecture
      Affichage des dernières données valides
    
  



📝 Changelog
Version 1.0 (Optimisée)
✅ Refactorisation complète :

Structure modulaire (6 fichiers au lieu de 1)
Séparation des responsabilités (UI, capteur, stockage, menu)
✅ Améliorations esthétiques :

Palette de couleurs professionnelle
Barres de progression avec dégradé IAQ
Hiérarchie visuelle claire
✅ Améliorations ergonomiques :

Menu hiérarchique avec navigation intuitive
Légende des boutons affichée en permanence
Écrans de confirmation pour les actions critiques
✅ Améliorations techniques :

Sauvegarde atomique du CSV
Cache des données et statistiques
Mode veille pour économiser la batterie
Validation des données du capteur
✅ Documentation :

README.md complet avec toutes les informations
Commentaires détaillés dans le code
