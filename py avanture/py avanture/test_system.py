"""
Smart Parking - Test Script
Testiraj sve komponente bez hardware-a
"""

import requests
import json
import time
from datetime import datetime

# Konfiguracija
SERVER_URL = "http://localhost:5000"
API_ENDPOINTS = {
    'status': f'{SERVER_URL}/api/status',
    'realtime': f'{SERVER_URL}/api/realtime',
    'sensors': f'{SERVER_URL}/api/sensors/status',
    'arduino': f'{SERVER_URL}/api/arduino'
}

def print_header(text):
    """Ispis zaglavlja"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_server_connection():
    """Test: Jeli server dostupan?"""
    print_header("TEST 1: Konekcija sa serverom")
    
    try:
        response = requests.get(f'{SERVER_URL}/', timeout=5)
        print(f"✅ Server je dostupan!")
        print(f"   Status code: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Server nije dostupan!")
        print(f"   Pokušaj: python app.py")
        return False
    except Exception as e:
        print(f"❌ Greška: {e}")
        return False

def test_status_endpoint():
    """Test: Provjera /api/status"""
    print_header("TEST 2: Parking status")
    
    try:
        response = requests.get(API_ENDPOINTS['status'])
        data = response.json()
        
        if data.get('success'):
            parking = data.get('data', {})
            print(f"✅ /api/status radi!")
            print(f"   Ukupna mjesta: {parking.get('total_spots')}")
            print(f"   Dostupna mjesta: {parking.get('available_total')}")
            print(f"   Mjesta za invalide: {parking.get('invalid_spots')}")
            print(f"   Dostupna za invalide: {parking.get('available_invalid')}")
            return True
        else:
            print("❌ API vratio error")
            return False
    except Exception as e:
        print(f"❌ Greška: {e}")
        return False

def test_sensors_endpoint():
    """Test: Provjera /api/sensors/status"""
    print_header("TEST 3: Senzor status")
    
    try:
        response = requests.get(API_ENDPOINTS['sensors'])
        data = response.json()
        
        if data.get('success'):
            sensors = data.get('data', {})
            print(f"✅ /api/sensors/status radi!")
            print(f"   Ukupna mjesta: {sensors.get('total_spots')}")
            print(f"   Slobodna: {sensors.get('free_spots')}")
            print(f"   Zauzeta: {sensors.get('occupied_spots')}")
            print(f"   Popunjenost: {sensors.get('occupancy_rate')}%")
            
            # Prikaži detaljno
            print(f"\n   Detaljno:")
            for spot_key, spot in sensors.get('spots', {}).items():
                status = "🚫 ZAUZETO" if spot['occupied'] else "✅ SLOBODNO"
                print(f"      Mjesto {spot['spot_number']}: {status}")
            
            return True
        else:
            print("❌ API vratio error")
            return False
    except Exception as e:
        print(f"❌ Greška: {e}")
        return False

def test_realtime_endpoint():
    """Test: Provjera /api/realtime"""
    print_header("TEST 4: Real-time (kombinovano)")
    
    try:
        response = requests.get(API_ENDPOINTS['realtime'])
        data = response.json()
        
        if data.get('success'):
            print(f"✅ /api/realtime radi!")
            print(f"\n   PARKING INFO:")
            parking = data.get('parking', {})
            print(f"      Dostupnih: {parking.get('available_total')}")
            print(f"      Rezervisanih: {parking.get('reserved_count')}")
            
            print(f"\n   SENZOR INFO:")
            sensors = data.get('sensors', {})
            print(f"      Slobodnih: {sensors.get('free_spots')}")
            print(f"      Zauzetih: {sensors.get('occupied_spots')}")
            
            return True
        else:
            print("❌ API vratio error")
            return False
    except Exception as e:
        print(f"❌ Greška: {e}")
        return False

def test_arduino_endpoint():
    """Test: Provjera /api/arduino - Simulacija Arduino podataka"""
    print_header("TEST 5: Arduino endpoint (simulacija)")
    
    try:
        # Test 1: OCCUPIED
        print("📡 Pošalji: SPOT:1:OCCUPIED")
        response = requests.get(f'{API_ENDPOINTS["arduino"]}?spot=1&status=OCCUPIED')
        data = response.json()
        
        if data.get('success'):
            print(f"✅ Odgovor: {data.get('message')}")
        else:
            print(f"❌ {data.get('message')}")
        
        time.sleep(1)
        
        # Test 2: FREE
        print("📡 Pošalji: SPOT:1:FREE")
        response = requests.get(f'{API_ENDPOINTS["arduino"]}?spot=1&status=FREE')
        data = response.json()
        
        if data.get('success'):
            print(f"✅ Odgovor: {data.get('message')}")
            return True
        else:
            print(f"❌ {data.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Greška: {e}")
        return False

def test_multiple_sensors():
    """Test: Simulacija više senzora"""
    print_header("TEST 6: Simulacija više senzora")
    
    try:
        print("📡 Simulacija svih 5 mjesta...\n")
        
        for spot in range(1, 6):
            status = "OCCUPIED" if spot % 2 == 0 else "FREE"
            print(f"   Mjesto {spot}: {status}", end="")
            
            response = requests.get(
                f'{API_ENDPOINTS["arduino"]}?spot={spot}&status={status}'
            )
            data = response.json()
            
            if data.get('success'):
                print(" ✅")
            else:
                print(" ❌")
            
            time.sleep(0.5)
        
        # Provjeri konačni status
        print("\n   Konačan status:")
        response = requests.get(API_ENDPOINTS['sensors'])
        data = response.json()
        sensors = data.get('data', {})
        print(f"   Slobodnih: {sensors.get('free_spots')}")
        print(f"   Zauzetih: {sensors.get('occupied_spots')}")
        
        return True
    except Exception as e:
        print(f"❌ Greška: {e}")
        return False

def test_json_files():
    """Test: Provjera JSON fajlova"""
    print_header("TEST 7: JSON fajlovi (persistence)")
    
    import os
    
    files = ['sensor_data.json', 'parking_data.json']
    
    for filename in files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {filename}")
                print(f"   Zadnje ažuriranje: {data.get('last_updated', 'N/A')}")
            except Exception as e:
                print(f"❌ {filename}: {e}")
        else:
            print(f"⚠️ {filename} - nije pronađen (generisat će se)")

def run_continuous_test(duration=30):
    """Test: Kontinuirano praćenje - simulacija Arduino-a"""
    print_header(f"TEST 8: Kontinuirano praćenje ({duration}s)")
    
    import random
    
    print(f"Simuliram Arduino čitanja {duration} sekundi...\n")
    
    start_time = time.time()
    count = 0
    
    while time.time() - start_time < duration:
        spot = random.randint(1, 5)
        status = random.choice(['OCCUPIED', 'FREE'])
        
        try:
            response = requests.get(
                f'{API_ENDPOINTS["arduino"]}?spot={spot}&status={status}',
                timeout=5
            )
            data = response.json()
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if data.get('success'):
                emoji = "🚫" if status == "OCCUPIED" else "✅"
                print(f"[{timestamp}] {emoji} Mjesto {spot}: {status}")
                count += 1
            
        except Exception as e:
            print(f"❌ Greška: {e}")
        
        time.sleep(random.uniform(1, 3))
    
    print(f"\n✅ Ukupno slanih: {count} podataka")
    return True

def main():
    """Glavna funkcija"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     Smart Parking System - TEST SCRIPT                ║
    ║                                                        ║
    ║  Prije pokretanja, pokreni:                           ║
    ║    python app.py                                      ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'Server konekcija': False,
        'Status endpoint': False,
        'Senzor endpoint': False,
        'Real-time endpoint': False,
        'Arduino endpoint': False,
        'Više senzora': False,
        'JSON fajlovi': False,
        'Kontinuirano': False
    }
    
    # Pokretaj testove
    print("⏳ Pokretam testove...\n")
    
    results['Server konekcija'] = test_server_connection()
    if not results['Server konekcija']:
        print("\n❌ Trebam pristup serveru za ostatak testova!")
        return
    
    results['Status endpoint'] = test_status_endpoint()
    results['Senzor endpoint'] = test_sensors_endpoint()
    results['Real-time endpoint'] = test_realtime_endpoint()
    results['Arduino endpoint'] = test_arduino_endpoint()
    results['Više senzora'] = test_multiple_sensors()
    
    test_json_files()
    
    # Pitaj za kontinuirani test
    print_header("Dodatni test")
    choice = input("Želiš li kontinuirani test 30 sekundi? (y/n): ").strip().lower()
    if choice == 'y':
        results['Kontinuirano'] = run_continuous_test(30)
    
    # Summary
    print_header("REZULTATI")
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\nUkupno: {passed}/{total} testova prošlo")
    
    if passed == total:
        print("\n🎉 SVE JE RADILO! Sistem je spreman!")
    else:
        print("\n⚠️ Neki testovi nisu prošli. Provjeri grešku gore.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test prekinut!")
    except Exception as e:
        print(f"\n❌ Greška: {e}")
