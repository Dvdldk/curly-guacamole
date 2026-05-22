# =============================================
# display.py - Gestion de l'affichage
# Barres de progression, messages, et interface utilisateur
# =============================================

from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_RGB565
from machine import Pin, PWM
from utils import (
    COLORS, IAQ_COLORS, BAR_COLORS, SYMBOLS, TEXT_SCALES, LAYOUT,
    WIDTH, HEIGHT, rgb565, clamp, handle_error
)

class DisplayManager:
    """Gère tout l'affichage sur l'écran Pico Display."""

    def __init__(self, backlight_pin=20):
        # Initialisation de l'écran
        self.display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_RGB565)
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT

        # Gestion du rétroéclairage
        self.backlight = PWM(Pin(backlight_pin))
        self.backlight.freq(1000)
        self.set_backlight(100)  # 100% par défaut

        # État de l'affichage
        self.last_displayed_data = None
        self.in_sleep_mode = False

        # Historique des min/max pour les barres
        self.historical_min_max = {
            "temp": {"min": 0, "max": 40},
            "hum": {"min": 0, "max": 100},
            "press": {"min": 900, "max": 1100},
            "iaq": {"min": 0, "max": 500}
        }

    def set_backlight(self, percent):
        """Définit la luminosité du rétroéclairage (0-100%)."""
        duty = int(65535 * (percent / 100))
        self.backlight.duty_u16(duty)

    def clear(self):
        """Efface l'écran avec la couleur de fond."""
        self.display.set_pen(COLORS["BG"])
        self.display.clear()

    def update(self):
        """Met à jour l'affichage."""
        self.display.update()

    def draw_border(self):
        """Dessine une bordure autour de l'écran."""
        self.display.set_pen(COLORS["GRAY_DARK"])
        self.display.rectangle(0, 0, self.WIDTH, self.HEIGHT)

    def draw_separator(self, y):
        """Dessine une ligne de séparation horizontale."""
        self.display.set_pen(COLORS["GRAY_MEDIUM"])
        self.display.line(10, y, self.WIDTH - 10, y)

    def draw_horizontal_bar(self, y, label, value, min_val, max_val, is_iaq=False, unit=""):
        """
        Dessine une barre de progression horizontale avec label et valeur.
        """
        padding = LAYOUT["padding"]
        bar_height = LAYOUT["bar_height"]

        # Calculer la largeur de la barre
        if max_val > min_val:
            bar_width = max(0, int((value - min_val) / (max_val - min_val) * (self.WIDTH - 2 * padding)))
        else:
            bar_width = 0

        # Couleur de la barre
        if is_iaq:
            for (low, high), color in IAQ_COLORS.items():
                if low <= value <= high:
                    bar_color = color
                    break
            else:
                bar_color = IAQ_COLORS[(351, 500)]
        else:
            bar_color = BAR_COLORS.get(label.lower(), COLORS["TEXT"])

        # Dessiner la barre de fond (grise)
        self.display.set_pen(COLORS["GRAY_DARK"])
        self.display.rectangle(padding, y, self.WIDTH - 2 * padding, bar_height)

        # Dessiner la barre de progression
        self.display.set_pen(bar_color)
        self.display.rectangle(padding, y, bar_width, bar_height)

        # Afficher le label
        self.display.set_pen(COLORS["TEXT"])
        label_text = f"{label}"
        self.display.text(label_text, padding, y + 5, self.WIDTH, TEXT_SCALES["label"])

        # Afficher la valeur
        if is_iaq:
            value_str = f"{int(value)}"
        else:
            value_str = f"{value:.1f}{unit}"

        text_width = self.display.measure_text(value_str, TEXT_SCALES["value"])
        self.display.text(value_str, self.WIDTH - text_width - padding, y + 5, self.WIDTH, TEXT_SCALES["value"])

        # Afficher les min/max en petit
        self.display.set_pen(COLORS["GRAY_LIGHT"])
        range_str = f"{min_val:.0f}-{max_val:.0f}"
        self.display.text(range_str, self.WIDTH - 60, y + 5, self.WIDTH, TEXT_SCALES["small"])

    def show_data(self, temp, hum, press, iaq, gas=None):
        """
        Affiche les données du capteur avec des barres de progression.
        """
        # Ne pas rafraîchir si les données n'ont pas changé
        current_data = (temp, hum, press, iaq)
        if current_data == self.last_displayed_data:
            return
        self.last_displayed_data = current_data

        # Mettre à jour les min/max historiques
        self.update_historical_values(temp, hum, press, iaq)

        # Effacer l'écran
        self.clear()

        # Dessiner la bordure
        self.draw_border()

        # Titre
        self.display.set_pen(COLORS["TITLE"])
        self.display.text("Station Météo", LAYOUT["margin_left"], 5, self.WIDTH, TEXT_SCALES["title"])

        # Afficher l'état du capteur
        self.display.set_pen(COLORS["SUCCESS"])
        self.display.text("\u2713 Capteur OK", self.WIDTH - 80, 5, self.WIDTH, TEXT_SCALES["small"])

        # Position Y pour les barres
        bar_y_positions = [30, 65, 100, 135 - LAYOUT["bar_height"] - 5]

        # Dessiner les barres
        self.draw_horizontal_bar(
            y=bar_y_positions[0],
            label="Température",
            value=temp,
            min_val=self.historical_min_max["temp"]["min"],
            max_val=self.historical_min_max["temp"]["max"],
            unit="\u2103"
        )

        self.draw_horizontal_bar(
            y=bar_y_positions[1],
            label="Humidité",
            value=hum,
            min_val=self.historical_min_max["hum"]["min"],
            max_val=self.historical_min_max["hum"]["max"],
            unit="%"
        )

        self.draw_horizontal_bar(
            y=bar_y_positions[2],
            label="Pression",
            value=press,
            min_val=self.historical_min_max["press"]["min"],
            max_val=self.historical_min_max["press"]["max"],
            unit="hPa"
        )

        self.draw_horizontal_bar(
            y=bar_y_positions[3],
            label="IAQ",
            value=iaq,
            min_val=self.historical_min_max["iaq"]["min"],
            max_val=self.historical_min_max["iaq"]["max"],
            is_iaq=True
        )

        # Légende des boutons
        self.show_legend()

        # Mettre à jour l'affichage
        self.update()

    def update_historical_values(self, temp, hum, press, iaq):
        """Met à jour les valeurs min/max historiques."""
        self.historical_min_max["temp"]["min"] = min(self.historical_min_max["temp"]["min"], temp)
        self.historical_min_max["temp"]["max"] = max(self.historical_min_max["temp"]["max"], temp)

        self.historical_min_max["hum"]["min"] = min(self.historical_min_max["hum"]["min"], hum)
        self.historical_min_max["hum"]["max"] = max(self.historical_min_max["hum"]["max"], hum)

        self.historical_min_max["press"]["min"] = min(self.historical_min_max["press"]["min"], press)
        self.historical_min_max["press"]["max"] = max(self.historical_min_max["press"]["max"], press)

        self.historical_min_max["iaq"]["min"] = min(self.historical_min_max["iaq"]["min"], iaq)
        self.historical_min_max["iaq"]["max"] = max(self.historical_min_max["iaq"]["max"], iaq)

    def show_legend(self):
        """Affiche la légende des boutons en bas de l'écran."""
        self.display.set_pen(COLORS["GRAY_LIGHT"])
        legend = "Y:Menu  X:Rafraîchir"
        self.display.text(legend, LAYOUT["margin_left"], self.HEIGHT - 15, self.WIDTH, TEXT_SCALES["small"])

    def show_message(self, message, color=None, duration=2.0):
        """
        Affiche un message temporaire à l'écran.
        """
        if color is None:
            color = COLORS["TEXT"]

        self.clear()

        # Titre
        self.display.set_pen(COLORS["TITLE"])
        self.display.text("Message", LAYOUT["margin_left"], 5, self.WIDTH, TEXT_SCALES["title"])

        # Message
        self.display.set_pen(color)
        lines = message.split('\n')
        y_pos = 30
        for line in lines:
            self.display.text(line, LAYOUT["margin_left"], y_pos, self.WIDTH, TEXT_SCALES["value"])
            y_pos += 20

        # Instruction pour revenir
        self.display.set_pen(COLORS["GRAY_LIGHT"])
        self.display.text("Appuyez sur Y", self.WIDTH // 2 - 40, self.HEIGHT - 15, self.WIDTH, TEXT_SCALES["small"])

        self.update()

        if duration > 0:
            import time
            time.sleep(duration)

    def show_confirmation(self, message, confirm_text="Oui", cancel_text="Non"):
        """Affiche un écran de confirmation."""
        self.clear()

        # Titre
        self.display.set_pen(COLORS["WARNING"])
        self.display.text("\u26A0 Confirmation", LAYOUT["margin_left"], 5, self.WIDTH, TEXT_SCALES["title"])

        # Message
        self.display.set_pen(COLORS["TEXT"])
        self.display.text(message, LAYOUT["margin_left"], 30, self.WIDTH, TEXT_SCALES["value"])

        # Boutons Oui/Non
        self.display.set_pen(COLORS["BUTTON_A"])
        self.display.text(f"A: {confirm_text}", 50, 70, self.WIDTH, TEXT_SCALES["value"])

        self.display.set_pen(COLORS["BUTTON_B"])
        self.display.text(f"B: {cancel_text}", 150, 70, self.WIDTH, TEXT_SCALES["value"])

        self.update()

    def show_stats(self, stats, n_days):
        """Affiche les statistiques pour les derniers n_days."""
        self.clear()

        # Titre
        self.display.set_pen(COLORS["TITLE"])
        self.display.text(f"Stats ({n_days} jours)", LAYOUT["margin_left"], 5, self.WIDTH, TEXT_SCALES["title"])

        # Afficher les stats
        y_pos = 25
        for key, values in stats.items():
            if values['min'] is not None:
                # Nom de la métrique
                self.display.set_pen(COLORS["SUBTITLE"])
                display_key = key.capitalize()
                if key == "temperature":
                    display_key = "Température"
                elif key == "humidity":
                    display_key = "Humidité"
                elif key == "pressure":
                    display_key = "Pression"
                elif key == "iaq":
                    display_key = "IAQ"
                self.display.text(f"{display_key}:", LAYOUT["margin_left"], y_pos, self.WIDTH, TEXT_SCALES["label"])

                # Valeurs
                self.display.set_pen(COLORS["TEXT"])
                unit = "\u2103" if key == "temperature" else "%" if key == "humidity" else "hPa" if key == "pressure" else ""
                stats_text = f"Min:{values['min']:.1f}{unit} Max:{values['max']:.1f}{unit} Moy:{values['avg']:.1f}{unit}"
                self.display.text(stats_text, LAYOUT["margin_left"], y_pos + 15, self.WIDTH, TEXT_SCALES["small"])

                y_pos += 40

        # Instruction pour revenir
        self.display.set_pen(COLORS["GRAY_LIGHT"])
        self.display.text("Y pour revenir", self.WIDTH // 2 - 40, self.HEIGHT - 15, self.WIDTH, TEXT_SCALES["small"])

        self.update()

    def show_splash_screen(self):
        """Affiche l'écran de démarrage."""
        self.clear()

        # Logo / Titre
        self.display.set_pen(COLORS["TITLE"])
        self.display.text("Station Météo", 20, 40, self.WIDTH, TEXT_SCALES["title"])

        self.display.set_pen(COLORS["SUBTITLE"])
        self.display.text("BME680 + Pico", 40, 80, self.WIDTH, TEXT_SCALES["subtitle"])

        self.display.set_pen(COLORS["GRAY_LIGHT"])
        self.display.text("Initialisation...", 60, 110, self.WIDTH, TEXT_SCALES["small"])

        self.update()

    def show_sleep_screen(self):
        """Affiche l'écran de veille."""
        self.clear()

        self.display.set_pen(COLORS["GRAY_LIGHT"])
        self.display.text("Mode veille...", 50, self.HEIGHT // 2 - 10, self.WIDTH, TEXT_SCALES["title"])
        self.display.text("Bouton pour réveil", 30, self.HEIGHT // 2 + 20, self.WIDTH, TEXT_SCALES["small"])

        self.update()
        self.in_sleep_mode = True

    def wake_up(self):
        """Réveille l'écran du mode veille."""
        self.in_sleep_mode = False
        self.set_backlight(100)

    def show_time_input_screen(self, field_values, current_field_index, FIELDS):
        """Affiche l'écran de saisie de la date/heure."""
        self.clear()

        # Titre
        self.display.set_pen(COLORS["TITLE"])
        self.display.text("Configurer", LAYOUT["margin_left"], 5, self.WIDTH, TEXT_SCALES["title"])
        self.display.text("date/heure", LAYOUT["margin_left"], 20, self.WIDTH, TEXT_SCALES["subtitle"])

        # Champs
        y_pos = 45
        for i, field in enumerate(FIELDS):
            if field == "Confirmer":
                value = "OK"
            else:
                value = field_values[field]
                if field != "Année":
                    value = f"{value:02d}"

            # Couleur du champ (jaune si sélectionné)
            if i == current_field_index:
                color = COLORS["MENU_SELECTED"]
            else:
                color = COLORS["TEXT"]

            self.display.set_pen(color)
            if field == "Confirmer":
                self.display.text(f"{field}: {value}", LAYOUT["margin_left"], y_pos, self.WIDTH, TEXT_SCALES["value"])
            else:
                self.display.text(f"{field}: {value}", LAYOUT["margin_left"], y_pos, self.WIDTH, TEXT_SCALES["value"])

            y_pos += 25

        # Légende
        self.display.set_pen(COLORS["GRAY_LIGHT"])
        self.display.text("A:+ B:- X:OK Y:Annul", LAYOUT["margin_left"], self.HEIGHT - 15, self.WIDTH, TEXT_SCALES["small"])

        self.update()

    def show_menu(self, menu_items, current_index, title="Menu", space_used=0.0, line_count=0):
        """Affiche le menu système."""
        self.clear()

        # Titre
        self.display.set_pen(COLORS["TITLE"])
        self.display.text(title, LAYOUT["margin_left"], 5, self.WIDTH, TEXT_SCALES["title"])

        # Infos système
        self.display.set_pen(COLORS["GRAY_LIGHT"])
        self.display.text(f"Espace: {space_used:.1f}%", LAYOUT["margin_left"], 25, self.WIDTH, TEXT_SCALES["small"])
        self.display.text(f"Mesures: {line_count}", LAYOUT["margin_left"], 35, self.WIDTH, TEXT_SCALES["small"])

        # Éléments du menu
        y_pos = 55
        for i, item in enumerate(menu_items):
            if i >= current_index - 2 and i <= current_index + 2:
                # Couleur de l'élément (jaune si sélectionné)
                if i == current_index:
                    color = COLORS["MENU_SELECTED"]
                else:
                    color = COLORS["MENU_UNSELECTED"]

                self.display.set_pen(color)
                self.display.text(f"> {item}", LAYOUT["margin_left"], y_pos, self.WIDTH, TEXT_SCALES["value"])
                y_pos += 25

        # Légende
        self.display.set_pen(COLORS["GRAY_LIGHT"])
        self.display.text("X:Sel  Y:Retour", LAYOUT["margin_left"], self.HEIGHT - 15, self.WIDTH, TEXT_SCALES["small"])

        self.update()