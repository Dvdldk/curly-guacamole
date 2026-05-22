# =============================================
# storage.py - Gestion du stockage des données
# Sauvegarde atomique, cache, et gestion de l'espace
# =============================================

import uos
import time
from utils import handle_error, COLORS, format_timestamp

class StorageManager:
    """Gère le stockage des données en CSV avec sauvegarde atomique."""

    def __init__(self):
        # Configuration du stockage
        self.MAX_FLASH_USAGE = 0.7  # 70% max de l'espace flash
        self.FLASH_SIZE = 2 * 1024 * 1024  # 2 Mo
        self.MAX_FILE_SIZE = int(self.MAX_FLASH_USAGE * self.FLASH_SIZE)

        # Noms des fichiers
        self.DATA_FILE = "data.csv"
        self.BACKUP_FILE = "data_backup.csv"
        self.TEMP_FILE = "data_temp.csv"

        # En-tête CSV
        self.CSV_HEADER = "timestamp,temperature,humidity,pressure,gas,iaq\n"
        self.LINE_FORMAT = "{},{:.2f},{:.2f},{:.2f},{},{}\n"

        # Cache des données
        self.data_cache = []
        self.last_cache_update = 0
        self.CACHE_INTERVAL = 60 * 1000  # 1 minute

        # Cache des stats
        self.stats_cache = {}
        self.last_stats_update = 0
        self.STATS_INTERVAL = 10 * 60 * 1000  # 10 minutes

        # Initialisation
        self.init_storage()

    def init_storage(self):
        """Initialise le stockage (crée le fichier CSV si nécessaire)."""
        try:
            uos.stat(self.DATA_FILE)
        except OSError:
            try:
                with open(self.DATA_FILE, "w") as f:
                    f.write(self.CSV_HEADER)
                print("Fichier CSV créé.")
            except Exception as e:
                handle_error(e, "Création CSV")

        # Vérifier l'intégrité du fichier
        if not self.check_csv_integrity():
            self.repair_csv()

    def get_file_size(self, filename):
        """Retourne la taille d'un fichier en octets."""
        try:
            return uos.stat(filename)[6]
        except OSError:
            return 0

    def get_free_space(self):
        """Retourne l'espace libre en octets."""
        try:
            stat = uos.statvfs('/')
            return stat[3] * stat[4]
        except:
            return 0

    def get_space_used_percent(self):
        """Retourne le pourcentage d'espace utilisé par le fichier CSV."""
        try:
            file_size = self.get_file_size(self.DATA_FILE)
            total_space = self.get_free_space() + file_size
            return (file_size / total_space) * 100 if total_space > 0 else 0.0
        except:
            return 0.0

    def get_line_count(self):
        """Retourne le nombre de lignes de données (hors en-tête)."""
        try:
            with open(self.DATA_FILE, "r") as f:
                return len(f.readlines()) - 1
        except OSError:
            return 0

    def check_csv_integrity(self):
        """Vérifie l'intégrité du fichier CSV."""
        try:
            with open(self.DATA_FILE, "r") as f:
                lines = f.readlines()
                if len(lines) < 1 or lines[0].strip() != self.CSV_HEADER.strip():
                    return False
                for line in lines[1:]:
                    if len(line.strip().split(',')) != 6:
                        return False
            return True
        except OSError:
            return False

    def repair_csv(self):
        """Répare le fichier CSV en supprimant les lignes corrompues."""
        if not self.check_csv_integrity():
            try:
                with open(self.DATA_FILE, "r") as f:
                    lines = f.readlines()

                # Garder seulement les lignes valides
                valid_lines = [lines[0]]  # Garder l'en-tête
                for line in lines[1:]:
                    if len(line.strip().split(',')) == 6:
                        valid_lines.append(line)

                # Réécrire le fichier
                with open(self.DATA_FILE, "w") as f:
                    f.writelines(valid_lines)
                print("Fichier CSV réparé.")
                return True
            except Exception as e:
                handle_error(e, "Réparation CSV")
                return False
        return True

    def write_data(self, timestamp, temp, humidity, pressure, gas, iaq):
        """
        Écrit les données dans le fichier CSV de manière atomique.
        """
        try:
            # Vérifier la taille avant d'écrire
            current_size = self.get_file_size(self.DATA_FILE)
            if (current_size + 100) >= self.MAX_FILE_SIZE:
                self.cleanup_old_entries()

            # Écrire dans un fichier temporaire d'abord
            with open(self.TEMP_FILE, "w") as f:
                f.write(self.CSV_HEADER)
                # Copier les anciennes données si le fichier existe
                try:
                    with open(self.DATA_FILE, "r") as old_f:
                        f.write(old_f.read())
                except OSError:
                    pass
                # Ajouter la nouvelle ligne
                line = self.LINE_FORMAT.format(timestamp, temp, humidity, pressure, gas, iaq)
                f.write(line)

            # Vérifier la taille avant de renommer
            temp_size = self.get_file_size(self.TEMP_FILE)
            if temp_size <= self.MAX_FILE_SIZE:
                uos.remove(self.DATA_FILE)
                uos.rename(self.TEMP_FILE, self.DATA_FILE)
                # Mettre à jour le cache
                self.update_cache()
            else:
                uos.remove(self.TEMP_FILE)
                self.cleanup_old_entries()
                # Réessayer
                self.write_data(timestamp, temp, humidity, pressure, gas, iaq)
        except Exception as e:
            handle_error(e, "Écriture CSV")
            # Nettoyer le fichier temporaire
            try:
                uos.remove(self.TEMP_FILE)
            except:
                pass

    def cleanup_old_entries(self):
        """Nettoie les anciennes entrées pour libérer de l'espace."""
        current_size = self.get_file_size(self.DATA_FILE)
        if current_size >= self.MAX_FILE_SIZE:
            try:
                with open(self.DATA_FILE, "r") as f:
                    lines = f.readlines()[1:]  # Ignorer l'en-tête

                if not lines:
                    return

                avg_line_size = current_size / len(lines) if lines else 100
                max_lines = int((self.MAX_FILE_SIZE * 0.9) / avg_line_size)

                if max_lines < len(lines):
                    lines_to_keep = lines[-max_lines:]
                    with open(self.BACKUP_FILE, "w") as f_backup:
                        f_backup.write(self.CSV_HEADER)
                        f_backup.writelines(lines_to_keep)
                    uos.remove(self.DATA_FILE)
                    uos.rename(self.BACKUP_FILE, self.DATA_FILE)
                    print(f"Nettoyage: {len(lines) - max_lines} lignes supprimées.")
            except OSError as e:
                handle_error(e, "Nettoyage CSV")

    def update_cache(self):
        """Met à jour le cache des données."""
        try:
            with open(self.DATA_FILE, "r") as f:
                self.data_cache = f.readlines()[1:]  # Ignorer l'en-tête
            self.last_cache_update = time.ticks_ms()
        except OSError:
            self.data_cache = []

    def get_cached_data(self):
        """Retourne les données en cache (met à jour si nécessaire)."""
        if time.ticks_diff(time.ticks_ms(), self.last_cache_update) > self.CACHE_INTERVAL:
            self.update_cache()
        return self.data_cache

    def get_stats(self, n_days):
        """
        Calcule les statistiques pour les derniers n_days.
        Retourne un dictionnaire avec min, max, avg pour chaque métrique.
        """
        try:
            current_time = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0))
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
            with open(self.DATA_FILE, "r") as f:
                lines = f.readlines()[1:]
                for line in lines:
                    parts = line.strip().split(',')
                    if len(parts) != 6:
                        continue
                    timestamp_str, temp, humidity, pressure, gas, iaq = parts
                    try:
                        # Parser le timestamp
                        year, month, day = map(int, timestamp_str.split()[0].split('-'))
                        hour, minute, second = map(int, timestamp_str.split()[1].split(':'))
                        line_time = time.mktime((year, month, day, hour, minute, second, 0, 0, 0))
                    except:
                        continue

                    if line_time < cutoff_time:
                        continue

                    # Mettre à jour les stats
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
            handle_error(e, "Lecture CSV pour stats")

        # Calculer les moyennes
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

    def get_cached_stats(self, n_days):
        """Retourne les stats en cache (met à jour si nécessaire)."""
        cache_key = f"{n_days}d"
        if (time.ticks_diff(time.ticks_ms(), self.last_stats_update) > self.STATS_INTERVAL or
            cache_key not in self.stats_cache):
            self.update_stats_cache()
        return self.stats_cache.get(cache_key, self.get_stats(n_days))

    def update_stats_cache(self):
        """Met à jour le cache des stats."""
        self.stats_cache = {
            "1d": self.get_stats(1),
            "7d": self.get_stats(7),
            "30d": self.get_stats(30),
        }
        self.last_stats_update = time.ticks_ms()

    def erase_data(self):
        """Efface toutes les données."""
        try:
            uos.remove(self.DATA_FILE)
            self.init_storage()
            self.data_cache = []
            self.stats_cache = {}
            print("Données effacées.")
            return True
        except OSError as e:
            handle_error(e, "Effacement données")
            return False

    def export_data(self):
        """Prépare les données pour l'export (retourne le chemin du fichier)."""
        return self.DATA_FILE