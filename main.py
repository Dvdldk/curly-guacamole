# =============================================
# main.py - Station Météo BME680 + Pico Display
# Version optimisée avec interface améliorée
# =============================================

from machine import Pin, RTC
import time

# Importer les modules personnalisés
from display import DisplayManager
from sensor import SensorManager
from storage import StorageManager
from menu import MenuManager
from utils import (
    COLORS, handle_error, format_timestamp,
    BacklightManager, WIDTH, HEIGHT
)

class WeatherStation:
    """
    Station météo complète avec capteur BME680.
    Gère l'affichage, la lecture des capteurs, le stockage et l'interface utilisateur.
    """

    def __init__(self):
        print("Initialisation de la station météo...")

        # Initialisation des composants
        self.display = DisplayManager()
        self.sensor = SensorManager()
        self.storage = StorageManager()
        self.menu = MenuManager(self.display)

        # Lier le storage au menu pour les actions
        self.menu.storage = self.storage
        self.menu.station = self

        # Initialisation du RTC
        self.rtc = RTC()

        # État de l'application
        self.current_screen = "home"
        self.last_activity_time = time.ticks_ms()
        self.last_display_update = 0
        self.last_data_save = 0
        self.last_displayed_data = None

        # Intervalles
        self.DISPLAY_INTERVAL = 5 * 1000      # 5 secondes
        self.SAVE_INTERVAL = 300 * 1000        # 5 minutes
        self.SLEEP_TIMEOUT = 30 * 1000         # 30 secondes d'inactivité
        self.in_sleep_mode = False

        # État pour la saisie de l'heure
        self.in_time_input = False

    def get_timestamp(self):
        """Récupère le timestamp actuel."""
        try:
            year, month, day, _, hour, minute, _, _ = self.rtc.datetime()
            return format_timestamp(year, month, day, hour, minute)
        except:
            return "2026-01-01 00:00"

    def get_button_pressed(self):
        """Détecte quel bouton est pressé."""
        buttons = {
            Pin(12): "A",
            Pin(13): "B",
            Pin(14): "X",
            Pin(15): "Y"
        }
        for pin, button in buttons.items():
            pin.init(Pin.IN, Pin.PULL_UP)
            if pin.value() == 0:
                return button
        return None

    def reset_sleep_timer(self):
        """Réinitialise le timer de veille."""
        self.last_activity_time = time.ticks_ms()
        if self.in_sleep_mode:
            self.wake_up()

    def check_sleep_mode(self):
        """Vérifie si l'appareil doit passer en mode veille."""
        if time.ticks_diff(time.ticks_ms(), self.last_activity_time) > self.SLEEP_TIMEOUT:
            if not self.in_sleep_mode:
                self.enter_sleep_mode()

    def enter_sleep_mode(self):
        """Passe en mode veille."""
        self.in_sleep_mode = True
        self.display.set_backlight(15)  # 15% de luminosité
        self.display.show_sleep_screen()
        print("Mode veille activé.")

    def wake_up(self):
        """Réveille l'appareil du mode veille."""
        self.in_sleep_mode = False
        self.display.set_backlight(100)  # 100% de luminosité
        self.display.wake_up()
        # Rafraîchir l'affichage
        self.force_data_refresh()
        print("Réveil du mode veille.")

    def force_data_refresh(self):
        """Force le rafraîchissement des données du capteur."""
        data = self.sensor.read_data()
        if data:
            temp, hum, press, gas, iaq = data
            self.display.show_data(temp, hum, press, iaq)
            self.last_displayed_data = (temp, hum, press, iaq)

    def wait_for_time_input(self):
        """Attend que l'utilisateur configure la date/heure."""
        self.in_time_input = True
        time_input_state = self.menu.get_time_input_state()

        # Afficher l'écran de saisie
        self.display.show_time_input_screen(
            field_values=time_input_state["FIELD_VALUES"],
            current_field_index=time_input_state["current_field_index"],
            FIELDS=time_input_state["FIELDS"]
        )

        while self.in_time_input:
            button = self.get_button_pressed()
            if button:
                self.reset_sleep_timer()
                if self.handle_time_button(button):
                    return
            time.sleep(0.1)

    def handle_time_button(self, button):
        """Gère les appuis sur les boutons dans l'écran de saisie du temps."""
        time_input_state = self.menu.get_time_input_state()
        current_field_index = time_input_state["current_field_index"]
        FIELDS = time_input_state["FIELDS"]

        if current_field_index >= len(FIELDS):
            return False

        field = FIELDS[current_field_index]

        if button == "A" and field != "Confirmer":
            # Incrémenter
            self.menu.increment_time_field(field)
            self.display.show_time_input_screen(
                field_values=time_input_state["FIELD_VALUES"],
                current_field_index=current_field_index,
                FIELDS=FIELDS
            )
        elif button == "B" and field != "Confirmer":
            # Décrémenter
            self.menu.decrement_time_field(field)
            self.display.show_time_input_screen(
                field_values=time_input_state["FIELD_VALUES"],
                current_field_index=current_field_index,
                FIELDS=FIELDS
            )
        elif button == "X":
            if field == "Confirmer":
                # Valider et régler l'heure
                self.set_rtc_from_input()
                self.in_time_input = False
                self.display.show_message("Heure réglée!", COLORS["SUCCESS"])
                return True
            else:
                # Champ suivant
                self.menu.next_time_field()
                time_input_state = self.menu.get_time_input_state()
                self.display.show_time_input_screen(
                    field_values=time_input_state["FIELD_VALUES"],
                    current_field_index=time_input_state["current_field_index"],
                    FIELDS=FIELDS
                )
        elif button == "Y":
            # Annuler
            self.in_time_input = False
            self.menu.reset_time_input()
            return True

        return False

    def set_rtc_from_input(self):
        """Règle le RTC avec les valeurs saisies."""
        field_values = self.menu.get_time_input_values()
        year = field_values["Année"]
        month = field_values["Mois"]
        day = field_values["Jour"]
        hour = field_values["Heure"]
        minute = field_values["Minute"]

        try:
            self.rtc.datetime((year, month, day, 0, hour, minute, 0, None))
            print(f"RTC réglé: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")
        except Exception as e:
            handle_error(e, "Configuration RTC", self.display)

    def handle_button(self, button):
        """Gère les appuis sur les boutons dans l'écran principal."""
        self.reset_sleep_timer()

        if self.menu.in_menu:
            # Gérer les boutons dans le menu
            should_close = self.menu.handle_button(button)
            if should_close:
                self.menu.in_menu = False
                self.force_data_refresh()
        elif self.menu.in_confirmation:
            # Gérer les boutons dans la confirmation
            self.menu.handle_confirmation_button(button)
        elif self.in_time_input:
            # Géré dans wait_for_time_input
            pass
        else:
            # Écran principal
            if button == "Y":
                self.menu.in_menu = True
                self.menu.current_menu = "main"
                self.menu.current_index = 0
                self.menu.show()
            elif button == "X":
                self.force_data_refresh()
            elif button == "A":
                # Stats 24h
                stats = self.storage.get_stats(1)
                self.display.show_stats(stats, 1)
            elif button == "B":
                # Stats 7j
                stats = self.storage.get_stats(7)
                self.display.show_stats(stats, 7)

    def run(self):
        """Boucle principale de l'application."""
        # Afficher l'écran de démarrage
        self.display.show_splash_screen()
        time.sleep(2)

        # Affichage initial
        self.force_data_refresh()

        # Boucle principale
        while True:
            current_time = time.ticks_ms()

            # Gérer les boutons
            button = self.get_button_pressed()
            if button:
                self.handle_button(button)

            # Rafraîchir l'affichage toutes les 5 secondes
            if time.ticks_diff(current_time, self.last_display_update) >= self.DISPLAY_INTERVAL:
                data = self.sensor.read_data()
                if data:
                    temp, hum, press, gas, iaq = data
                    self.display.show_data(temp, hum, press, iaq)
                    self.last_display_update = current_time
                    self.last_displayed_data = (temp, hum, press, iaq)

            # Sauvegarder les données toutes les 5 minutes
            if time.ticks_diff(current_time, self.last_data_save) >= self.SAVE_INTERVAL:
                data = self.sensor.read_data()
                if data:
                    temp, hum, press, gas, iaq = data
                    timestamp = self.get_timestamp()
                    self.storage.write_data(timestamp, temp, hum, press, gas, iaq)
                    self.last_data_save = current_time
                    print(f"Données sauvegardées: {timestamp}")

            # Vérifier le mode veille
            if not self.menu.in_menu and not self.menu.in_confirmation and not self.in_time_input:
                self.check_sleep_mode()

            time.sleep(0.1)

# =============================================
# Point d'entrée principal
# =============================================
if __name__ == "__main__":
    try:
        station = WeatherStation()
        station.run()
    except Exception as e:
        print(f"Erreur fatale: {e}")
        # Essayer d'afficher l'erreur
        try:
            from display import DisplayManager
            display = DisplayManager()
            display.show_message(f"Erreur fatale:\n{e}", COLORS["ERROR"])
        except:
            pass