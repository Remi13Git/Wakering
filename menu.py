import asyncio
from config import VIBRATIONS
from alarm_manager import AlarmManager


class MenuManager:
   def __init__(self, ring):
       self.ring = ring
       self.alarm_manager = AlarmManager(ring)
      
   async def vibration_menu(self):
       """Menu des vibrations"""
       print("\n📳 === VIBRATIONS ===")
       for key, vib in VIBRATIONS.items():
           print(f"{key}. {vib['name']}")
       print("0. 🔙 Retour")
      
       choice = input("\n👉 Choix (0-5): ").strip()
      
       if choice == "0":
           return
       elif choice in VIBRATIONS:
           await self.ring.send_vibration(choice)
       else:
           print("❌ Option invalide")
  
   async def alarm_menu(self):
       """Menu des alarmes"""
       while True:
           print("\n⏰ === ALARMES ===")
          
           # Afficher les informations de statut
           status = self.alarm_manager.get_status_info()
           print(f"🕐 Heure actuelle: {status['current_time']}")
           print(f"📊 Surveillance: {'✅ Active' if status['monitoring_active'] else '❌ Inactive'}")
           print(f"📋 Alarmes: {status['active_alarms']}/{status['total_alarms']} actives")
           if status['next_alarm']:
               print(f"⏭️ Prochaine: {status['next_alarm']}")
          
           self.alarm_manager.list_alarms()
           print("\n1. ➕ Ajouter alarme")
           print("2. ❌ Supprimer alarme")
           print("3. 🔄 Activer/Désactiver alarme")
           print("4. 📋 Actualiser la liste")
           print("5. 🧪 Créer alarme de test (+1min)")
           print("6. 📳 Test vibration alarme")
           print("0. 🔙 Retour")
          
           choice = input("\n👉 Choix (0-6): ").strip()
          
           if choice == "0":
               break
           elif choice == "1":
               self.alarm_manager.create_alarm_interactive()
           elif choice == "2":
               try:
                   if not self.alarm_manager.alarms:
                       print("❌ Aucune alarme à supprimer")
                       continue
                   alarm_id = int(input("ID de l'alarme à supprimer: "))
                   self.alarm_manager.remove_alarm(alarm_id)
               except (ValueError, KeyboardInterrupt):
                   print("❌ Opération annulée")
           elif choice == "3":
               try:
                   if not self.alarm_manager.alarms:
                       print("❌ Aucune alarme à modifier")
                       continue
                   alarm_id = int(input("ID de l'alarme à modifier: "))
                   if not self.alarm_manager.toggle_alarm(alarm_id):
                       print("❌ Alarme introuvable")
               except (ValueError, KeyboardInterrupt):
                   print("❌ Opération annulée")
           elif choice == "4":
               continue  # Rafraîchit automatiquement
           elif choice == "5":
               self.alarm_manager.create_test_alarm()
           elif choice == "6":
               print("📳 Test de vibration d'alarme...")
               await self.ring.send_vibration("3")
           else:
               print("❌ Option invalide")
          
           await asyncio.sleep(0.5)
  
   async def main_menu(self):
       """Menu principal"""
       # Démarrer la surveillance des alarmes
       self.alarm_manager.start_monitoring()
      
       try:
           while True:
               self.ring.print_status()
               print("\n🎛️ === MENU ===")
               print("1. 📳 Vibrations")
               print("2. 💓 Fréquence cardiaque")
               print("3. 🫁 Saturation O2")
               print("4. 🌡️ Température")
               print("5. ⏰ Alarmes")
               print("6. 🔓 Unbind")
               print("0. 🚪 Quitter")
              
               choice = input("\n👉 Choix (0-6): ").strip()
              
               if choice == "1":
                   await self.vibration_menu()
               elif choice == "2":
                   await self.ring.measure('heartrate')
               elif choice == "3":
                   await self.ring.measure('o2')
               elif choice == "4":
                   await self.ring.measure('temperature')
               elif choice == "5":
                   await self.alarm_menu()
               elif choice == "6":
                   confirm = input("⚠️ Confirmer unbind? (o/N): ").strip().lower()
                   if confirm in ['o', 'oui', 'y', 'yes']:
                       if await self.ring.unbind():
                           break
               elif choice == "0":
                   print("👋 Au revoir!")
                   break
               else:
                   print("❌ Option invalide")
              
               await asyncio.sleep(1)
      
       finally:
           # Arrêter la surveillance des alarmes lors de la sortie
           self.alarm_manager.stop_monitoring()