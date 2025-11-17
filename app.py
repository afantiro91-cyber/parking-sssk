"""
Smart Parking System - Flask API Backend
Povezuje Python sa HTML/CSS/JS frontenom i Arduino senzorima
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from parking_system import ParkingSystem
from arduino_sensors import ArduinoSensorManager, ArduinoDataReceiver
import plates_access as plates_mod
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Omogući CORS za Arduino zahtjeve
parking = ParkingSystem(total_spots=5, invalid_spots=1)
sensor_manager = ArduinoSensorManager(total_spots=5)
sensor_receiver = ArduinoDataReceiver(sensor_manager)

# Konfiguracija
app.config['JSON_AS_ASCII'] = False
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    """Prikaži glavnu stranicu"""
    return render_template('index.html')


@app.route('/api/status', methods=['GET'])
def api_status():
    """API endpoint za stanje sistema"""
    status = parking.get_status()
    return jsonify({
        'success': True,
        'data': status
    })


@app.route('/api/reserve', methods=['POST'])
def api_reserve():
    """API endpoint za rezervaciju mjesta"""
    try:
        data = request.get_json()
        
        # Validacija
        if not data or 'spot_type' not in data:
            return jsonify({
                'success': False,
                'message': '❌ Nedostaju obavezni podaci!'
            }), 400
        
        spot_type = data.get('spot_type', 'obicno')
        user_name = data.get('user_name', 'Nepoznat')
        
        # Provjera fajla ako je priložen
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': '❌ Molimo odaberi fajl!'
                }), 400
            
            # Spremi fajl
            if file:
                filename = f"{datetime.now().timestamp()}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Rezerviši mjesto
        result = parking.reserve_spot(spot_type, user_name)
        
        if result['success']:
            # Spremi QR kod
            qr_file = f"qr_{result['reservation_id']}.png"
            qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_file)
            with open(qr_path, 'wb') as f:
                f.write(result['qr_code'].getvalue())
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'reservation_id': result['reservation_id'],
                'qr_code_url': f'/api/qr/{result["reservation_id"]}',
                'qr_value': result['qr_value'],
                'timestamp': result['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 409  # Conflict - nema dostupnih mjesta
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Greška na serveru: {str(e)}'
        }), 500


@app.route('/api/cancel/<int:reservation_id>', methods=['DELETE'])
def api_cancel(reservation_id):
    """API endpoint za otkazivanje rezervacije"""
    result = parking.cancel_reservation(reservation_id)
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': result['message']
        })
    else:
        return jsonify({
            'success': False,
            'message': result['message']
        }), 404


@app.route('/api/qr/<int:reservation_id>')
def api_qr(reservation_id):
    """API endpoint za download QR koda"""
    qr_file = f"qr_{reservation_id}.png"
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_file)
    
    if os.path.exists(qr_path):
        return send_file(qr_path, mimetype='image/png')
    else:
        return jsonify({
            'success': False,
            'message': '❌ QR kod nije pronađen'
        }), 404


@app.route('/api/reservations', methods=['GET'])
def api_reservations():
    """API endpoint za sve rezervacije"""
    status = parking.get_status()
    return jsonify({
        'success': True,
        'reservations': status['reservations'],
        'total_count': len(status['reservations'])
    })


@app.route('/api/verify', methods=['POST'])
def api_verify():
        """Verificira skenirani QR kod (provjera dozvole za ulaz)

        Expected JSON: { "code": "...scanned string..." }
        Returns JSON: { success: bool, message: str, reservation: {...} }
        """
        try:
                data = request.get_json() or {}
                code = data.get('code')
                if not code:
                        return jsonify({'success': False, 'message': 'Nedostaje code parametar'}), 400

                result = parking.verify_code(code)
                if result['success']:
                        res = result['reservation']
                        return jsonify({'success': True, 'message': 'Access granted', 'reservation': res})
                else:
                        return jsonify({'success': False, 'message': 'Access denied'}), 403
        except Exception as e:
                return jsonify({'success': False, 'message': f'Greška: {e}'}), 500


@app.route('/scanner')
def scanner_page():
        """Serve a small camera QR scanner page that POSTs scanned code to /api/verify"""
        return '''
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>QR Scanner - Parkingsssk</title>
            <style>
                body{font-family:Segoe UI,Arial,sans-serif;text-align:center;padding:20px;background:#fafafa}
                #reader{width:320px;margin:0 auto}
                .status{margin-top:12px;font-weight:700}
                .granted{color:green}
                .denied{color:red}
                button{padding:10px 14px;border-radius:8px;border:none;background:#2b8a3e;color:#fff;font-weight:700}
            </style>
            <script src="https://unpkg.com/html5-qrcode@2.3.7/minified/html5-qrcode.min.js"></script>
        </head>
        <body>
            <h1>QR Scanner - Parkingsssk</h1>
            <div id="reader"></div>
            <p class="status" id="status">Kliknite Start za pokretanje kamere</p>
            <p><button id="startBtn">Start</button> <button id="stopBtn">Stop</button></p>
            <script>
                const startBtn=document.getElementById('startBtn');
                const stopBtn=document.getElementById('stopBtn');
                const status=document.getElementById('status');
                const html5QrCode = new Html5Qrcode("reader");

                // Helper: verify QR code string via /api/verify (for QR that contain reservation code)
                async function verifyCode(code){
                    try{
                        const res = await fetch('/api/verify', {
                            method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code})
                        });
                        const j = await res.json();
                        if(res.ok && j.success){ status.textContent='✅ Access granted — ' + (j.reservation?('ID:'+j.reservation.id):''); status.className='status granted'; }
                        else { status.textContent='⛔ Access denied'; status.className='status denied'; }
                    }catch(e){ status.textContent='Error: '+e; status.className='status denied'; }
                }

                // Helper: verify plate via /api/verify_plate (for plate query param)
                async function verifyPlate(plate){
                    try{
                        const res = await fetch('/api/verify_plate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({plate})});
                        const j = await res.json();
                        if(res.ok && j.success){ status.textContent='✅ Access granted — spot: ' + (j.spot||'N/A'); status.className='status granted'; }
                        else { status.textContent='⛔ Access denied'; status.className='status denied'; }
                    }catch(e){ status.textContent='Error: '+e; status.className='status denied'; }
                }

                // Called when camera successfully decodes a QR
                function onScanSuccess(decodedText, decodedResult){
                    // stop scanning and verify
                    html5QrCode.stop().then(()=>{
                        verifyCode(decodedText);
                    }).catch(()=>{ verifyCode(decodedText); });
                }

                // Check URL for ?plate=... and auto-verify if present
                (function checkQuery(){
                    try{
                        const params = new URLSearchParams(window.location.search);
                        const plate = params.get('plate');
                        if(plate){
                            status.textContent = 'Provjeravam tablicu...';
                            verifyPlate(plate);
                            // hide camera controls when verifying by plate
                            startBtn.style.display = 'none';
                            stopBtn.style.display = 'none';
                            return;
                        }
                    }catch(e){ /* ignore */ }
                })();

                startBtn.addEventListener('click', ()=>{
                    Html5Qrcode.getCameras().then(cameras=>{
                        if(cameras && cameras.length){
                            const camId=cameras[0].id;
                            html5QrCode.start(camId, { fps: 10, qrbox: 250 }, onScanSuccess, (err)=>{});
                            status.textContent='Scanning...'; status.className='status';
                        } else { status.textContent='No camera found'; }
                    }).catch(e=>status.textContent='Camera error: '+e);
                });

                stopBtn.addEventListener('click', ()=>{ html5QrCode.stop().then(()=>status.textContent='Stopped').catch(e=>status.textContent='Stop error:'+e); });
            </script>
        </body>
        </html>
        '''


@app.route('/plates_admin')
def plates_admin_page():
    """Serve simple plates admin HTML page where staff can type plates."""
    # send_file used because file is at project root
    return send_file('plates_admin.html')


@app.route('/api/plates', methods=['GET'])
def api_get_plates():
    plates = plates_mod.load_plates()
    return jsonify({'success': True, 'plates': plates})


@app.route('/api/plates', methods=['POST'])
def api_set_plates():
    data = request.get_json() or {}
    plates = data.get('plates')
    if not isinstance(plates, list):
        return jsonify({'success': False, 'message': 'Invalid payload, expected plates list'}), 400
    plates_mod.save_plates(plates)
    return jsonify({'success': True})


@app.route('/api/plates/<int:spot>', methods=['PUT'])
def api_update_plate(spot: int):
    data = request.get_json() or {}
    plate = data.get('plate')
    if not plate:
        return jsonify({'success': False, 'message': 'Missing plate'}), 400
    plates = plates_mod.load_plates()
    # update or add
    updated = False
    for p in plates:
        if p.get('spot') == spot:
            p['plate'] = plate
            updated = True
            break
    if not updated:
        plates.append({'spot': spot, 'plate': plate})
    plates.sort(key=lambda x: x['spot'])
    plates_mod.save_plates(plates)
    return jsonify({'success': True})


@app.route('/api/plates/<int:spot>', methods=['DELETE'])
def api_delete_plate(spot: int):
    plates = plates_mod.load_plates()
    new = [p for p in plates if p.get('spot') != spot]
    plates_mod.save_plates(new)
    return jsonify({'success': True})


@app.route('/api/verify_plate', methods=['POST'])
def api_verify_plate():
    data = request.get_json() or {}
    plate = data.get('plate')
    if not plate:
        return jsonify({'success': False, 'message': 'Missing plate'}), 400
    plates = plates_mod.load_plates()
    ok, spot = plates_mod.verify_plate(plates, plate)
    return jsonify({'success': ok, 'spot': spot})


@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({
        'success': False,
        'message': '❌ Stranica nije pronađena'
    }), 404


@app.errorhandler(500)
def server_error(error):
    """500 error handler"""
    return jsonify({
        'success': False,
        'message': '❌ Greška na serveru'
    }), 500


if __name__ == '__main__':
    print("🚀 Smart Parking Flask Server pokrenut!")
    print("📍 Pristupite na: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
