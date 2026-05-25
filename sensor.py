# =============================================
# sensor.py - Gestion du capteur BME680
# Lecture et validation des données du capteur
# =============================================

from pimoroni_i2c import PimoroniI2C
from breakout_bme68x import BreakoutBME68X
from config import I2C_SDA_PIN, I2C_SCL_PIN, SENSOR_RANGES
from utils import handle_error, is_valid_sensor_value

class DummyBME68X:
    """Capteur factice pour les tests ou en cas d'erreur."""

    def read(self):
        """Retourne des données factices."""
        return {
            "temperature": 20.0,
            "humidity": 50.0,
            "pressure": 101325,  # en Pa
            "gas": 100000        # en Ω
        }

class SensorManager:
    """Gère la lecture et la validation des données du capteur BME680."""

    def __init__(self):
        self.bme = None
        self.last_reading = None
        self.init_sensor()

    def init_sensor(self):
        """Initialise le capteur BME680."""
        try:
            i2c = PimoroniI2C(sda=I2C_SDA_PIN, scl=I2C_SCL_PIN)
            self.bme = BreakoutBME68X(i2c)
            print("BME680 initialisé avec succès !")
            # Tester la lecture initiale
            test_data = self.read_raw_data()
            if test_data:
                print(f"Lecture test: Temp={test_data[0]:.1f}°C, Hum={test_data[1]:.1f}%, Press={test_data[2]/100:.1f}hPa")
        except Exception as e:
            print(f"Erreur initialisation BME680: {e}")
            self.bme = DummyBME68X()
            handle_error(e, "Init BME680")

    def read_raw_data(self):
        """Lit les données brutes du capteur."""
        if not self.bme:
            return None

        try:
            data = self.bme.read()
            if data:
                return (
                    data.get("temperature", 20.0),    # °C
                    data.get("humidity", 50.0),       # %
                    data.get("pressure", 101325),    # Pa
                    data.get("gas", 100000)          # Ω
                )
            return None
        except Exception as e:
            handle_error(e, "Lecture BME680")
            return None

    def read_data(self):
        """
        Lit et valide les données du capteur.
        Retourne (temp, hum, press, gas, iaq) ou None en cas d'erreur.
        """
        raw_data = self.read_raw_data()
        if not raw_data:
            return None

        temp, hum, press, gas = raw_data

        # Valider les données
        if not all([
            is_valid_sensor_value("temp", temp),
            is_valid_sensor_value("hum", hum),
            is_valid_sensor_value("press", press / 100),  # Convertir en hPa
            is_valid_sensor_value("gas", gas)
        ]):
            handle_error("Données capteur invalides", "Validation")
            return None

        # Calculer l'IAQ
        iaq = self.calculate_iaq(gas)

        # Convertir la pression en hPa
        press_hpa = press / 100

        # Stocker la dernière lecture valide
        self.last_reading = (temp, hum, press_hpa, gas, iaq)

        return temp, hum, press_hpa, gas, iaq

    def calculate_iaq(self, gas_resistance):
        """
        Calcule un IAQ (Indice de Qualité de l'Air) simplifié.
        Basé sur la résistance du gaz.
        """
        if gas_resistance < 50000:
            return 50
        elif gas_resistance < 100000:
            return 100
        elif gas_resistance < 200000:
            return 200
        elif gas_resistance < 300000:
            return 300
        else:
            return 400

    def get_last_reading(self):
        """Retourne la dernière lecture valide."""
        return self.last_reading

    def is_sensor_ready(self):
        """Vérifie si le capteur est prêt."""
        return self.bme is not None

    def get_sensor_status(self):
        """Retourne l'état du capteur."""
        if self.bme and not isinstance(self.bme, DummyBME68X):
            return "OK", "Capteur BME680 fonctionnel"
        else:
            return "ERREUR", "Capteur en mode factice"

    def get_all_metrics(self):
        """
        Retourne un dictionnaire avec toutes les métriques.
        Format: {"temperature": value, "humidity": value, "pressure": value, "iaq": value}
        """
        data = self.read_data()
        if data:
            temp, hum, press, gas, iaq = data
            return {
                "temperature": temp,
                "humidity": hum,
                "pressure": press,
                "iaq": iaq,
                "gas": gas
            }
        return None