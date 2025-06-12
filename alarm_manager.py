import asyncio
import threading
from datetime import datetime, time
import json
import os


class AlarmManager:
   def __init__(self, ring):
       self.ring = ring
       self.alarms = []
       self.alarm_file = "alarms.json"
       self.running = False
       self.alarm_task = None
       self.load_alarms()
  
   def load_alarms(self):
       """Charger les alarmes depuis le fichier"""
       try:
           if os.path.exists(self.alarm_file):
               with open(self.alarm_file, 'r') as f:
                   self.alarms = json.load(f)
       except Exception as e:
           print(f"❌ Erreur chargement alarmes: {e}")
           self.alarms = []
  
   def save_alarms(self):
       """Sauvegarder les alarmes dans le fichier"""
       try:
           with open(self.alarm_file, 'w') as f:
               json.dump(self.alarms, f, indent=2)
       except Exception as e:
           print(f"❌ Erreur sauvegarde alarmes: {e}")
  
   def add_alarm(self, hour, minute, label="Alarme", enabled=True):
       """Ajouter une nouvelle alarme"""
       alarm_id = len(self.alarms) + 1
       alarm = {
           "id": alarm_id,
           "hour": hour,
           "minute": minute,
           "label": label,
           "enabled": enabled
       }
       self.alarms.append(alarm)
       self.save_alarms()
       print(f"✅ Alarme ajoutée: {hour:02d}:{minute:02d} - {label}")
       return alarm_id
  
   def remove_alarm(self, alarm_id):
       """Supprimer une alarme"""
       self.alarms = [a for a in self.alarms if a["id"] != alarm_id]
       self.save_alarms()
       print(f"✅ Alarme {alarm_id} supprimée")
  
   def toggle_alarm(self, alarm_id):
       """Activer/désactiver une alarme"""
       for alarm in self.alarms:
           if alarm["id"] == alarm_id:
               alarm["enabled"] = not alarm["enabled"]
               self.save_alarms()
               status = "activée" if alarm["enabled"] else "désactivée"
               print(f"✅ Alarme {alarm_id} {status}")
               return True
       return False
  
   def list_alarms(self):
       """Afficher toutes les alarmes"""
       if not self.alarms:
           print("📋 Aucune alarme configurée")
           return
      
       print("\n📋 === ALARMES ===")
       for alarm in self.alarms:
           status = "🟢" if alarm["enabled"] else "🔴"
           print(f"{alarm['id']}. {status} {alarm['hour']:02d}:{alarm['minute']:02d} - {alarm['label']}")
  
   async def check_alarms(self):
       """Vérifier les alarmes (boucle principale)"""
       last_triggered = {}  # Pour éviter les déclenchements multiples
      
       while self.running:
           try:
               current_time = datetime.now()
               current_hour = current_time.hour
               current_minute = current_time.minute
              
               # Debug: afficher l'heure actuelle toutes les minutes
               if current_time.second == 0:
                   print(f"🕐 Il est {current_hour:02d}:{current_minute:02d}")
              
               for alarm in self.alarms:
                   alarm_key = f"{alarm['id']}_{current_hour:02d}_{current_minute:02d}"
                  
                   if (alarm["enabled"] and
                       alarm["hour"] == current_hour and
                       alarm["minute"] == current_minute and
                       alarm_key not in last_triggered):
                      
                       # Marquer comme déclenchée pour cette minute
                       last_triggered[alarm_key] = True
                      
                       print(f"\n🚨🚨🚨 ALARME DÉCLENCHÉE! 🚨🚨🚨")
                       print(f"⏰ {alarm['hour']:02d}:{alarm['minute']:02d} - {alarm['label']}")
                       print("=" * 50)
                      
                       # Envoyer la vibration d'alarme
                       try:
                           if self.ring.client and self.ring.client.is_connected:
                               await self.ring.send_vibration("3")  # Vibration alarme
                               print("📳 Vibration envoyée!")
                           else:
                               print("❌ Bague non connectée - vibration non envoyée")
                       except Exception as e:
                           print(f"❌ Erreur vibration: {e}")
              
               # Nettoyer les déclenchements anciens (garder seulement la minute actuelle)
               current_keys = [k for k in last_triggered.keys()
                             if k.endswith(f"{current_hour:02d}_{current_minute:02d}")]
               last_triggered = {k: v for k, v in last_triggered.items() if k in current_keys}
              
           except Exception as e:
               print(f"❌ Erreur surveillance alarmes: {e}")
          
           await asyncio.sleep(1)  # Vérifier toutes les secondes
  
   def start_monitoring(self):
       """Démarrer la surveillance des alarmes"""
       if not self.running:
           self.running = True
           # Créer la tâche et la stocker pour pouvoir la suivre
           loop = asyncio.get_event_loop()
           self.alarm_task = loop.create_task(self.check_alarms())
           print("✅ Surveillance des alarmes démarrée")
           print(f"📊 {len([a for a in self.alarms if a['enabled']])} alarme(s) active(s)")
       else:
           print("⚠️ Surveillance déjà active")
  
   def stop_monitoring(self):
       """Arrêter la surveillance des alarmes"""
       if self.running:
           self.running = False
           if self.alarm_task and not self.alarm_task.done():
               self.alarm_task.cancel()
           print("⏹️ Surveillance des alarmes arrêtée")
       else:
           print("⚠️ Surveillance déjà arrêtée")
  
   def create_alarm_interactive(self):
       """Interface interactive pour créer une alarme"""
       try:
           print("\n⏰ === NOUVELLE ALARME ===")
           hour = int(input("Heure (0-23): "))
           minute = int(input("Minute (0-59): "))
           label = input("Label (optionnel): ").strip()
          
           if not (0 <= hour <= 23) or not (0 <= minute <= 59):
               print("❌ Heure invalide")
               return False
          
           if not label:
               label = f"Alarme {hour:02d}:{minute:02d}"
          
           self.add_alarm(hour, minute, label)
           return True
          
       except ValueError:
           print("❌ Format invalide")
           return False
       except KeyboardInterrupt:
           print("\n❌ Annulé")
           return False
  
   def create_test_alarm(self):
       """Créer une alarme de test dans 1 minute"""
       current_time = datetime.now()
       test_minute = (current_time.minute + 1) % 60
       test_hour = current_time.hour
       if current_time.minute == 59:  # Si on est à 59 minutes, passer à l'heure suivante
           test_hour = (test_hour + 1) % 24
      
       self.add_alarm(test_hour, test_minute, "🧪 Test Alarme", True)
       print(f"✅ Alarme de test créée pour {test_hour:02d}:{test_minute:02d}")
       print(f"⏰ Heure actuelle: {current_time.hour:02d}:{current_time.minute:02d}")
       return True
  
   def get_status_info(self):
       """Obtenir des informations de statut détaillées"""
       current_time = datetime.now()
       active_alarms = [a for a in self.alarms if a['enabled']]
      
       status = {
           'current_time': f"{current_time.hour:02d}:{current_time.minute:02d}:{current_time.second:02d}",
           'monitoring_active': self.running,
           'total_alarms': len(self.alarms),
           'active_alarms': len(active_alarms),
           'next_alarm': None
       }
      
       # Trouver la prochaine alarme
       if active_alarms:
           next_alarm = None
           min_diff = float('inf')
          
           for alarm in active_alarms:
               alarm_time = alarm['hour'] * 60 + alarm['minute']
               current_mins = current_time.hour * 60 + current_time.minute
              
               # Calculer la différence (en tenant compte du passage à minuit)
               diff = alarm_time - current_mins
               if diff < 0:
                   diff += 24 * 60  # Ajouter 24h si l'alarme est le lendemain
              
               if diff < min_diff:
                   min_diff = diff
                   next_alarm = alarm
          
           if next_alarm:
               status['next_alarm'] = f"{next_alarm['hour']:02d}:{next_alarm['minute']:02d} - {next_alarm['label']}"
      
       return status