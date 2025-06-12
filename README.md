# WakeRing - Wake Up Smart

Interface Python pour communiquer avec votre bague connecté via Bluetooth Low Energy (BLE).

## ✨ Fonctionnalités

- 🔌 **Connexion automatique** - Détection et connexion à la bague
- 🔐 **Authentification complète** - Séquence d'authentification en 11 paquets
- 💓 **Mesure de fréquence cardiaque** - Capture du BPM en temps réel
- 🫁 **Saturation en oxygène** - Mesure du taux d'O2 dans le sang
- 🌡️ **Température corporelle** - Monitoring de la température
- 🚶 **Nombre de pas** - Affichage du nombre de pas effectués
- 📳 **Vibrations** - 5 types de notifications (Tips, Santé, Alarme, Appel, Rappel)
- 🔓 **Unbind** - Dissociation de la bague
- 📊 **Interface interactive** - Menu en ligne de commande 

## 🚀 Installation

### Prérequis
- Python 3.7+
- Bluetooth activé sur votre machine
- Bague compatible

### Configuration

1. **Cloner/télécharger le projet**
   ```bash
   git clone <votre-repo>
   cd wakering
   ```

2. **Créer l'environnement virtuel**
   ```bash
   python -m venv venv
   ```

3. **Activer l'environnement**
   ```bash
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

4. **Installer les dépendances**
   ```bash
   pip install bleak asyncio
   ```

5. **Configurer votre bague**
   
   Modifiez l'adresse dans `config.py` :
   ```python
   RING_ADDRESS = "VOTRE-ADRESSE-BAGUE"
   ```

## 🎮 Utilisation

### Lancement rapide
```bash
source venv/bin/activate
python main.py
```

### Menu principal
```
🎛️ === MENU ===
1. 📳 Vibrations
2. 💓 Fréquence cardiaque
3. 🫁 Saturation O2
4. 🌡️ Température
5. 🚶 Nombre de pas
6. ⏰ Alarmes
7. 🔓 Unbind
0. 🚪 Quitter
```

### Types de vibrations disponibles
- 💡 **Tips** - Conseils et astuces
- 🏥 **Alerte santé** - Notifications santé
- ⏰ **Alarme** - Réveils et alarmes
- 📞 **Appel** - Notifications d'appel
- 📅 **Rappel** - Rappels d'événements

## 📁 Structure du projet

```
wakering/
├── alarm_manager.py    # Configuration des alarmes
├── config.py           # Configuration et constantes
├── data_analyzer.py    # Analyse des données capteurs
├── wakering.py         # Classe principale de communication
├── menu.py             # Interface utilisateur
├── main.py             # Point d'entrée
└── venv/               # Environnement virtuel
```

## 🔧 Configuration avancée

### Modifier l'adresse de la bague
Dans `config.py`, changez :
```python
RING_ADDRESS = "38501439-08EC-00D8-9D8C-08A9FF1B1ACB"
```

### Identifier les commandes
Les commandes Bluetooth sont définies dans `config.py` :
```python
COMMANDS = {
    'heartrate': "00 06 83 40 01 62 31 51 01 01 94 73",
    'o2': "00 06 83 40 00 1F 31 51 02 01 C1 20",
    # ...
}
```

## 📊 Données collectées

### Fréquence cardiaque
- **Format** : BPM (battements par minute)
- **Plage** : 40-200 BPM
- **Position** : Offset 14 des trames 17 bytes

### Saturation O2
- **Format** : Pourcentage (%)
- **Plage** : 80-100%
- **Position** : Offset 14 des trames 17 bytes

### Température
- **Format** : Degrés Celsius (°C)
- **Plage** : 30-45°C
- **Position** : Offsets 14-15 des trames 20 bytes (Big Endian / 10)

### Nombre de pas
- **Format** : Little endian
- **Plage** : 0-65535
- **Position** : Offsets 16-17 des trames 28 bytes

## 🐛 Dépannage

### Bague non détectée
1. Vérifiez que la bague est allumée
2. Activez le mode pairing sur la bague
3. Vérifiez que le Bluetooth est activé
4. Essayez de redémarrer le script

### Échec d'authentification
1. Relancez le processus d'authentification (option 7)
2. Vérifiez que la bague n'est pas connectée à un autre appareil
3. Redémarrez la bague si nécessaire

### Mesures incohérentes
1. Assurez-vous que votre doigt est bien placé sur le capteur
2. Restez immobile pendant la mesure
3. Nettoyez le capteur de la bague

## 🔒 Sécurité

- Les données ne sont pas sauvegardées automatiquement
- Aucune donnée n'est transmise sur internet
- Toutes les communications restent locales (Bluetooth)

## 📝 Licence

Ce projet est développé à des fins éducatives et de recherche. Utilisez-le de manière responsable et conformément aux lois locales.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Ajouter de nouvelles fonctionnalités

## ⚠️ Avertissement

Ce logiciel est fourni "tel quel" sans garantie. Les mesures obtenues ne doivent pas remplacer un avis médical professionnel.