# =============================================
# menu.py - Gestion des menus et de la navigation
# Menu hiérarchique et gestion des actions
# =============================================

from config import METRIC_NAMES
from utils import handle_error, COLORS

class MenuManager:
    """Gère les menus et la navigation dans l'interface."""

    def __init__(self, display):
        self.display = display
        self.current_menu = "main"
        self.current_index = 0
        self.in_menu = False
        self.in_confirmation = False
        self.confirmation_option = None
        self.confirmation_action = None

        # Structure du menu hiérarchique
        self.menu_structure = {
            "main": {
                "title": "Menu Principal",
                "items": [
                    {"label": "Exporter CSV", "action": "export_csv"},
                    {"label": "Effacer données", "action": "confirm_clear_data"},
                    {"label": "Régler heure", "action": "confirm_set_time"},
                    {"label": "Statistiques", "submenu": "stats"},
                    {"label": "Visualiser", "submenu": "visualize"},
                    {"label": "À propos", "action": "show_about"},
                ]
            },
            "stats": {
                "title": "Statistiques",
                "items": [
                    {"label": "24 heures", "action": "show_stats_24h"},
                    {"label": "7 jours", "action": "show_stats_7d"},
                    {"label": "30 jours", "action": "show_stats_30d"},
                ]
            },
            "visualize": {
                "title": "Visualiser",
                "items": [
                    {"label": "Température", "action": "show_histogram_temp"},
                    {"label": "Humidité", "action": "show_histogram_hum"},
                    {"label": "Pression", "action": "show_histogram_press"},
                    {"label": "IAQ", "action": "show_histogram_iaq"},
                ]
            }
        }

        # Actions associées
        self.actions = {
            "export_csv": self.action_export_csv,
            "confirm_clear_data": self.action_confirm_clear_data,
            "clear_data": self.action_clear_data,
            "confirm_set_time": self.action_confirm_set_time,
            "set_time": self.action_set_time,
            "show_stats_24h": lambda: self.action_show_stats(1),
            "show_stats_7d": lambda: self.action_show_stats(7),
            "show_stats_30d": lambda: self.action_show_stats(30),
            "show_about": self.action_show_about,
            "show_histogram_temp": lambda: self.action_show_histogram("temperature"),
            "show_histogram_hum": lambda: self.action_show_histogram("humidity"),
            "show_histogram_press": lambda: self.action_show_histogram("pressure"),
            "show_histogram_iaq": lambda: self.action_show_histogram("iaq"),
        }

        # État pour la saisie de l'heure
        self.time_input_state = {
            "FIELDS": ["Jour", "Mois", "Année", "Heure", "Minute", "Confirmer"],
            "FIELD_VALUES": {
                "Jour": 1,
                "Mois": 1,
                "Année": 2026,
                "Heure": 12,
                "Minute": 0
            },
            "FIELD_RANGES": {
                "Jour": (1, 31),
                "Mois": (1, 12),
                "Année": (2020, 2030),
                "Heure": (0, 23),
                "Minute": (0, 59)
            },
            "current_field_index": 0
        }

    def show(self):
        """Affiche le menu actuel."""
        self.in_menu = True
        menu = self.menu_structure.get(self.current_menu, {"title": "Menu", "items": []})

        # Obtenir les infos système
        space_used = 0.0
        line_count = 0
        if hasattr(self, 'storage'):
            space_used = self.storage.get_space_used_percent()
            line_count = self.storage.get_line_count()

        # Afficher le menu
        items = [item["label"] for item in menu.get("items", [])]
        self.display.show_menu(
            menu_items=items,
            current_index=self.current_index,
            title=menu.get("title", "Menu"),
            space_used=space_used,
            line_count=line_count
        )

    def hide(self):
        """Cache le menu."""
        self.in_menu = False

    def handle_button(self, button):
        """
        Gère les appuis sur les boutons dans le menu.
        Retourne True si le menu doit être fermé.
        """
        if not self.in_menu and not self.in_confirmation:
            return False

        if self.in_confirmation:
            return self.handle_confirmation_button(button)

        menu = self.menu_structure.get(self.current_menu, {"title": "Menu", "items": []})
        items = menu.get("items", [])

        if button == "X":  # Sélectionner
            if self.current_index < len(items):
                item = items[self.current_index]
                if "action" in item:
                    action = item["action"]
                    if action in self.actions:
                        self.actions[action]()
                    return False
                elif "submenu" in item:
                    self.current_menu = item["submenu"]
                    self.current_index = 0
                    self.show()
                    return False
            return False

        elif button == "Y":  # Retour
            if self.current_menu != "main":
                self.current_menu = "main"
                self.current_index = 0
                self.show()
            else:
                self.in_menu = False
                return True

        elif button == "A":  # Haut
            self.current_index = (self.current_index - 1) % len(items)
            self.show()

        elif button == "B":  # Bas
            self.current_index = (self.current_index + 1) % len(items)
            self.show()

        return False

    def handle_confirmation_button(self, button):
        """Gère les boutons dans l'écran de confirmation."""
        if button == "A":  # Oui
            if self.confirmation_action:
                self.confirmation_action()
            self.in_confirmation = False
            self.in_menu = False
            return True
        elif button == "B":  # Non
            self.in_confirmation = False
            self.show()
        return False

    def show_confirmation(self, message, confirm_action):
        """Affiche un écran de confirmation."""
        self.in_confirmation = True
        self.confirmation_action = confirm_action
        self.display.show_confirmation(message)

    # --- Actions du menu ---

    def action_export_csv(self):
        """Action: Exporter le CSV."""
        if hasattr(self, 'storage'):
            data_file = self.storage.export_data()
            self.display.show_message(
                f"Fichier prêt!\nConnecter Thonny\nChemin: /{data_file}",
                COLORS["INFO"]
            )

    def action_confirm_clear_data(self):
        """Action: Demander confirmation pour effacer les données."""
        self.show_confirmation("Effacer toutes les données?", self.action_clear_data)

    def action_clear_data(self):
        """Action: Effacer les données."""
        if hasattr(self, 'storage'):
            if self.storage.erase_data():
                self.display.show_message("Données effacées!", COLORS["SUCCESS"])
            else:
                self.display.show_message("Erreur effacement", COLORS["ERROR"])

    def action_confirm_set_time(self):
        """Action: Demander confirmation pour régler l'heure."""
        self.show_confirmation("Régler l'heure maintenant?", self.action_set_time)

    def action_set_time(self):
        """Action: Régler l'heure (ouvre l'écran de saisie)."""
        self.in_menu = False
        self.in_confirmation = False
        if hasattr(self, 'station'):
            self.station.wait_for_time_input()

    def action_show_stats(self, n_days):
        """Action: Afficher les statistiques."""
        if hasattr(self, 'storage'):
            stats = self.storage.get_stats(n_days)
            self.display.show_stats(stats, n_days)
            self.in_menu = False

    def action_show_about(self):
        """Action: Afficher la page 'À propos'."""
        about_text = "Station Météo\nBME680 + Pico\nv1.0\n\nCapteurs:\n- Température\n- Humidité\n- Pression\n- IAQ"
        self.display.show_message(about_text, COLORS["INFO"])

    def action_show_histogram(self, metric_name):
        """Action: Afficher l'histogramme pour une métrique."""
        if hasattr(self, 'storage') and hasattr(self, 'station'):
            # Récupérer les données récentes
            recent_data = self.storage.get_recent_data(50)

            # Extraire les valeurs pour la métrique demandée
            metric_values = []
            current_value = None

            # Mapper le nom de la métrique au champ CSV
            metric_to_field = {
                "temperature": 1,
                "humidity": 2,
                "pressure": 3,
                "iaq": 5
            }

            if metric_name in metric_to_field:
                field_index = metric_to_field[metric_name]
                for entry in recent_data:
                    if len(entry) > field_index:
                        metric_values.append(entry[field_index])

                # Obtenir la valeur actuelle
                if hasattr(self.station, 'sensor'):
                    current_metrics = self.station.sensor.get_all_metrics()
                    if current_metrics and metric_name in current_metrics:
                        current_value = current_metrics[metric_name]

            # Afficher l'histogramme
            if hasattr(self.station, 'histogram_manager'):
                self.station.histogram_manager.show_metric_screen(
                    metric_name, metric_values, current_value
                )

            self.in_menu = False

    # --- Gestion de la saisie de l'heure ---

    def get_time_input_state(self):
        """Retourne l'état actuel de la saisie de l'heure."""
        return self.time_input_state

    def set_time_input_value(self, field, value):
        """Définit la valeur d'un champ de saisie."""
        if field in self.time_input_state["FIELD_VALUES"]:
            self.time_input_state["FIELD_VALUES"][field] = value

    def increment_time_field(self, field):
        """Incrémente la valeur d'un champ."""
        if field in self.time_input_state["FIELD_RANGES"]:
            min_val, max_val = self.time_input_state["FIELD_RANGES"][field]
            current = self.time_input_state["FIELD_VALUES"][field]
            new_value = min(current + 1, max_val)

            # Vérification spéciale pour le jour
            if field == "Jour":
                month = self.time_input_state["FIELD_VALUES"]["Mois"]
                year = self.time_input_state["FIELD_VALUES"]["Année"]
                max_day = self.get_max_day(month, year)
                new_value = min(new_value, max_day)

            self.time_input_state["FIELD_VALUES"][field] = new_value

    def decrement_time_field(self, field):
        """Décrémente la valeur d'un champ."""
        if field in self.time_input_state["FIELD_RANGES"]:
            min_val, max_val = self.time_input_state["FIELD_RANGES"][field]
            current = self.time_input_state["FIELD_VALUES"][field]
            new_value = max(current - 1, min_val)
            self.time_input_state["FIELD_VALUES"][field] = new_value

    def next_time_field(self):
        """Passe au champ suivant."""
        self.time_input_state["current_field_index"] = (
            self.time_input_state["current_field_index"] + 1
        ) % len(self.time_input_state["FIELDS"])

    def get_max_day(self, month, year):
        """Retourne le nombre de jours dans un mois."""
        if month in [4, 6, 9, 11]:
            return 30
        elif month == 2:
            return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
        else:
            return 31

    def get_time_input_values(self):
        """Retourne les valeurs actuelles de la saisie."""
        return self.time_input_state["FIELD_VALUES"]

    def reset_time_input(self):
        """Réinitialise la saisie de l'heure."""
        self.time_input_state["current_field_index"] = 0
        self.time_input_state["FIELD_VALUES"] = {
            "Jour": 1,
            "Mois": 1,
            "Année": 2026,
            "Heure": 12,
            "Minute": 0
        }