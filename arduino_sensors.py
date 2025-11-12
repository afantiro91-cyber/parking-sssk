"""
Smart Parking System - Arduino IoT Integration
Spaja Arduino senzore sa Python backenom za real-time praćenje mjesta
"""

import json
import os
from datetime import datetime
from typing import Dict, List
import threading
import time

class ArduinoSensorManager:
    """Upravlja Arduino senzorima za praćenje parkirnih mjesta"""
    
    def __init__(self, total_spots: int = 5):
        """
        Inicijalizacija managera
        
        Args:
            total_spots: Ukupan broj parkirnih mjesta
        """
        self.total_spots = total_spots
        self.sensor_data = {}
        self.sensor_file = "sensor_data.json"
        self.monitoring = False
        
        # Inicijalizuj sve senzore kao slobodne
        for i in range(1, total_spots + 1):
            self.sensor_data[f'spot_{i}'] = {
                'spot_number': i,
                'occupied': False,
                'last_update': datetime.now().isoformat(),
                'sensor_id': f'SENSOR_{i}'
            }
        
        self.load_sensor_data()
    
    def load_sensor_data(self) -> None:
        """Učitaj prethodne podatke sa senzora"""
        if os.path.exists(self.sensor_file):
            try:
                with open(self.sensor_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sensor_data.update(data.get('sensors', {}))
                print("✅ Podaci sa senzora učitani")
            except Exception as e:
                print(f"⚠️ Greška pri učitavanju: {e}")
    
    def save_sensor_data(self) -> None:
        """Spremi podatke sa senzora u JSON"""
        try:
            data = {
                'sensors': self.sensor_data,
                'last_updated': datetime.now().isoformat(),
                'total_spots': self.total_spots
            }
            with open(self.sensor_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Greška pri spremanju: {e}")
    
    def update_spot_status(self, spot_number: int, occupied: bool) -> Dict:
        """
        Ažurira status parkirnog mjesta
        
        Args:
            spot_number: Broj mjesta (1-5)
            occupied: Da li je mjesto zauzeto
            
        Returns:
            Dict: Ažurirani status
        """
        spot_key = f'spot_{spot_number}'
        
        if spot_key not in self.sensor_data:
            return {
                'success': False,
                'message': f'❌ Mjesto {spot_number} ne postoji!'
            }
        
        old_status = self.sensor_data[spot_key]['occupied']
        self.sensor_data[spot_key]['occupied'] = occupied
        self.sensor_data[spot_key]['last_update'] = datetime.now().isoformat()
        
        self.save_sensor_data()
        
        action = "🚗 Zauzeto" if occupied else "✅ Oslobođeno"
        
        return {
            'success': True,
            'spot_number': spot_number,
            'occupied': occupied,
            'old_status': old_status,
            'action': action,
            'timestamp': self.sensor_data[spot_key]['last_update']
        }
    
    def get_free_spots(self) -> int:
        """Vrati broj slobodnih mjesta"""
        return sum(1 for spot in self.sensor_data.values() if not spot['occupied'])
    
    def get_occupied_spots(self) -> int:
        """Vrati broj zauzetih mjesta"""
        return sum(1 for spot in self.sensor_data.values() if spot['occupied'])
    
    def get_spots_status(self) -> Dict:
        """Vrati detaljno stanje svih mjesta"""
        return {
            'total_spots': self.total_spots,
            'free_spots': self.get_free_spots(),
            'occupied_spots': self.get_occupied_spots(),
            'occupancy_rate': round((self.get_occupied_spots() / self.total_spots) * 100, 2),
            'spots': self.sensor_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_spot_by_number(self, spot_number: int) -> Dict:
        """Vrati podatke o određenom mjestu"""
        spot_key = f'spot_{spot_number}'
        if spot_key in self.sensor_data:
            return {
                'success': True,
                'data': self.sensor_data[spot_key]
            }
        return {
            'success': False,
            'message': f'❌ Mjesto {spot_number} nije pronađeno'
        }
    
    def print_status(self) -> None:
        """Ispiši vizuelni prikaz parkirnog mjesta"""
        status = self.get_spots_status()
        
        print("\n" + "="*60)
        print("🚗 SMART PARKING - REAL-TIME PRAĆENJE SENZORA")
        print("="*60)
        print(f"Ukupna mjesta: {status['total_spots']}")
        print(f"Slobodna mjesta: {status['free_spots']}")
        print(f"Zauzeta mjesta: {status['occupied_spots']}")
        print(f"Popunjenost: {status['occupancy_rate']}%")
        print("-"*60)
        
        # Vizuelni prikaz
        for spot_key, spot in sorted(self.sensor_data.items()):
            status_symbol = "🚫" if spot['occupied'] else "✅"
            spot_num = spot['spot_number']
            print(f"{status_symbol} Mjesto {spot_num}: {'ZAUZETO' if spot['occupied'] else 'SLOBODNO'}")
        
        print("="*60 + "\n")


class ArduinoDataReceiver:
    """Simulira primanje podataka sa Arduino senzora"""
    
    def __init__(self, sensor_manager: ArduinoSensorManager):
        """
        Inicijalizacija
        
        Args:
            sensor_manager: Instanca ArduinoSensorManager-a
        """
        self.sensor_manager = sensor_manager
        self.listening = False
    
    def process_sensor_data(self, sensor_string: str) -> Dict:
        """
        Obradi podatke primljene sa Arduino-a
        
        Format: "SPOT:1:OCCUPIED" ili "SPOT:3:FREE"
        
        Args:
            sensor_string: String sa Arduino senzora
            
        Returns:
            Dict: Rezultat obrade
        """
        try:
            parts = sensor_string.strip().split(':')
            
            if len(parts) != 3 or parts[0] != 'SPOT':
                return {
                    'success': False,
                    'message': '❌ Neispravan format podataka!'
                }
            
            spot_number = int(parts[1])
            status = parts[2].upper()
            
            if status not in ['OCCUPIED', 'FREE']:
                return {
                    'success': False,
                    'message': '❌ Neispravan status!'
                }
            
            occupied = (status == 'OCCUPIED')
            result = self.sensor_manager.update_spot_status(spot_number, occupied)
            
            return result
        
        except ValueError:
            return {
                'success': False,
                'message': '❌ Greška pri parsiranju podataka!'
            }
    
    def simulate_sensor_readings(self, duration: int = 30) -> None:
        """
        Simulira čitanja sa senzora
        
        Args:
            duration: Kako dugo da simulira (sekunde)
        """
        import random
        
        print(f"\n🔄 Simulacija senzora početa ({duration} sekundi)...\n")
        self.listening = True
        
        start_time = time.time()
        
        while self.listening and (time.time() - start_time) < duration:
            # Nasumično odaberi mjesto i status
            spot = random.randint(1, self.sensor_manager.total_spots)
            status = random.choice(['OCCUPIED', 'FREE'])
            
            sensor_data = f"SPOT:{spot}:{status}"
            print(f"📡 Primljen: {sensor_data}")
            
            result = self.process_sensor_data(sensor_data)
            
            if result['success']:
                print(f"   → {result['action']}")
            else:
                print(f"   → {result['message']}")
            
            # Kratko čekanje između čitanja
            time.sleep(random.uniform(1, 3))
        
        self.listening = False
        print("\n✅ Simulacija završena")
    
    def start_monitoring_thread(self, duration: int = 60) -> threading.Thread:
        """
        Pokreni praćenje u zasebnoj niti
        
        Args:
            duration: Trajanje praćenja
            
        Returns:
            threading.Thread: Nit koja se izvršava
        """
        thread = threading.Thread(
            target=self.simulate_sensor_readings,
            args=(duration,),
            daemon=True
        )
        thread.start()
        return thread


def main():
    """Glavna funkcija - demo"""
    
    sensor_manager = ArduinoSensorManager(total_spots=5)
    receiver = ArduinoDataReceiver(sensor_manager)
    
    print("\n🚗 Arduino Smart Parking - Upravljač senzora\n")
    
    while True:
        print("\nOpcije:")
        print("1. Prikaži stanje parkiranja")
        print("2. Ažurira status mjesta")
        print("3. Simuliraj Arduino čitanja (30s)")
        print("4. Prikaži detaljne podatke mjesta")
        print("5. Izlaz")
        
        choice = input("\nOdaberi opciju (1-5): ").strip()
        
        if choice == '1':
            sensor_manager.print_status()
        
        elif choice == '2':
            try:
                spot = int(input("Unesi broj mjesta (1-5): "))
                status = input("Unesi status (OCCUPIED/FREE): ").upper()
                
                if status not in ['OCCUPIED', 'FREE']:
                    print("❌ Neispravan status!")
                    continue
                
                occupied = (status == 'OCCUPIED')
                result = receiver.process_sensor_data(f"SPOT:{spot}:{status}")
                
                if result['success']:
                    print(f"\n✅ {result['action']}")
                    print(f"Vrijeme: {result['timestamp']}")
                else:
                    print(f"\n❌ {result['message']}")
            
            except ValueError:
                print("❌ Neispravan unos!")
        
        elif choice == '3':
            receiver.simulate_sensor_readings(duration=30)
            sensor_manager.print_status()
        
        elif choice == '4':
            try:
                spot = int(input("Unesi broj mjesta: "))
                result = sensor_manager.get_spot_by_number(spot)
                
                if result['success']:
                    data = result['data']
                    print(f"\n📍 Mjesto {data['spot_number']}:")
                    print(f"   Senzor ID: {data['sensor_id']}")
                    print(f"   Status: {'🚫 ZAUZETO' if data['occupied'] else '✅ SLOBODNO'}")
                    print(f"   Posljednja ažuriranja: {data['last_update']}")
                else:
                    print(f"❌ {result['message']}")
            
            except ValueError:
                print("❌ Neispravan unos!")
        
        elif choice == '5':
            print("\n👋 Izlaz iz aplikacije")
            break
        
        else:
            print("❌ Neispravna opcija!")


if __name__ == "__main__":
    main()
