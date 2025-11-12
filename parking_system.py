"""
Smart Parking System - Python Backend
Školski projekt za upravljanje parkirnim mjestima
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import qrcode
from io import BytesIO

class ParkingSystem:
    """Sistem za upravljanje parkirnim mjestima"""
    
    def __init__(self, total_spots: int = 5, invalid_spots: int = 1):
        """
        Inicijalizacija sistema
        
        Args:
            total_spots: Ukupan broj parkirnih mjesta
            invalid_spots: Broj mjesta za invalide
        """
        self.total_spots = total_spots
        self.invalid_spots = invalid_spots
        self.reserved_spots = []
        self.reservation_counter = 0
        self.data_file = "parking_data.json"
        
        # Učitaj podatke ako postoje
        self.load_data()
    
    def load_data(self) -> None:
        """Učitaj podatke iz JSON fajla"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.reserved_spots = data.get('reserved_spots', [])
                    self.reservation_counter = data.get('counter', 0)
                print("✅ Podaci učitani iz fajla")
            except Exception as e:
                print(f"❌ Greška pri učitavanju: {e}")
        else:
            print("📝 Nema prethodnih podataka")
    
    def save_data(self) -> None:
        """Spremi podatke u JSON fajl"""
        try:
            data = {
                'reserved_spots': self.reserved_spots,
                'counter': self.reservation_counter,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("✅ Podaci spremljeni")
        except Exception as e:
            print(f"❌ Greška pri spremanju: {e}")
    
    def get_available_spots(self) -> Tuple[int, int]:
        """
        Vrati broj slobodnih mjesta
        
        Returns:
            Tuple: (ukupno_slobodno, slobodno_za_invalide)
        """
        reserved_normal = sum(1 for spot in self.reserved_spots if spot['type'] == 'obicno')
        reserved_invalid = sum(1 for spot in self.reserved_spots if spot['type'] == 'invalid')
        
        available_normal = self.total_spots - self.invalid_spots - reserved_normal
        available_invalid = self.invalid_spots - reserved_invalid
        
        return available_normal + available_invalid, available_invalid
    
    def generate_qr_code(self, value: str) -> BytesIO:
        """
        Generiši QR kod
        
        Args:
            value: Vrijednost za QR kod
            
        Returns:
            BytesIO: QR kod kao slika
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(value)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        return img_io
    
    def reserve_spot(self, spot_type: str, user_name: str = "Nepoznat") -> Dict:
        """
        Rezerviši parkirno mjesto
        
        Args:
            spot_type: Tip mjesta ('obicno' ili 'invalid')
            user_name: Ime korisnika
            
        Returns:
            Dict: Rezultat rezervacije
        """
        available_total, available_invalid = self.get_available_spots()
        
        # Provjera dostupnosti
        if spot_type == 'invalid':
            if available_invalid <= 0:
                return {
                    'success': False,
                    'message': '🚫 Sva invalidska mjesta su zauzeta!',
                    'qr_code': None
                }
        else:
            if available_total <= 0:
                return {
                    'success': False,
                    'message': '🚫 Sva mjesta su zauzeta!',
                    'qr_code': None
                }
        
        # Generiši jedinstvenu rezervaciju
        self.reservation_counter += 1
        timestamp = datetime.now().isoformat()
        qr_value = f"Parking-{spot_type.upper()}-{self.reservation_counter}-{timestamp}"
        
        # Kreiraj rezervaciju
        reservation = {
            'id': self.reservation_counter,
            'type': spot_type,
            'user_name': user_name,
            'timestamp': timestamp,
            'qr_value': qr_value
        }
        
        self.reserved_spots.append(reservation)
        self.save_data()
        
        # Generiši QR kod
        qr_img = self.generate_qr_code(qr_value)
        
        return {
            'success': True,
            'message': f'✅ Mjesto ({spot_type}) je uspješno rezervisano!',
            'reservation_id': self.reservation_counter,
            'qr_code': qr_img,
            'qr_value': qr_value,
            'timestamp': timestamp
        }
    
    def get_status(self) -> Dict:
        """
        Vrati stanje sistema
        
        Returns:
            Dict: Detaljne informacije o sistemu
        """
        available_total, available_invalid = self.get_available_spots()
        
        return {
            'total_spots': self.total_spots,
            'invalid_spots': self.invalid_spots,
            'available_total': available_total,
            'available_invalid': available_invalid,
            'reserved_count': len(self.reserved_spots),
            'reservations': self.reserved_spots
        }

    def verify_code(self, code: str) -> Dict:
        """Provjeri da li prosleđeni QR kod odgovara nekoj rezervaciji.

        Returns:
            Dict: {'success': bool, 'reservation': reservation or None}
        """
        # Direct match with stored qr_value
        for res in self.reserved_spots:
            if res.get('qr_value') == code:
                return {'success': True, 'reservation': res}

        # Some QR scans may include surrounding URL or whitespace; try to find by id if numeric
        try:
            if '/' in code:
                # extract last path part
                last = code.rstrip('/').split('/')[-1]
                rid = int(last)
                for res in self.reserved_spots:
                    if res.get('id') == rid:
                        return {'success': True, 'reservation': res}
        except Exception:
            pass

        # fallback: check if code substring matches qr_value
        for res in self.reserved_spots:
            if res.get('qr_value') and res.get('qr_value') in code:
                return {'success': True, 'reservation': res}

        return {'success': False, 'reservation': None}
    
    def cancel_reservation(self, reservation_id: int) -> Dict:
        """
        Otkaži rezervaciju
        
        Args:
            reservation_id: ID rezervacije za otkazivanje
            
        Returns:
            Dict: Rezultat otkazivanja
        """
        for i, spot in enumerate(self.reserved_spots):
            if spot['id'] == reservation_id:
                cancelled = self.reserved_spots.pop(i)
                self.save_data()
                return {
                    'success': True,
                    'message': f'✅ Rezervacija {reservation_id} je otkazana!',
                    'cancelled_spot': cancelled
                }
        
        return {
            'success': False,
            'message': f'❌ Rezervacija {reservation_id} nije pronađena!'
        }
    
    def print_status(self) -> None:
        """Ispiši detaljnu analizu stanja"""
        status = self.get_status()
        
        print("\n" + "="*50)
        print("🚗 SMART PARKING SISTEM - STANJE")
        print("="*50)
        print(f"Ukupna mjesta: {status['total_spots']}")
        print(f"Mjesta za invalide: {status['invalid_spots']}")
        print(f"Slobodna mjesta: {status['available_total']}")
        print(f"Slobodna invalidska mjesta: {status['available_invalid']}")
        print(f"Zauzetih mjesta: {status['reserved_count']}")
        print("="*50)
        
        if status['reservations']:
            print("\n📋 Rezervacije:")
            for res in status['reservations']:
                print(f"  • ID: {res['id']} | Tip: {res['type']} | Korisnik: {res['user_name']}")
                print(f"    Vrijeme: {res['timestamp']}")
        else:
            print("\n📋 Nema aktivnih rezervacija")
        
        print("="*50 + "\n")


def main():
    """Glavna funkcija - demo primjer"""
    
    # Inicijalizuj sistem
    parking = ParkingSystem(total_spots=5, invalid_spots=1)
    
    print("\n🚗 Dobrodošli u Smart Parking Sistem!\n")
    
    while True:
        print("\nOpcije:")
        print("1. Rezerviši mjesto")
        print("2. Prikaži stanje")
        print("3. Otkaži rezervaciju")
        print("4. Izlaz")
        
        choice = input("\nOdaberi opciju (1-4): ").strip()
        
        if choice == '1':
            print("\nTip mjesta:")
            print("1. Obično mjesto")
            print("2. Mjesto za invalide")
            spot_choice = input("Odaberi (1 ili 2): ").strip()
            
            spot_type = 'invalid' if spot_choice == '2' else 'obicno'
            user_name = input("Unesi ime korisnika: ").strip() or "Nepoznat"
            
            result = parking.reserve_spot(spot_type, user_name)
            print(f"\n{result['message']}")
            
            if result['success']:
                print(f"ID Rezervacije: {result['reservation_id']}")
                print(f"QR vrijednost: {result['qr_value']}")
                print(f"Vrijeme: {result['timestamp']}")
                
                # Spremi QR kod kao sliku
                qr_file = f"qr_code_{result['reservation_id']}.png"
                with open(qr_file, 'wb') as f:
                    f.write(result['qr_code'].getvalue())
                print(f"QR kod spreman: {qr_file}")
        
        elif choice == '2':
            parking.print_status()
        
        elif choice == '3':
            try:
                res_id = int(input("Unesi ID rezervacije za otkazivanje: "))
                result = parking.cancel_reservation(res_id)
                print(f"\n{result['message']}")
            except ValueError:
                print("❌ Neispravna vrijednost!")
        
        elif choice == '4':
            print("\n👋 Hvala što ste koristili Smart Parking Sistem!")
            break
        
        else:
            print("❌ Neispravna opcija!")


if __name__ == "__main__":
    main()
