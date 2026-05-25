# =============================================
# histogram.py - Gestion des histogrammes pour l'affichage des données
# =============================================

from config import (
    WIDTH, HEIGHT, HISTOGRAM_HEIGHT, VALUE_DISPLAY_HEIGHT,
    HISTOGRAM_BAR_WIDTH, HISTOGRAM_BAR_SPACING, HISTOGRAM_MAX_BARS
)
from utils import COLORS, get_iaq_color, get_metric_color, get_metric_unit, get_metric_display_name

class HistogramManager:
    """Gère l'affichage des histogrammes pour les données des capteurs."""

    def __init__(self, display):
        self.display = display
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT

    def draw_histogram(self, data_values, metric_name, current_value=None):
        """
        Dessine un histogramme pour une métrique donnée.

        Args:
            data_values: Liste des valeurs historiques (ex: [20.5, 21.0, 19.5, ...])
            metric_name: Nom de la métrique (ex: "temperature", "humidity", "pressure", "iaq")
            current_value: Valeur actuelle à afficher en bas (optionnel)
        """
        if not data_values:
            self._draw_empty_histogram(metric_name, current_value)
            return

        # Limiter le nombre de barres
        data_values = data_values[-HISTOGRAM_MAX_BARS:]

        # Calculer les dimensions
        bar_count = len(data_values)
        total_bar_width = bar_count * HISTOGRAM_BAR_WIDTH
        total_spacing = (bar_count - 1) * HISTOGRAM_BAR_SPACING
        total_width = total_bar_width + total_spacing

        # Centrer l'histogramme
        start_x = (self.WIDTH - total_width) // 2

        # Trouver les valeurs min/max pour l'échelle
        min_val = min(data_values)
        max_val = max(data_values)

        # Ajouter une marge pour éviter que les barres touchent le haut
        value_range = max_val - min_val
        if value_range == 0:
            value_range = 1  # Éviter la division par zéro

        # Dessiner le fond de l'histogramme
        self._draw_histogram_background(metric_name)

        # Dessiner les barres
        for i, value in enumerate(data_values):
            # Calculer la hauteur de la barre (en pixels)
            bar_height = int(((value - min_val) / value_range) * HISTOGRAM_HEIGHT)

            # Position de la barre
            x = start_x + i * (HISTOGRAM_BAR_WIDTH + HISTOGRAM_BAR_SPACING)
            y = HEIGHT - VALUE_DISPLAY_HEIGHT - HISTOGRAM_HEIGHT + (HISTOGRAM_HEIGHT - bar_height)

            # Couleur de la barre
            if metric_name == "iaq":
                color = get_iaq_color(value)
            else:
                color = get_metric_color(metric_name)

            # Dessiner la barre
            self.display.display.set_pen(color)
            self.display.display.rectangle(x, y, HISTOGRAM_BAR_WIDTH, bar_height)

        # Dessiner la valeur actuelle en bas
        if current_value is not None:
            self._draw_current_value(metric_name, current_value)

        # Mettre à jour l'affichage
        self.display.update()

    def _draw_histogram_background(self, metric_name):
        """Dessine le fond de l'histogramme avec le titre."""
        # Effacer l'écran
        self.display.clear()

        # Dessiner une bordure
        self.display.draw_border()

        # Titre
        display_name = get_metric_display_name(metric_name)
        self.display.display.set_pen(COLORS["TITLE"])
        self.display.display.text(
            display_name,
            15, 5,
            self.WIDTH,
            2  # Taille du titre
        )

        # Zone de l'histogramme (fond)
        self.display.display.set_pen(COLORS["HISTOGRAM_BG"])
        self.display.display.rectangle(
            0,
            HEIGHT - VALUE_DISPLAY_HEIGHT - HISTOGRAM_HEIGHT,
            self.WIDTH,
            HISTOGRAM_HEIGHT
        )

        # Ligne de base (axe X)
        self.display.display.set_pen(COLORS["HISTOGRAM_GRID"])
        self.display.display.line(
            0,
            HEIGHT - VALUE_DISPLAY_HEIGHT - HISTOGRAM_HEIGHT + HISTOGRAM_HEIGHT,
            self.WIDTH,
            HEIGHT - VALUE_DISPLAY_HEIGHT - HISTOGRAM_HEIGHT + HISTOGRAM_HEIGHT
        )

    def _draw_current_value(self, metric_name, value):
        """Dessine la valeur actuelle et son unité en bas de l'écran."""
        # Zone réservée en bas
        y_pos = HEIGHT - VALUE_DISPLAY_HEIGHT + 5

        # Nom de la métrique
        display_name = get_metric_display_name(metric_name)
        unit = get_metric_unit(metric_name)

        # Valeur formatée
        if metric_name == "iaq":
            value_str = f"{int(value)}"
        else:
            value_str = f"{value:.1f}{unit}"

        # Afficher le nom de la métrique
        self.display.display.set_pen(COLORS["SUBTITLE"])
        self.display.display.text(
            display_name + ":",
            15, y_pos,
            self.WIDTH,
            1
        )

        # Afficher la valeur
        self.display.display.set_pen(COLORS["TEXT"])
        self.display.display.text(
            value_str,
            15, y_pos + 15,
            self.WIDTH,
            3  # Grande taille pour la valeur
        )

        # Afficher l'unité séparément si nécessaire
        if unit and metric_name != "iaq":
            unit_width = self.display.display.measure_text(unit, 2)
            value_width = self.display.display.measure_text(f"{value:.1f}", 3)
            self.display.display.set_pen(COLORS["GRAY_LIGHT"])
            self.display.display.text(
                unit,
                15 + value_width, y_pos + 15,
                self.WIDTH,
                2
            )

    def _draw_empty_histogram(self, metric_name, current_value):
        """Dessine un histogramme vide (pas de données)."""
        self._draw_histogram_background(metric_name)

        # Message "Pas de données"
        self.display.display.set_pen(COLORS["GRAY_LIGHT"])
        self.display.display.text(
            "Pas de données",
            WIDTH // 2 - 40,
            HEIGHT // 2 - 10,
            WIDTH,
            2
        )

        # Afficher la valeur actuelle si disponible
        if current_value is not None:
            self._draw_current_value(metric_name, current_value)

        self.display.update()

    def show_metric_screen(self, metric_name, data_values, current_value):
        """
        Affiche un écran complet pour une métrique avec son histogramme.

        Args:
            metric_name: Nom de la métrique (ex: "temperature")
            data_values: Liste des valeurs historiques
            current_value: Valeur actuelle
        """
        self.draw_histogram(data_values, metric_name, current_value)

        # Légende des boutons
        self.display.display.set_pen(COLORS["GRAY_LIGHT"])
        legend = "Y:Retour  X:Rafraîchir"
        self.display.display.text(
            legend,
            15,
            HEIGHT - 5,
            self.WIDTH,
            1
        )

        self.display.update()