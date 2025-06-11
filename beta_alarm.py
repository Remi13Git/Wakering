import asyncio
import binascii
from datetime import datetime

class AlarmManager:
    def __init__(self, wakering_instance):
        self.ring = wakering_instance
        self.alarms = {}  # {id: alarm_data}
        self.next_alarm_id = 1
        self.transaction_id = 0x12  # Commencer avec la valeur observée dans l'app
        
    def _encode_name_utf16(self, name):
        """Encoder le nom en UTF-16 Little Endian (max 10 caractères)"""
        if len(name) > 10:
            name = name[:10]
        return name.encode('utf-16le')
    
    def _create_day_mask(self, days):
        """Créer le masque des jours
        days peut être:
        - 'daily' : tous les jours (0x7F)
        - liste comme ['monday', 'tuesday'] : jours spécifiques
        - entier : masque direct
        """
        if isinstance(days, int):
            return days & 0x7F
        
        if days == 'daily':
            return 0x7F
        
        day_mapping = {
            'monday': 0x01, 'tuesday': 0x02, 'wednesday': 0x04,
            'thursday': 0x08, 'friday': 0x10, 'saturday': 0x20, 'sunday': 0x40
        }
        
        mask = 0
        for day in days:
            if day.lower() in day_mapping:
                mask |= day_mapping[day.lower()]
        
        return mask
    
    def _get_next_alarm_id(self):
        """Obtenir le prochain ID d'alarme disponible (1-5)"""
        for i in range(1, 6):
            if i not in self.alarms:
                return i
        return None  # Toutes les alarmes sont utilisées
    
    def _increment_transaction_id(self):
        """Incrémenter l'ID de transaction"""
        self.transaction_id = (self.transaction_id + 1) & 0xFF
        return self.transaction_id
    
    def _calculate_checksum(self, data):
        """Calcul du checksum sur les données (derniers 2 bytes)"""
        # Calculer sur tout sauf les 2 derniers bytes
        checksum = sum(data[:-2]) & 0xFFFF
        return [checksum & 0xFF, (checksum >> 8) & 0xFF]
    
    def _create_alarm_packet(self, alarm_id, name, hour, minute, day_mask, enabled):
        """Créer le paquet de création d'alarme selon le format observé"""
        
        # Packet de 55 bytes total comme dans l'app officielle
        packet = bytearray(55)
        
        # Header (15 bytes) - copié exactement de l'app officielle
        packet[0] = 0x00
        packet[1] = 0x31  # Longueur payload (49 bytes)
        packet[2] = 0x83
        packet[3] = 0x40
        packet[4] = 0x00
        packet[5] = self.transaction_id  # Transaction ID
        packet[6] = 0x34
        packet[7] = 0x34  # Commande création (pas 36!)
        
        # Timestamp pattern observé dans l'app (5 bytes)
        packet[8] = 0x19
        packet[9] = 0x06
        packet[10] = 0x0B  # Mois (novembre)
        packet[11] = 0x04  # Jour (04 comme dans la séquence)
        packet[12] = 0x19  # Valeur supplémentaire (19 comme dans la séquence)
        
        # Position 13: Pattern observé 0x38 (comme dans la séquence)
        packet[13] = 0x38
        
        # Configuration de l'alarme (6 bytes) - position 14-19
        packet[14] = 0x01           # Constante
        packet[15] = 0x05           # Type alarme
        packet[16] = day_mask       # Masque jours
        packet[17] = hour           # Heure
        packet[18] = minute         # Minutes en décimal direct
        packet[19] = 0x01 if enabled else 0x00  # État
        
        # Padding jusqu'à la position du nom (positions 20-47)
        for i in range(20, 48):
            packet[i] = 0x00
        
        # Nom UTF-16 à partir de la position 48
        name_utf16 = self._encode_name_utf16(name)
        name_start = 48
        name_end = min(name_start + len(name_utf16), 53)  # Laisser place pour checksum
        
        for i, byte_val in enumerate(name_utf16):
            if name_start + i < name_end:
                packet[name_start + i] = byte_val
        
        # Checksum sur les 2 derniers bytes (positions 53-54)
        # Calculer checksum sur les 53 premiers bytes
        checksum = sum(packet[:53]) & 0xFFFF
        packet[53] = checksum & 0xFF
        packet[54] = (checksum >> 8) & 0xFF
        
        return packet
    
    def _create_initialization_packet(self):
        """Créer le paquet d'initialisation (avant création d'alarme)"""
        packet = bytearray([
            0x00, 0x0A,              # Longueur payload (10 bytes)
            0x83, 0x40,              # Type
            0x00, self.transaction_id,  # Transaction ID
            0x34, 0x35,              # Commande initialisation
            0x19, 0x06, 0x0B, 0x04, 0x19,  # Timestamp pattern
            0x21                     # Init flag
        ])
        
        # Checksum sur les 2 derniers bytes
        checksum = sum(packet) & 0xFFFF
        packet.extend([checksum & 0xFF, (checksum >> 8) & 0xFF])
        
        return packet
    
    def _create_finalization_packet(self):
        """Créer le paquet de finalisation selon le format observé"""
        next_id = self._increment_transaction_id()
        
        packet = bytearray([
            0x00, 0x0A,              # Longueur payload (10 bytes)
            0x83, 0x40,              # Type
            0x00, next_id,           # Transaction ID incrémenté
            0x34, 0x35,              # Commande finalisation
            0x19, 0x06, 0x0B, 0x04, 0x19,  # Timestamp (même pattern que init)
            0x38                     # Finalisation flag (38 comme dans la séquence)
        ])
        
        # Checksum sur les 2 derniers bytes
        checksum = sum(packet) & 0xFFFF
        packet.extend([checksum & 0xFF, (checksum >> 8) & 0xFF])
        
        return packet
    
    def _create_closure_packet(self):
        """Créer le paquet de clôture (après finalisation)"""
        next_id = self._increment_transaction_id()
        
        packet = bytearray([
            0x00, 0x04,              # Longueur payload (4 bytes)
            0x83, 0x40,              # Type
            0x00, next_id,           # Transaction ID incrémenté
            0x81, 0x17               # Commande clôture
        ])
        
        # Checksum sur les 2 derniers bytes
        checksum = sum(packet) & 0xFFFF
        packet.extend([checksum & 0xFF, (checksum >> 8) & 0xFF])
        
        return packet
    
    def _packet_to_hex(self, packet):
        """Convertir un paquet en chaîne hexadécimale"""
        return ' '.join([f'{b:02X}' for b in packet])
    
    async def create_alarm(self, name, hour, minute, days='daily', enabled=True):
        """Créer une nouvelle alarme"""
        if not self.ring.client or not self.ring.client.is_connected:
            print("❌ Bague non connectée")
            return None
        
        # Validation
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            print("❌ Heure/minute invalide")
            return None
        
        alarm_id = self._get_next_alarm_id()
        if alarm_id is None:
            print("❌ Limite d'alarmes atteinte (5 max)")
            return None
        
        day_mask = self._create_day_mask(days)
        
        print(f"⏰ Création alarme '{name}' à {hour:02d}:{minute:02d}")
        
        try:
            # Phase 0: Initialisation (16 bytes) - NOUVEAU !
            init_packet = self._create_initialization_packet()
            init_hex = self._packet_to_hex(init_packet)
            print(f"📨 Init: {init_hex}")
            
            success = await self.ring.write_data(init_hex, char_uuid="00000101-0000-1000-8000-00805f9b34fb")
            if not success:
                print("❌ Échec initialisation")
                return None
            
            await asyncio.sleep(1)
            
            # Phase 1: Envoyer la configuration (55 bytes)
            packet = self._create_alarm_packet(alarm_id, name, hour, minute, day_mask, enabled)
            hex_packet = self._packet_to_hex(packet)
            print(f"📨 Config: {hex_packet}")
            
            # Utiliser l'UUID correct pour l'écriture
            success = await self.ring.write_data(hex_packet, char_uuid="00000101-0000-1000-8000-00805f9b34fb")
            if not success:
                print("❌ Échec envoi configuration")
                return None
            
            # Attendre la notification de réponse
            await asyncio.sleep(2)
            
            # Phase 2: Finalisation (16 bytes)
            final_packet = self._create_finalization_packet()
            final_hex = self._packet_to_hex(final_packet)
            print(f"📨 Final: {final_hex}")
            
            success = await self.ring.write_data(final_hex, char_uuid="00000101-0000-1000-8000-00805f9b34fb")
            if not success:
                print("❌ Échec finalisation")
                return None
            
            await asyncio.sleep(1)
            
            # Phase 3: Clôture (10 bytes) - NOUVEAU !
            closure_packet = self._create_closure_packet()
            closure_hex = self._packet_to_hex(closure_packet)
            print(f"📨 Closure: {closure_hex}")
            
            success = await self.ring.write_data(closure_hex, char_uuid="00000101-0000-1000-8000-00805f9b34fb")
            if not success:
                print("❌ Échec clôture")
                return None
            
            # Attendre la réponse complète
            await asyncio.sleep(2)
            
            # Sauvegarder l'alarme
            self.alarms[alarm_id] = {
                'name': name,
                'hour': hour,
                'minute': minute,
                'days': days,
                'day_mask': day_mask,
                'enabled': enabled
            }
            
            print(f"✅ Alarme créée avec ID {alarm_id}")
            return alarm_id
            
        except Exception as e:
            print(f"❌ Erreur création alarme: {e}")
            return None
    
    async def modify_alarm(self, alarm_id, name=None, hour=None, minute=None, days=None, enabled=None):
        """Modifier une alarme existante"""
        if alarm_id not in self.alarms:
            print(f"❌ Alarme {alarm_id} introuvable")
            return False
        
        # Récupérer les valeurs actuelles
        current = self.alarms[alarm_id].copy()
        
        # Appliquer les modifications
        if name is not None:
            current['name'] = name
        if hour is not None:
            current['hour'] = hour
        if minute is not None:
            current['minute'] = minute
        if days is not None:
            current['days'] = days
            current['day_mask'] = self._create_day_mask(days)
        if enabled is not None:
            current['enabled'] = enabled
        
        print(f"⏰ Modification alarme {alarm_id}")
        
        try:
            # Utiliser le même protocole de création
            packet = self._create_alarm_packet(
                alarm_id, current['name'], current['hour'], 
                current['minute'], current['day_mask'], current['enabled']
            )
            hex_packet = self._packet_to_hex(packet)
            print(f"📨 Modif: {hex_packet}")
            
            success = await self.ring.write_data(hex_packet, char_uuid="00000101-0000-1000-8000-00805f9b34fb")
            if not success:
                return False
            
            await asyncio.sleep(2)
            
            # Finalisation
            final_packet = self._create_finalization_packet()
            final_hex = self._packet_to_hex(final_packet)
            print(f"📨 Final: {final_hex}")
            
            success = await self.ring.write_data(final_hex, char_uuid="00000101-0000-1000-8000-00805f9b34fb")
            if not success:
                return False
            
            await asyncio.sleep(2)
            
            # Mettre à jour localement
            self.alarms[alarm_id] = current
            
            print(f"✅ Alarme {alarm_id} modifiée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur modification: {e}")
            return False
    
    async def delete_alarm(self, alarm_id):
        """Supprimer une alarme"""
        if alarm_id not in self.alarms:
            print(f"❌ Alarme {alarm_id} introuvable")
            return False
        
        current = self.alarms[alarm_id]
        print(f"🗑️ Suppression alarme {alarm_id} '{current['name']}'")
        
        try:
            # Pour la suppression, on envoie la config avec état désactivé
            # puis on supprime localement
            packet = self._create_alarm_packet(
                alarm_id, current['name'], current['hour'], 
                current['minute'], current['day_mask'], False  # Désactivé
            )
            
            # Modifier la commande pour suppression (34 35 au lieu de 34 34)
            packet[7] = 0x35
            
            hex_packet = self._packet_to_hex(packet)
            print(f"📨 Delete: {hex_packet}")
            
            success = await self.ring.write_data(hex_packet, char_uuid="00000101-0000-1000-8000-00805f9b34fb")
            if not success:
                return False
            
            await asyncio.sleep(2)
            
            # Finalisation
            final_packet = self._create_finalization_packet()
            final_hex = self._packet_to_hex(final_packet)
            print(f"📨 Final: {final_hex}")
            
            success = await self.ring.write_data(final_hex, char_uuid="00000101-0000-1000-8000-00805f9b34fb")
            if not success:
                return False
            
            await asyncio.sleep(2)
            
            # Supprimer localement
            del self.alarms[alarm_id]
            
            print(f"✅ Alarme {alarm_id} supprimée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression: {e}")
            return False
    
    def list_alarms(self):
        """Afficher toutes les alarmes"""
        if not self.alarms:
            print("📭 Aucune alarme configurée")
            return
        
        print("\n⏰ === ALARMES ===")
        for alarm_id, alarm in self.alarms.items():
            status = "🟢" if alarm['enabled'] else "🔴"
            days_str = "Quotidien" if alarm['days'] == 'daily' else str(alarm['days'])
            print(f"{alarm_id}. {status} {alarm['name']} - {alarm['hour']:02d}:{alarm['minute']:02d} ({days_str})")
    
    def get_alarm(self, alarm_id):
        """Récupérer une alarme par son ID"""
        return self.alarms.get(alarm_id)
    
    async def toggle_alarm(self, alarm_id):
        """Activer/désactiver une alarme"""
        if alarm_id not in self.alarms:
            print(f"❌ Alarme {alarm_id} introuvable")
            return False
        
        current_state = self.alarms[alarm_id]['enabled']
        return await self.modify_alarm(alarm_id, enabled=not current_state)