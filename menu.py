import asyncio
from config import VIBRATIONS


class MenuManager:
   def __init__(self, ring):
       self.ring = ring


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


   async def main_menu(self):
       """Menu principal"""
       while True:
           self.ring.print_status()
           print("\n🎛️ === MENU ===")
           print("1. 📳 Vibrations")
           print("2. 💓 Fréquence cardiaque")
           print("3. 🫁 Saturation O2")
           print("4. 🌡️ Température")
           print("5. 🔓 Unbind")
           print("0. 🚪 Quitter")
          
           choice = input("\n👉 Choix (0-5): ").strip()
          
           if choice == "1":
               await self.vibration_menu()
           elif choice == "2":
               await self.ring.measure('heartrate')
           elif choice == "3":
               await self.ring.measure('o2')
           elif choice == "4":
               await self.ring.measure('temperature')
           elif choice == "5":
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