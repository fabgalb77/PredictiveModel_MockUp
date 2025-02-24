import os
import json
from flask import render_template, redirect, url_for, session, request, jsonify
from functools import wraps
from models.patient import get_all_patients, get_patient_by_id

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def init_routes(app):
    @app.route('/')
    @login_required
    def index():
        patients = get_all_patients()
        return render_template('patient_list.html', patients=patients)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if username in app.config['USERS'] and app.config['USERS'][username] == password:
                session['username'] = username
                return redirect(url_for('index'))
            error = 'Invalid credentials'
        
        return render_template('login.html', error=error)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/patient/<patient_id>')
    @login_required
    def patient_details(patient_id):
        patient = get_patient_by_id(patient_id)
        if patient:
            return render_template('patient_viewer.html', patient=patient)
        return "Patient not found", 404
        
    @app.route('/add_patient')
    @login_required
    def add_patient():
        return render_template('patient_form.html', is_edit=False, patient=None)
        
    @app.route('/edit_patient/<patient_id>')
    @login_required
    def edit_patient(patient_id):
        patient = get_patient_by_id(patient_id)
        if patient:
            return render_template('patient_form.html', is_edit=True, patient=patient)
        return "Patient not found", 404

    @app.route('/series_info/<patient_id>/<series_folder>')
    @login_required
    def series_info(patient_id, series_folder):
        """Get information about a DICOM series"""
        from flask import jsonify
        import os
        
        try:
            base_path = os.path.join('imaging', patient_id, series_folder)
            
            # Count slices for MRI series
            if series_folder.startswith('MRI'):
                files = sorted([f for f in os.listdir(base_path) if f.endswith('.dcm')])
                return jsonify({
                    'slices': len(files),
                    'description': series_folder.replace('_', ' ')
                })
            else:
                return jsonify({
                    'slices': 1,
                    'description': series_folder.replace('_', ' ')
                })
                
        except Exception as e:
            app.logger.error(f"Error getting series info: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/patient_image/<patient_id>/<series_folder>/<int:slice_index>')
    @login_required
    def patient_image(patient_id, series_folder, slice_index):
        """Serve DICOM images as PNG"""
        from flask import send_file
        import os
        import pydicom
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import io
        import numpy as np
        
        try:
            # Define path to imaging folder
            base_path = os.path.join('imaging', patient_id, series_folder)
            
            # Handle different series types
            if series_folder.startswith('MRI'):
                # For MRI, get the appropriate slice from the series
                files = sorted([f for f in os.listdir(base_path) if f.endswith('.dcm')])
                if slice_index >= len(files):
                    slice_index = len(files) - 1
                    
                file_path = os.path.join(base_path, files[slice_index])
                
            else:
                # For X-rays, there's typically just one file
                files = [f for f in os.listdir(base_path) if f.endswith('.dcm')]
                file_path = os.path.join(base_path, files[0])
            
            # Read DICOM and convert to PNG
            dcm = pydicom.dcmread(file_path)
            pixel_array = dcm.pixel_array
            
            # Smart normalization using DICOM Photometric Interpretation
            if series_folder.startswith('XRAY'):
                # Check Photometric Interpretation tag (0028,0004)
                photo_interp = 'MONOCHROME2'  # Default if not specified
                if hasattr(dcm, 'PhotometricInterpretation'):
                    photo_interp = dcm.PhotometricInterpretation
                
                # MONOCHROME1: high values = dark (needs inversion for display)
                # MONOCHROME2: high values = bright (standard display)
                needs_inversion = photo_interp.strip() == 'MONOCHROME1'
                
                if needs_inversion:
                    # Invert if MONOCHROME1
                    pixel_array = np.max(pixel_array) - pixel_array
                
                # Apply contrast stretching with percentile clipping
                p_low, p_high = np.percentile(pixel_array, [1, 99])
                pixel_array = np.clip(pixel_array, p_low, p_high)
                
                # Rescale to 0-255
                if p_high > p_low:
                    pixel_array = ((pixel_array - p_low) / (p_high - p_low) * 255).astype(np.uint8)
                else:
                    pixel_array = ((pixel_array - np.min(pixel_array)) / 
                                  (np.max(pixel_array) - np.min(pixel_array) + 1e-10) * 255).astype(np.uint8)

            else:
                # For MRIs, standard normalization is usually fine
                # Apply min-max scaling to 0-255 range
                min_val = np.min(pixel_array)
                max_val = np.max(pixel_array)
                if max_val > min_val:
                    pixel_array = ((pixel_array - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                else:
                    pixel_array = np.zeros_like(pixel_array)
            
            plt.figure(figsize=(10, 10))
            plt.imshow(pixel_array, cmap='gray', vmin=0, vmax=255)
            plt.axis('off')
            
            # Add zero padding to make it square
            plt.gca().set_aspect('equal')
            plt.tight_layout()
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            
            # Save to memory buffer
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0)
            plt.close()
            img_buf.seek(0)
            
            return send_file(img_buf, mimetype='image/png')
            
        except Exception as e:
            app.logger.error(f"Error loading image: {str(e)}")
            # Return placeholder for error
            return send_file('static/images/image_error.png', mimetype='image/png')

    @app.route('/patient_landmarks/<patient_id>')
    @login_required
    def patient_landmarks(patient_id):
        """Get landmark data for a specific patient"""
        from flask import jsonify
        import os
        import json
        
        try:
            # Path to landmark file
            landmark_file = os.path.join('landmarks', f'{patient_id}.json')
            
            if os.path.exists(landmark_file):
                with open(landmark_file, 'r') as f:
                    data = json.load(f)
                    return jsonify(data['imaging_data'])
            else:
                return jsonify({"error": "No landmark data available for this patient"}), 404
                
        except Exception as e:
            app.logger.error(f"Error loading landmark data: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/surgical_recommendation/<patient_id>')
    @login_required
    def get_surgical_recommendation(patient_id):
        """Get surgical recommendation for a patient"""
        try:
            # Get absolute path to recommendations folder
            base_dir = os.path.dirname(os.path.abspath(__file__))
            recommendation_file = os.path.join(base_dir, 'recommendations', f'{patient_id}.json')
            
            if not os.path.exists(recommendation_file):
                app.logger.error(f"Recommendation file not found: {recommendation_file}")
                return jsonify({"error": "Recommendation not found"}), 404
                
            with open(recommendation_file, 'r') as f:
                data = json.load(f)
                return jsonify(data)
                
        except Exception as e:
            app.logger.error(f"Error loading recommendation for {patient_id}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/predict_outcome/<patient_id>', methods=['POST'])
    @login_required
    def predict_outcome(patient_id):
        """Get predicted outcome based on surgical plan"""
        try:
            # Get surgery plan from request
            surgery_plan = request.json
            
            # In the future, this would use the surgery_plan to generate predictions
            # For now, load static predictions from file
            prediction_file = os.path.join('predictions', f'{patient_id}.json')
            with open(prediction_file, 'r') as f:
                data = json.load(f)
            return jsonify(data['predicted_outcome'])
        except Exception as e:
            app.logger.error(f"Error loading prediction: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/predict/<patient_id>')
    @login_required
    def prediction_interface(patient_id):
        """Show prediction interface for a patient"""
        patient = get_patient_by_id(patient_id)
        if patient:
            return render_template('prediction_interface.html', patient=patient)
        return "Patient not found", 404