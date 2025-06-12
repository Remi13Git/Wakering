import time

class DataAnalyzer:
    def __init__(self):
        self.heartrate_data = []
        self.o2_data = []
        self.temperature_data = []
        self.steps_data = []
        self.current_bpm = None
        self.current_o2 = None
        self.current_temperature = None
        self.current_steps = None

    def clear_data(self, data_type):
        """Vider les données d'un type spécifique"""
        if data_type == 'heartrate':
            self.heartrate_data.clear()
            self.current_bpm = None
        elif data_type == 'o2':
            self.o2_data.clear()
            self.current_o2 = None
        elif data_type == 'temperature':
            self.temperature_data.clear()
            self.current_temperature = None
        elif data_type == 'steps':
            self.steps_data.clear()
            self.current_steps = None

    def analyze_heartrate(self, raw_data):
        """Analyse BPM à l'offset 14 des trames de 17 bytes"""
        if len(raw_data) == 17:
            expected_header = [0x00, 0x0B, 0x21, 0x40]
            if list(raw_data[:4]) == expected_header and raw_data[8] == 0x19 and raw_data[9] == 0x06:
                bpm_value = raw_data[14]
                if 40 <= bpm_value <= 200:
                    self.current_bpm = bpm_value
                    print(f"💓 ✅ BPM: {bpm_value}")
                    return bpm_value
        return None

    def analyze_o2(self, raw_data):
        """Analyse O2 à l'offset 14 des trames de 17 bytes"""
        if len(raw_data) == 17:
            expected_header = [0x00, 0x0B, 0x21, 0x40]
            if list(raw_data[:4]) == expected_header and raw_data[8] == 0x19 and raw_data[9] == 0x06:
                o2_value = raw_data[14]
                if 80 <= o2_value <= 100:
                    self.current_o2 = o2_value
                    print(f"🫁 ✅ O2: {o2_value}%")
                    return o2_value
        return None

    def analyze_temperature(self, raw_data):
        """Analyse température sur 2 bytes (offsets 14-15) des trames de 20 bytes"""
        if len(raw_data) == 20:
            expected_header = [0x00, 0x0E, 0x21, 0x40]
            if list(raw_data[:4]) == expected_header and raw_data[8] == 0x19 and raw_data[9] == 0x06:
                temp_raw = (raw_data[14] << 8) | raw_data[15]
                temp_celsius = temp_raw / 10.0
                if 30.0 <= temp_celsius <= 45.0:
                    self.current_temperature = temp_celsius
                    print(f"🌡️ ✅ Température: {temp_celsius:.1f}°C")
                    return temp_celsius
        return None

    def analyze_steps(self, raw_data):
        """Analyse des pas aux positions 16-17 des trames de 28 bytes"""
        if len(raw_data) == 28:
            expected_header = [0x00, 0x16, 0x21, 0x40]
            if list(raw_data[:4]) == expected_header:
                # Position 16 = multiples de 256, Position 17 = reste (0-255)
                multiples_256 = raw_data[16]  # Nombre de fois qu'on a dépassé 255
                remainder = raw_data[17]      # Reste (0-255)
                steps_value = (multiples_256 * 256) + remainder
                
                if 0 <= steps_value <= 65535:
                    self.current_steps = steps_value
                    print(f"🚶 ✅ Pas: {steps_value}")
                    return steps_value
        return None

    def store_data(self, data_type, raw_data):
        """Stocker les données reçues"""
        data_entry = {
            'timestamp': time.time(),
            'raw': raw_data
        }
                
        if data_type == 'heartrate':
            self.heartrate_data.append(data_entry)
        elif data_type == 'o2':
            self.o2_data.append(data_entry)
        elif data_type == 'temperature':
            self.temperature_data.append(data_entry)
        elif data_type == 'steps':
            self.steps_data.append(data_entry)