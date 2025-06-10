import asyncio
from wakering import Wakering
from menu import MenuManager
from config import RING_ADDRESS

async def main():
    print("🔧 === WAKERING ===")
    print("🚀 Connexion + Authentification + Menu")
    print("⚠️ Bague allumée et en mode pairing requis\n")
    
    ring = Wakering(RING_ADDRESS)
    menu = MenuManager(ring)
    
    try:
        # Connexion
        print("🔌 === CONNEXION ===")
        if not await ring.connect():
            print("❌ Impossible de se connecter")
            return
        
        # Authentification
        print("\n🔐 === AUTHENTIFICATION ===")
        auth_success = await ring.authenticate()
        
        if not auth_success:
            confirm = input("❓ Continuer sans auth? (o/N): ").strip().lower()
            if confirm not in ['o', 'oui', 'y', 'yes']:
                return
        
        print("\n🎉 Prêt!")
        await asyncio.sleep(1)
        
        # Menu interactif
        await menu.main_menu()
        
    except KeyboardInterrupt:
        print("\n⚠️ Interruption")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        await ring.disconnect()
        print("✅ Terminé")

if __name__ == "__main__":
    asyncio.run(main())