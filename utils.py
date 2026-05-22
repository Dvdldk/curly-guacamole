# =============================================
# utils.py - Fonctions utilitaires pour la station météo
# Gestion des couleurs, du temps, et des erreurs
# =============================================

from machine import Pin, PWM
import time

# --- Constantes globales ---
WIDTH = 240
HEIGHT = 135

# --- Gestion des couleurs RGB565 ---
def rgb565(r, g, b):
    """Convertit RGB (0-255) en RGB565 (16-bit)."""
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3

# --- Palette de couleurs améliorée ---
COLORS = {
    # Couleurs de base
    "BG": rgb565(10, 10, 20),          # Fond noir profond
    "TEXT": rgb565(240, 240, 255),     # Texte blanc légèrement bleuté
    "TITLE": rgb565(100, 200, 255),    # Bleu clair pour les titres
    "SUBTITLE": rgb565(150, 150, 255), # Sous-titres

    # Couleurs pour les barres
    "TEMP": rgb565(0, 180, 255),       # Bleu (froid)
    "HUM": rgb565(0, 220, 255),        # Cyan (eau)
    "PRESS": rgb565(255, 150, 0),     # Orange (pression)
    "IAQ_GOOD": rgb565(0, 255, 0),    # Vert (bon IAQ)
    "IAQ_MEDIUM": rgb565(255, 255, 0), # Jaune (moyen)
    "IAQ_BAD": rgb565(255, 0, 0),      # Rouge (mauvais)

    # Couleurs pour les messages
    "SUCCESS": rgb565(0, 255, 0),      # Vert (succès)
    "WARNING": rgb565(255, 165, 0),    # Orange (avertissement)
    "ERROR": rgb565(255, 0, 0),        # Rouge (erreur)
    "INFO": rgb565(0, 200, 255),       # Bleu (information)

    # Couleurs pour les boutons
    "BUTTON_A": rgb565(0, 255, 0),     # Vert
    "BUTTON_B": rgb565(255, 0, 0),     # Rouge
    "BUTTON_X": rgb565(0, 255, 255),   # Cyan
    "BUTTON_Y": rgb565(255, 255, 0),   # Jaune

    # Couleurs pour les menus
    "MENU_SELECTED": rgb565(255, 255, 0), # Jaune (sélectionné)
    "MENU_UNSELECTED": rgb565(100, 100, 255), # Bleu clair (non sélectionné)

    # Gris pour les séparateurs et arrière-plans
    "GRAY_DARK": rgb565(50, 50, 50),   # Gris foncé
    "GRAY_MEDIUM": rgb565(100, 100, 100), # Gris moyen
    "GRAY_LIGHT": rgb565(150, 150, 150), # Gris clair
}

# --- Palette IAQ avec dégradé visuel ---
IAQ_COLORS = {
    (0, 50): COLORS["IAQ_GOOD"],        # Vert (excellent)
    (51, 100): rgb565(100, 255, 100),   # Vert clair
    (101, 150): COLORS["IAQ_MEDIUM"],   # Jaune (moyen)
    (151, 200): rgb565(255, 165, 0),    # Orange
    (201, 250): rgb565(255, 100, 0),    # Orange foncé
    (251, 350): COLORS["IAQ_BAD"],      # Rouge
    (351, 500): rgb565(150, 0, 0),      # Rouge foncé
}

# Couleurs pour les barres par type de donnée
BAR_COLORS = {
    "temp": COLORS["TEMP"],
    "hum": COLORS["HUM"],
    "press": COLORS["PRESS"],
}

# --- Symboles Unicode pour l'affichage ---
SYMBOLS = {
    "temp": "\u2103",  # °C
    "hum": "%",
    "press": "hPa",
    "iaq": "",
    "check": "\u2713",  # ✓
    "cross": "\u2717", # ✗
    "arrow_right": "\u2192", # →
    "thermometer": "\u1F321", # 🌡️ (peut ne pas être supporté)
    "droplet": "\u1F4A7",      # 💧
    "gauge": "\u1F3F8",        # 🏸 (approximation)
}

# --- Gestion du rétroéclairage ---
class BacklightManager:
    """Gère le rétroéclairage de l'écran."""

    def __init__(self, pin=20):
        self.bl = PWM(Pin(pin))
        self.bl.freq(1000)
        self.set_brightness(100)  # 100% par défaut

    def set_brightness(self, percent):
        """Définit la luminosité (0-100%)."""
        duty = int(65535 * (percent / 100))
        self.bl.duty_u16(duty)

    def fade_out(self, duration=1.0):
        """Fondu vers l'éteint (pour le mode veille)."""
        steps = 20
        for i in range(steps, -1, -1):
            self.set_brightness(i * (100 / steps))
            time.sleep(duration / steps)

    def fade_in(self, duration=1.0):
        """Fondu depuis l'éteint."""
        steps = 20
        for i in range(0, steps + 1):
            self.set_brightness(i * (100 / steps))
            time.sleep(duration / steps)

# --- Gestion des erreurs ---
def handle_error(error, context="", display=None, color=None):
    """
    Gère les erreurs de manière centralisée.
    Affiche un message sur l'écran si disponible.
    """
    print(f"[{context}] Erreur: {error}")

    if display:
        error_msg = f"Erreur ({context}):\n{str(error)[:40]}"
        display.show_message(error_msg, color or COLORS["ERROR"])

# --- Fonctions de temps ---
def format_timestamp(year, month, day, hour, minute, second=None):
    """Formate un timestamp en chaîne lisible."""
    if second is not None:
        return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"

def get_max_day(month, year):
    """Retourne le nombre de jours dans un mois."""
    if month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
    else:
        return 31

def time_diff_ms(start, end):
    """Calcule la différence de temps en millisecondes."""
    return time.ticks_diff(end, start)

# --- Fonctions utilitaires pour les valeurs ---
def clamp(value, min_val, max_val):
    """Limite une valeur entre min_val et max_val."""
    return max(min_val, min(max_val, value))

def map_value(value, in_min, in_max, out_min, out_max):
    """Mappe une valeur d'une plage à une autre."""
    return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)

def is_valid_sensor_value(value_type, value):
    """Vérifie si une valeur de capteur est valide."""
    ranges = {
        "temp": (0, 50),      # °C
        "hum": (0, 100),      # %
        "press": (900, 1100), # hPa
        "gas": (0, 1000000),  # Résistance gaz (ohms)
        "iaq": (0, 500),      # Indice qualité air
    }
    if value_type in ranges:
        min_val, max_val = ranges[value_type]
        return min_val <= value <= max_val
    return True

# --- Constantes pour les tailles de texte ---
TEXT_SCALES = {
    "title": 3,
    "subtitle": 2,
    "label": 1,
    "value": 2,
    "small": 1,
}

# --- Constantes pour les marges et espacements ---
LAYOUT = {
    "margin_top": 10,
    "margin_left": 15,
    "margin_right": 15,
    "margin_bottom": 15,
    "line_spacing": 30,
    "bar_height": 25,
    "padding": 5,
}