import asyncio
import binascii
from bleak import BleakClient, BleakScanner
from config import *
from data_analyzer import DataAnalyzer




class Wakering:
   def __init__(self, address):
       self.address = address
       self.client = None
       self.analyzer = DataAnalyzer()
       self.is_authenticated = False
       self.measuring_type = None  # 'heartrate', 'o2', 'temperature', 'steps', None




   async def connect(self):
       """Se connecter à la bague"""
       print(f"🔍 Recherche de la bague...")
       devices = await BleakScanner.discover()
       target_device = None
      
       for device in devices:
           if (device.address.upper() == self.address.upper() or
               (device.name and ("aizo" in device.name.lower() or "ring" in device.name.lower()))):
               target_device = device
               break
      
       if not target_device:
           print("❌ Bague non trouvée")
           return False
      
       self.client = BleakClient(target_device)
       try:
           await self.client.connect()
           await self.client.start_notify(NOTIFY_CHAR_UUID, self.notification_handler)
           print("✅ Connecté")
           return True
       except Exception as e:
           print(f"❌ Erreur: {e}")
           return False




   def notification_handler(self, sender, data):
       """Gestionnaire des notifications"""
       hex_data = binascii.hexlify(data).decode('utf-8').upper()
       formatted_hex = ' '.join([hex_data[i:i+2] for i in range(0, len(hex_data), 2)])
      
       if self.measuring_type:
           print(f"📊 [{self.measuring_type.upper()}] {formatted_hex}")
           self.analyzer.store_data(self.measuring_type, data)
          
           if self.measuring_type == 'heartrate':
               self.analyzer.analyze_heartrate(data)
           elif self.measuring_type == 'o2':
               self.analyzer.analyze_o2(data)
           elif self.measuring_type == 'temperature':
               self.analyzer.analyze_temperature(data)
           elif self.measuring_type == 'steps':
               self.analyzer.analyze_steps(data)
       else:
           print(f"📨 {formatted_hex}")




   async def write_data(self, data_hex, char_uuid=None):
       """Écrire des données"""
       if not self.client or not self.client.is_connected:
           return False
      
       try:
           data_bytes = bytes.fromhex(data_hex.replace(' ', ''))
           write_uuid = char_uuid or WRITE_CHAR_UUID
           await self.client.write_gatt_char(write_uuid, data_bytes)
           await asyncio.sleep(0.5)
           return True
       except Exception as e:
           print(f"❌ Erreur d'écriture: {e}")
           return False




   async def authenticate(self):
       """Authentifier la bague"""
       print("🔐 Authentification...")
       success_count = 0
      
       for i, packet in enumerate(AUTH_PACKETS, 1):
           if await self.write_data(packet):
               success_count += 1
           await asyncio.sleep(0.8)
      
       self.is_authenticated = success_count == len(AUTH_PACKETS)
       print(f"✅ Authentifiée" if self.is_authenticated else "❌ Échec auth")
       return self.is_authenticated




   async def measure(self, measure_type, duration=20):
       """Effectuer une mesure"""
       if measure_type not in COMMANDS:
           return False
      
       # Pour les pas, mesure instantanée
       if measure_type == 'steps':
           print(f"🚶 Récupération du nombre de pas...")
           self.analyzer.clear_data(measure_type)
           self.measuring_type = measure_type
           
           # Envoyer commande
           success = await self.write_data(COMMANDS[measure_type])
           if not success:
               self.measuring_type = None
               return False
           
           # Attendre la réponse (2-3 secondes max)
           await asyncio.sleep(3)
           self.measuring_type = None
           
           # Afficher résultat
           if self.analyzer.current_steps is not None:
               print(f"🎯 Résultat: {self.analyzer.current_steps} pas")
               return True
           else:
               print("❌ Aucun résultat pour les pas")
               return False
       
       # Pour les autres mesures, fonctionnement normal
       print(f"⏳ Mesure {measure_type}...")
       self.analyzer.clear_data(measure_type)
       self.measuring_type = measure_type
      
       # Envoyer commande de démarrage
       char_uuid = HEARTRATE_WRITE_UUID if measure_type in ['heartrate', 'o2', 'temperature'] else WRITE_CHAR_UUID
       success = await self.write_data(COMMANDS[measure_type], char_uuid)
      
       if not success:
           self.measuring_type = None
           return False
      
       # Attendre pendant la mesure
       for i in range(duration):
           await asyncio.sleep(1)
           remaining = duration - i - 1
           if remaining > 0:
               print(f"⏱️ {remaining}s", end='\r')
      
       # Arrêter la mesure si nécessaire
       if measure_type == 'heartrate':
           await self.write_data(COMMANDS['heartrate_stop'])
      
       self.measuring_type = None
      
       # Afficher résultat
       if measure_type == 'heartrate':
           result = self.analyzer.current_bpm
           unit = "BPM"
       elif measure_type == 'o2':
           result = self.analyzer.current_o2
           unit = "%"
       elif measure_type == 'temperature':
           result = self.analyzer.current_temperature
           unit = "°C"
      
       if result is not None:
           print(f"\n🎯 Résultat: {result}{unit}")
           return True
       else:
           print(f"\n❌ Aucun résultat pour {measure_type}")
           return False




   async def send_vibration(self, vib_type):
       """Envoyer vibration"""
       if vib_type not in VIBRATIONS:
           return False
      
       vib = VIBRATIONS[vib_type]
       print(f"📳 {vib['name']}")
       return await self.write_data(vib['data'])




   async def unbind(self):
       """Dissocier la bague"""
       print("🔓 Unbind...")
       success = await self.write_data(COMMANDS['unbind'])
       if success:
           await asyncio.sleep(3)
           print("✅ Dissociée")
       return success




   def print_status(self):
       """Afficher le statut"""
       if self.client and self.client.is_connected:
           auth = "🔐 Auth" if self.is_authenticated else "🔒 Non auth"
           bpm = f"💓 {self.analyzer.current_bpm} BPM" if self.analyzer.current_bpm else "💓 -"
           o2 = f"🫁 {self.analyzer.current_o2}%" if self.analyzer.current_o2 else "🫁 -"
           temp = f"🌡️ {self.analyzer.current_temperature:.1f} °C" if self.analyzer.current_temperature else "🌡️ -"
           steps = f"🚶 {self.analyzer.current_steps} pas" if self.analyzer.current_steps is not None else "🚶 -"
          
           print(f"\n📊 ✅ Connectée | {auth} | {bpm} | {o2} | {temp} | {steps}")
       else:
           print("\n📊 ❌ Déconnectée")




   async def disconnect(self):
       """Se déconnecter"""
       if self.client and self.client.is_connected:
           await self.client.disconnect()
           print("🔌 Déconnectée")