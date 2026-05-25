# =============================================
# config.py - Configuration centralisée du projet
# =============================================

# --- Intervalles (en millisecondes) ---
DISPLAY_INTERVAL = 5 * 1000      # 5 secondes
SAVE_INTERVAL = 300 * 1000       # 5 minutes
SLEEP_TIMEOUT = 30 * 1000        # 30 secondes d'inactivité
CACHE_INTERVAL = 60 * 1000       # 1 minute (cache des données)
STATS_INTERVAL = 10 * 60 * 1000  # 10 minutes (cache des stats)

# --- Chemins des fichiers ---
DATA_FILE = "data.csv"
BACKUP_FILE = "data_backup.csv"
TEMP_FILE = "data_temp.csv"

# --- Configuration du stockage ---
MAX_FLASH_USAGE = 0.7  # 70% max de l'espace flash
FLASH_SIZE = 2 * 1024 * 1024  # 2 Mo
MAX_FILE_SIZE = int(MAX_FLASH_USAGE * FLASH_SIZE)

# --- En-tête CSV ---
CSV_HEADER = "timestamp,temperature,humidity,pressure,gas,iaq\n"
LINE_FORMAT = "{},{:.2f},{:.2f},{:.2f},{},{}\n"

# --- Configuration de l'affichage ---
WIDTH = 240
HEIGHT = 135

# --- Broches matérielles ---
BUTTON_PINS = {
    "A": 12,
    "B": 13,
    "X": 14,
    "Y": 15
}

BACKLIGHT_PIN = 20
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

# --- Plages de valeurs valides pour les capteurs ---
SENSOR_RANGES = {
    "temp": (0, 50),       # °C
    "hum": (0, 100),       # %
    "press": (900, 1100),  # hPa
    "gas": (0, 1000000),   # Résistance gaz (ohms)
    "iaq": (0, 500)        # Indice qualité air
}

# --- Unités des métriques ---
UNITS = {
    "temperature": "°C",
    "humidity": "%",
    "pressure": "hPa",
    "iaq": "",
    "gas": "Ω"
}

# --- Noms affichables des métriques ---
METRIC_NAMES = {
    "temperature": "Température",
    "humidity": "Humidité",
    "pressure": "Pression",
    "iaq": "IAQ",
    "gas": "Gaz"
}

# --- Couleurs par défaut pour chaque métrique ---
METRIC_COLORS = {
    "temperature": "TEMP",
    "humidity": "HUM",
    "pressure": "PRESS",
    "iaq": "IAQ_GOOD"
}

# --- Configuration des histogrammes ---
HISTOGRAM_HEIGHT = 80  # Hauteur de la zone de l'histogramme
VALUE_DISPLAY_HEIGHT = 30  # Hauteur de la zone d'affichage de la valeur
HISTOGRAM_BAR_WIDTH = 4  # Largeur de chaque barre de l'histogramme
HISTOGRAM_BAR_SPACING = 1  # Espacement entre les barres
HISTOGRAM_MAX_BARS = 50  # Nombre maximum de barres à afficher