"""
Smart Parking System - Flask API Backend
Povezuje Python sa HTML/CSS/JS frontendom i Arduino senzorima
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from parking_system import ParkingSystem
import plates_access as plates_mod
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- Inicijalizacija sistema ---
parking = ParkingSystem(total_spots=15, invalid_spots=1)

# --- Folder za QR kodove i fajlove ---
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_AS_ASCII'] = False


# --- Glavna stranica ---
@app.route('/')
def index():
    return render_template('index.html')


# --- Status sistema ---
@app.route('/api/status', methods=['GET'])
def api_status():
    status = parking.get_status()
    return jsonify({'success': True, 'data': status})


# --- Rezervacija mjesta ---
@app.route('/api/reserve', methods=['POST'])
def api_reserve():
    try:
        data = request.get_json() or {}
        spot_type = data.get('spot_type', 'obicno')
        user_name = data.get('user_name', 'Nepoznat')

        # Rezerviši mjesto
        result = parking.reserve_spot(spot_type, user_name)

        if result['success']:
            # Spremi QR kod u fajl
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
            return jsonify({'success': False, 'message': result['message']}), 409

    except Exception as e:
        return jsonify({'success': False, 'message': f'Greška: {e}'}), 500


# --- Otkazivanje rezervacije ---
@app.route('/api/cancel/<int:reservation_id>', methods=['DELETE'])
def api_cancel(reservation_id):
    result = parking.cancel_reservation(reservation_id)
    status_code = 200 if result['success'] else 404
    return jsonify(result), status_code


# --- Preuzimanje QR koda ---
@app.route('/api/qr/<int:reservation_id>')
def api_qr(reservation_id):
    qr_file = f"qr_{reservation_id}.png"
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_file)
    if os.path.exists(qr_path):
        return send_file(qr_path, mimetype='image/png')
    return jsonify({'success': False, 'message': 'QR kod nije pronađen'}), 404


# --- Sve rezervacije ---
@app.route('/api/reservations', methods=['GET'])
def api_reservations():
    status = parking.get_status()
    return jsonify({
        'success': True,
        'reservations': status['reservations'],
        'total_count': len(status['reservations'])
    })


# --- Verifikacija QR koda ---
@app.route('/api/verify', methods=['POST'])
def api_verify():
    try:
        data = request.get_json() or {}
        code = data.get('code')
        if not code:
            return jsonify({'success': False, 'message': 'Nedostaje code parametar'}), 400

        result = parking.verify_code(code)
        if result['success']:
            res = result['reservation']
            return jsonify({'success': True, 'message': 'Access granted', 'reservation': res})
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    except Exception as e:
        return jsonify({'success': False, 'message': f'Greška: {e}'}), 500


# --- Plate admin ---
@app.route('/plates_admin')
def plates_admin_page():
    return send_file('plates_admin.html')


@app.route('/api/plates', methods=['GET'])
def api_get_plates():
    plates = plates_mod.load_plates() or []
    return jsonify({'success': True, 'plates': plates})


@app.route('/api/plates', methods=['POST'])
def api_set_plates():
    data = request.get_json() or {}
    plates = data.get('plates')
    if not isinstance(plates, list):
        return jsonify({'success': False, 'message': 'Invalid payload'}), 400
    plates_mod.save_plates(plates)
    return jsonify({'success': True})


@app.route('/api/plates/<int:spot>', methods=['PUT'])
def api_update_plate(spot: int):
    data = request.get_json() or {}
    plate = data.get('plate')
    if not plate:
        return jsonify({'success': False, 'message': 'Missing plate'}), 400
    plates = plates_mod.load_plates() or []
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
    plates = plates_mod.load_plates() or []
    new = [p for p in plates if p.get('spot') != spot]
    plates_mod.save_plates(new)
    return jsonify({'success': True})


@app.route('/api/verify_plate', methods=['POST'])
def api_verify_plate():
    data = request.get_json() or {}
    plate = data.get('plate')
    if not plate:
        return jsonify({'success': False, 'message': 'Missing plate'}), 400
    plates = plates_mod.load_plates() or []
    ok, spot = plates_mod.verify_plate(plates, plate)
    return jsonify({'success': ok, 'spot': spot})


# --- Error handlers ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Stranica nije pronađena'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'message': 'Greška na serveru'}), 500


if __name__ == '__main__':
    print("🚀 Smart Parking Flask Server pokrenut!")
    print("📍 Pristupite na: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
