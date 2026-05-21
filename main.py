# =============================================
# Projet BME680 + PicoGraphics + BreakoutBME68X
# Rafraîchissement affichage : 5 secondes
# Acquisition CSV : 5 minutes
# Sans BSEC (utilisation de calculate_iaq simplifié)
# =============================================

from machine import Pin, PWM, RTC
import time
import uos
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_RGB565
from pimoroni_i2c import PimoroniI2C
from breakout_bme68x import BreakoutBME68X

# --- Initialisation de l'écran et du rétroéclairage ---
WIDTH = 240
HEIGHT = 135
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_RGB565)
bl = PWM(Pin(20))
bl.freq(1000)
bl.duty_u16(65535)  # Rétroéclairage à 100%

# --- Fonction de conversion RGB565 ---
def rgb565(r, g, b):
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3

# --- Couleurs ---
BG_COLOR = rgb565(0, 0, 0)
TEXT_COLOR = rgb565(255, 255, 255)
BAR_COLORS = {
    "temp": rgb565(0, 150, 255),
    "hum": rgb565(0, 255, 255),
    "press": rgb565(255, 100, 0),
}
IAQ_COLORS = {
    (0, 50): rgb565(0, 255, 0),
    (51, 100): rgb565(100, 255, 100),
    (101, 150): rgb565(255, 255, 0),
    (151, 200): rgb565(255, 165, 0),
    (201, 250): rgb565(255, 100, 0),
    (251, 350): rgb565(255, 0, 0),
    (351, 500): rgb565(150, 0, 0),
}

# --- Données historiques pour les min/max ---
historical_min_max = {
    "temp": {"min": 0, "max": 40},
    "hum": {"min": 0, "max": 100},
    "press": {"min": 900, "max": 1100},
    "iaq": {"min": 0, "max": 500}
}

# --- Initialisation du BME680 ---
try:
    i2c = PimoroniI2C(sda=4, scl=5)
    bme = BreakoutBME68X(i2c)
    print("BME680 initialisé avec succès !")
except Exception as e:
    print(f"Erreur initialisation BME680: {e}")
    # Objet factice pour éviter les erreurs
    class DummyBME68X:
        def read_temperature(self):
            return 20.0
        def read_humidity(self):
            return 50.0
        def read_pressure(self):
            return 101325  # en Pa
        def read_gas_resistance(self):
            return 100000
    bme = DummyBME68X()

# --- Fonction calculate_iaq simplifiée ---
def calculate_iaq(gas_resistance):
    """Calcule un IAQ simplifié à partir de la résistance du gaz."""
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

# --- Gestion du stockage ---
MAX_FLASH_USAGE = 0.7
FLASH_SIZE = 2 * 1024 * 1024
MAX_FILE_SIZE = int(MAX_FLASH_USAGE * FLASH_SIZE)
DATA_FILE = "data.csv"
BACKUP_FILE = "data_backup.csv"
CSV_HEADER = "timestamp,temperature,humidity,pressure,gas,iaq\n"
LINE_FORMAT = "{},{:.2f},{:.2f},{:.2f},{},{}\n"

def init_storage():
    try:
        uos.stat(DATA_FILE)
    except OSError:
        try:
            with open(DATA_FILE, "w") as f:
                f.write(CSV_HEADER)
        except Exception as e:
            print(f"Erreur création fichier CSV: {e}")

def write_data(timestamp, temp, humidity, pressure, gas, iaq):
    try:
        current_size = get_file_size(DATA_FILE)
        if (current_size + 100) >= MAX_FILE_SIZE:
            cleanup_old_entries()
        with open(DATA_FILE, "a") as f:
            line = LINE_FORMAT.format(timestamp, temp, humidity, pressure, gas, iaq)
            f.write(line)
    except Exception as e:
        print(f"Erreur écriture CSV: {e}")

def get_file_size(filename):
    try:
        return uos.stat(filename)[6]
    except OSError:
        return 0

def cleanup_old_entries():
    current_size = get_file_size(DATA_FILE)
    if current_size >= MAX_FILE_SIZE:
        try:
            with open(DATA_FILE, "r") as f:
                lines = f.readlines()[1:]
            avg_line_size = current_size / len(lines) if lines else 100
            max_lines = int((MAX_FILE_SIZE * 0.9) / avg_line_size)
            if max_lines < len(lines):
                lines_to_keep = lines[-max_lines:]
                with open(BACKUP_FILE, "w") as f_backup:
                    f_backup.write(CSV_HEADER)
                    f_backup.writelines(lines_to_keep)
                uos.remove(DATA_FILE)
                uos.rename(BACKUP_FILE, DATA_FILE)
        except OSError as e:
            print(f"Erreur nettoyage fichier: {e}")

def get_stats(n_days):
    try:
        current_time = time.mktime(rtc.datetime()[:3] + (0, 0, 0, 0, 0))
        cutoff_time = current_time - (n_days * 86400)
    except:
        return {k: {'min': None, 'max': None, 'avg': None} for k in ['temperature', 'humidity', 'pressure', 'iaq']}

    stats = {
        'temperature': {'min': float('inf'), 'max': float('-inf'), 'sum': 0, 'count': 0},
        'humidity': {'min': float('inf'), 'max': float('-inf'), 'sum': 0, 'count': 0},
        'pressure': {'min': float('inf'), 'max': float('-inf'), 'sum': 0, 'count': 0},
        'iaq': {'min': float('inf'), 'max': float('-inf'), 'sum': 0, 'count': 0}
    }
    try:
        with open(DATA_FILE, "r") as f:
            lines = f.readlines()[1:]
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) != 6:
                    continue
                timestamp_str, temp, humidity, pressure, gas, iaq = parts
                try:
                    year, month, day = map(int, timestamp_str.split()[0].split('-'))
                    hour, minute, second = map(int, timestamp_str.split()[1].split(':'))
                    line_time = time.mktime((year, month, day, hour, minute, second, 0, 0, 0))
                except:
                    continue
                if line_time < cutoff_time:
                    continue
                temp_val = float(temp)
                stats['temperature']['min'] = min(stats['temperature']['min'], temp_val)
                stats['temperature']['max'] = max(stats['temperature']['max'], temp_val)
                stats['temperature']['sum'] += temp_val
                stats['temperature']['count'] += 1
                humidity_val = float(humidity)
                stats['humidity']['min'] = min(stats['humidity']['min'], humidity_val)
                stats['humidity']['max'] = max(stats['humidity']['max'], humidity_val)
                stats['humidity']['sum'] += humidity_val
                stats['humidity']['count'] += 1
                pressure_val = float(pressure)
                stats['pressure']['min'] = min(stats['pressure']['min'], pressure_val)
                stats['pressure']['max'] = max(stats['pressure']['max'], pressure_val)
                stats['pressure']['sum'] += pressure_val
                stats['pressure']['count'] += 1
                iaq_val = int(iaq)
                stats['iaq']['min'] = min(stats['iaq']['min'], iaq_val)
                stats['iaq']['max'] = max(stats['iaq']['max'], iaq_val)
                stats['iaq']['sum'] += iaq_val
                stats['iaq']['count'] += 1
    except OSError as e:
        print(f"Erreur lecture CSV: {e}")
    result = {}
    for key in stats:
        if stats[key]['count'] > 0:
            result[key] = {
                'min': stats[key]['min'],
                'max': stats[key]['max'],
                'avg': stats[key]['sum'] / stats[key]['count']
            }
        else:
            result[key] = {'min': None, 'max': None, 'avg': None}
    return result

def get_line_count():
    try:
        with open(DATA_FILE, "r") as f:
            return len(f.readlines()) - 1
    except OSError:
        return 0

def get_space_used_percent():
    try:
        file_size = get_file_size(DATA_FILE)
        total_space = get_free_space() + file_size
        return (file_size / total_space) * 100 if total_space > 0 else 0.0
    except:
        return 0.0

def get_free_space():
    try:
        stat = uos.statvfs('/')
        return stat[3] * stat[4]
    except:
        return 0

# --- Gestion du temps ---
rtc = RTC()
start_time = time.ticks_ms()

FIELDS = ["Jour", "Mois", "Année", "Heure", "Minute", "Confirmer"]
FIELD_VALUES = {
    "Jour": (1, 31),
    "Mois": (1, 12),
    "Année": (2020, 2030),
    "Heure": (0, 23),
    "Minute": (0, 59)
}
current_field_index = 0
field_values = {
    "Jour": 1,
    "Mois": 1,
    "Année": 2026,
    "Heure": 12,
    "Minute": 0
}

def init_time_manager():
    global start_time
    start_time = time.ticks_ms()

def get_timestamp():
    try:
        year, month, day, _, hour, minute, _, _ = rtc.datetime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(year, month, day, hour, minute)
    except:
        return "2026-01-01 00:00"

# --- Affichage ---
BAR_HEIGHT = 25
BAR_Y_POSITIONS = [20, 50, 80, 110]
TEXT_SCALE_1 = 1
TEXT_SCALE_2 = 2
PADDING = 5

def update_historical_values(temp, hum, press, iaq):
    historical_min_max["temp"]["min"] = min(historical_min_max["temp"]["min"], temp)
    historical_min_max["temp"]["max"] = max(historical_min_max["temp"]["max"], temp)
    historical_min_max["hum"]["min"] = min(historical_min_max["hum"]["min"], hum)
    historical_min_max["hum"]["max"] = max(historical_min_max["hum"]["max"], hum)
    historical_min_max["press"]["min"] = min(historical_min_max["press"]["min"], press)
    historical_min_max["press"]["max"] = max(historical_min_max["press"]["max"], press)
    historical_min_max["iaq"]["min"] = min(historical_min_max["iaq"]["min"], iaq)
    historical_min_max["iaq"]["max"] = max(historical_min_max["iaq"]["max"], iaq)

def draw_horizontal_bar(y, label, value, min_val, max_val, is_iaq=False):
    try:
        bar_width = max(0, int((value - min_val) / (max_val - min_val) * (WIDTH - 2 * PADDING)))
        if is_iaq:
            for (low, high), color in IAQ_COLORS.items():
                if low <= value <= high:
                    bar_color = color
                    break
            else:
                bar_color = IAQ_COLORS[(351, 500)]
        else:
            bar_color = BAR_COLORS.get(label.lower(), TEXT_COLOR)
        display.set_pen(bar_color)
        display.rectangle(PADDING, y, bar_width, BAR_HEIGHT)
        display.set_pen(TEXT_COLOR)
        display.text(label, PADDING, y + 5, WIDTH, TEXT_SCALE_1)
        value_str = f"{value:.1f}" if not is_iaq else f"{int(value)}"
        text_width = display.measure_text(value_str, TEXT_SCALE_2)
        display.text(value_str, WIDTH - text_width - PADDING, y + 5, WIDTH, TEXT_SCALE_2)
    except Exception as e:
        print(f"Erreur dessin barre: {e}")

def show_bme680_data(temp, hum, press, iaq):
    try:
        display.set_pen(BG_COLOR)
        display.clear()
        update_historical_values(temp, hum, press, iaq)
        display.set_pen(TEXT_COLOR)
        display.text("Station BME680", 10, 5, WIDTH, 2)
        draw_horizontal_bar(
            y=BAR_Y_POSITIONS[0],
            label="Température (°C)",
            value=temp,
            min_val=historical_min_max["temp"]["min"],
            max_val=historical_min_max["temp"]["max"]
        )
        draw_horizontal_bar(
            y=BAR_Y_POSITIONS[1],
            label="Humidité (%)",
            value=hum,
            min_val=historical_min_max["hum"]["min"],
            max_val=historical_min_max["hum"]["max"]
        )
        draw_horizontal_bar(
            y=BAR_Y_POSITIONS[2],
            label="Pression (hPa)",
            value=press,
            min_val=historical_min_max["press"]["min"],
            max_val=historical_min_max["press"]["max"]
        )
        draw_horizontal_bar(
            y=BAR_Y_POSITIONS[3],
            label="IAQ",
            value=iaq,
            min_val=historical_min_max["iaq"]["min"],
            max_val=historical_min_max["iaq"]["max"],
            is_iaq=True
        )
        display.update()
    except Exception as e:
        print(f"Erreur affichage données: {e}")

# --- Menu système ---
MENU_OPTIONS = ["Exporter CSV", "Effacer données", "Régler heure", "Stats 24h", "Stats 7j"]
current_menu_index = 0
in_menu = False
in_confirmation = False
confirmation_option = None

def show_menu():
    global in_menu
    in_menu = True
    try:
        display.set_pen(BG_COLOR)
        display.clear()
        display.set_pen(TEXT_COLOR)
        display.text("Menu Système", 10, 5, WIDTH, 2)
        display.text(f"Espace: {get_space_used_percent():.1f}%", 10, 25, WIDTH, 1)
        display.text(f"Mesures: {get_line_count()}", 10, 35, WIDTH, 1)
        y_pos = 55
        for i, option in enumerate(MENU_OPTIONS):
            color = rgb565(255, 255, 0) if i == current_menu_index else rgb565(100, 100, 255)
            display.set_pen(color)
            display.text(f"> {option}", 10, y_pos, WIDTH, 2)
            y_pos += 25
        display.update()
    except Exception as e:
        print(f"Erreur affichage menu: {e}")

def handle_menu_button(button):
    global current_menu_index, in_menu, in_confirmation, confirmation_option
    if not in_menu and not in_confirmation:
        return False
    if in_confirmation:
        if button == "A":
            if confirmation_option == "Effacer données":
                erase_data()
                show_message("Données effacées!", rgb565(0, 255, 0))
            elif confirmation_option == "Régler heure":
                wait_for_time_input()
                show_message("Heure réglée!", rgb565(0, 255, 0))
            in_confirmation = False
            in_menu = False
            return True
        elif button == "B":
            in_confirmation = False
            show_menu()
        return False
    if button == "A":
        selected_option = MENU_OPTIONS[current_menu_index]
        if selected_option == "Exporter CSV":
            show_message(f"Fichier prêt!\nConnecter Thonny\nChemin: /{DATA_FILE}", TEXT_COLOR)
        elif selected_option == "Effacer données":
            confirmation_option = selected_option
            show_confirmation("Effacer toutes les données?")
        elif selected_option == "Régler heure":
            confirmation_option = selected_option
            show_confirmation("Régler l'heure maintenant?")
        elif selected_option == "Stats 24h":
            show_stats(1)
            in_menu = False
        elif selected_option == "Stats 7j":
            show_stats(7)
            in_menu = False
        return False
    elif button == "B":
        current_menu_index = (current_menu_index - 1) % len(MENU_OPTIONS)
        show_menu()
    elif button == "X":
        current_menu_index = (current_menu_index + 1) % len(MENU_OPTIONS)
        show_menu()
    elif button == "Y":
        in_menu = False
        return True
    return False

def show_confirmation(message):
    global in_confirmation
    in_confirmation = True
    try:
        display.set_pen(BG_COLOR)
        display.clear()
        display.set_pen(rgb565(255, 165, 0))
        display.text("Confirmation", 10, 5, WIDTH, 2)
        display.set_pen(TEXT_COLOR)
        display.text(message, 10, 30, WIDTH, 2)
        display.set_pen(TEXT_COLOR)
        display.text("A: Oui", 50, 70, WIDTH, 2)
        display.text("B: Non", 150, 70, WIDTH, 2)
        display.update()
    except Exception as e:
        print(f"Erreur affichage confirmation: {e}")

def show_message(message, color=TEXT_COLOR):
    try:
        display.set_pen(BG_COLOR)
        display.clear()
        display.set_pen(color)
        lines = message.split('\n')
        for i, line in enumerate(lines):
            display.text(line, 10, 20 + i * 20, WIDTH, 2)
        display.set_pen(TEXT_COLOR)
        display.text("Appuyez sur Y pour revenir", 10, HEIGHT - 20, WIDTH, 1)
        display.update()
        time.sleep(2)
    except Exception as e:
        print(f"Erreur affichage message: {e}")

def erase_data():
    try:
        uos.remove(DATA_FILE)
    except OSError as e:
        print(f"Erreur effacement données: {e}")

def show_stats(n_days):
    try:
        stats = get_stats(n_days)
        display.set_pen(BG_COLOR)
        display.clear()
        display.set_pen(TEXT_COLOR)
        display.text(f"Stats ({n_days} jours)", 10, 5, WIDTH, 2)
        y_pos = 25
        for key, values in stats.items():
            if values['min'] is not None:
                display.text(f"{key.capitalize()}:", 10, y_pos, WIDTH, 1)
                display.text(f"Min: {values['min']:.1f}, Max: {values['max']:.1f}, Moy: {values['avg']:.1f}",
                             10, y_pos + 15, WIDTH, 1)
                y_pos += 40
        display.text("Appuyez sur Y pour revenir", 10, HEIGHT - 20, WIDTH, 1)
        display.update()
    except Exception as e:
        print(f"Erreur affichage stats: {e}")

# --- Gestion des boutons ---
def get_button_pressed():
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

def wait_for_time_input():
    """Attend que l'utilisateur configure la date/heure.
    Retourne au menu après validation."""
    global in_menu
    in_menu = False  # Désactiver le flag menu pendant la saisie
    show_time_input_screen()
    while True:
        button = get_button_pressed()
        if button and handle_time_button(button):
            return  # Retourne au menu (géré dans handle_time_button)
        time.sleep(0.1)
        

def show_time_input_screen():
    display.set_pen(BG_COLOR)
    display.clear()
    display.set_pen(TEXT_COLOR)
    display.text("Configurer la date/heure", 10, 10, WIDTH, 2)
    y_pos = 50
    for i, field in enumerate(FIELDS):
        value = field_values[field] if field != "Confirmer" else "OK"
        color = rgb565(255, 255, 0) if i == current_field_index else TEXT_COLOR
        display.set_pen(color)
        if field == "Confirmer":
            display.text(f"{field}: {value}", 10, y_pos, WIDTH, 2)
        else:
            display.text(f"{field}: {value:02d}", 10, y_pos, WIDTH, 2)
        y_pos += 30
    display.update()

def handle_time_button(button):
    """Gère les appuis sur les boutons dans l'écran de saisie du temps."""
    global current_field_index, start_time, in_menu  # Ajout de in_menu
    field = FIELDS[current_field_index]
    if button == "A" and field != "Confirmer":
        min_val, max_val = FIELD_VALUES[field]
        field_values[field] = min(field_values[field] + 1, max_val)
        if field == "Jour":
            max_day = get_max_day(field_values["Mois"], field_values["Année"])
            field_values[field] = min(field_values[field], max_day)
        show_time_input_screen()
    elif button == "B" and field != "Confirmer":
        min_val, max_val = FIELD_VALUES[field]
        field_values[field] = max(field_values[field] - 1, min_val)
        show_time_input_screen()
    elif button == "X":
        if field == "Confirmer":
            set_rtc_from_input()
            start_time = time.ticks_ms()
            current_field_index = 0  # Réinitialiser à "Jour" pour le prochain réglage
            in_menu = True          # Forcer l'affichage du menu après validation
            show_menu()             # Afficher le menu système
            return True
        else:
            current_field_index = (current_field_index + 1) % len(FIELDS)
            show_time_input_screen()
    return False

def set_rtc_from_input():
    year = field_values["Année"]
    month = field_values["Mois"]
    day = field_values["Jour"]
    hour = field_values["Heure"]
    minute = field_values["Minute"]
    try:
        rtc.datetime((year, month, day, 0, hour, minute, 0, None))
    except Exception as e:
        print(f"Erreur configuration RTC: {e}")

def get_max_day(month, year):
    if month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
    else:
        return 31

# --- Boucle principale ---
def main():
    global start_time
    init_storage()
    init_time_manager()
    start_time = time.ticks_ms()

    # Variables pour les intervalles
    last_acquisition_time = time.ticks_ms()  # Dernière sauvegarde CSV (5 min)
    last_display_time = time.ticks_ms()      # Dernier rafraîchissement affichage (5 s)
    ACQUISITION_INTERVAL = 300 * 1000        # 5 minutes en ms
    DISPLAY_INTERVAL = 5 * 1000              # 5 secondes en ms

    # Affichage initial
    show_bme680_data(0, 0, 0, 0)

    while True:
        current_time = time.ticks_ms()

        # Gestion des boutons
        button = get_button_pressed()
        if button:
            if button == "Y":
                show_menu()
            elif in_menu:
                handle_menu_button(button)
            else:
                if button == "A":
                    show_stats(1)  # Stats 24h
                elif button == "B":
                    show_stats(7)  # Stats 7j
                elif button == "X":
                    try:
                        temp = bme.read_temperature()
                        hum = bme.read_humidity()
                        press = bme.read_pressure() / 100
                        gas = bme.read_gas_resistance()
                        iaq = calculate_iaq(gas)
                        show_bme680_data(temp, hum, press, iaq)
                    except Exception as e:
                        print(f"Erreur lecture capteur: {e}")
                        show_bme680_data(0, 0, 0, 0)

        # Rafraîchissement de l'affichage toutes les 5 secondes
        if time.ticks_diff(current_time, last_display_time) >= DISPLAY_INTERVAL:
            try:
                temp = bme.read_temperature()
                hum = bme.read_humidity()
                press = bme.read_pressure() / 100
                gas = bme.read_gas_resistance()
                iaq = calculate_iaq(gas)
                show_bme680_data(temp, hum, press, iaq)
                last_display_time = current_time
            except Exception as e:
                print(f"Erreur rafraîchissement affichage: {e}")

        # Acquisition des données toutes les 5 minutes (sauvegarde CSV)
        if time.ticks_diff(current_time, last_acquisition_time) >= ACQUISITION_INTERVAL:
            try:
                temp = bme.read_temperature()
                hum = bme.read_humidity()
                press = bme.read_pressure() / 100
                gas = bme.read_gas_resistance()
                iaq = calculate_iaq(gas)
                timestamp = get_timestamp()
                write_data(timestamp, temp, hum, press, gas, iaq)
                last_acquisition_time = current_time
            except Exception as e:
                print(f"Erreur acquisition CSV: {e}")
                show_message(f"Erreur sauvegarde: {str(e)}", rgb565(255, 0, 0))
                time.sleep(1)
                show_bme680_data(0, 0, 0, 0)

        time.sleep(0.1)

if __name__ == "__main__":
    main()