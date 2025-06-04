from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
import os
import pandas as pd
import numpy as np

app = Flask(__name__)
app.secret_key = 'secret-key' 

# Daftar kriteria dengan bobot dan tipe
criteria = [
    {'kode': 'C1', 'nama': 'IPS', 'tipe': 'Benefit', 'bobot': 0.15},
    {'kode': 'C2', 'nama': 'Aktif Kemahasiswaan', 'tipe': 'Benefit', 'bobot': 0.10},
    {'kode': 'C3', 'nama': 'Kondisi Ekonomi', 'tipe': 'Cost', 'bobot': 0.35},
    {'kode': 'C4', 'nama': 'Semester Atas', 'tipe': 'Benefit', 'bobot': 0.05},
    {'kode': 'C5', 'nama': 'Berprestasi', 'tipe': 'Benefit', 'bobot': 0.15},
    {'kode': 'C6', 'nama': 'Motivasi', 'tipe': 'Benefit', 'bobot': 0.20},
]

# Normalisai matrix berdasarkan tipe kriteria
def normalize(matrix, types):
    normalized = []
    matrix_T = list(zip(*matrix))  

    for j, col in enumerate(matrix_T):
        tipe = types[j]
        col = list(col)
        if tipe == 'Benefit':
            max_val = max(col)
            norm_col = [x / max_val if max_val != 0 else 0 for x in col]
        else:  # Cost
            min_val = min(col)
            norm_col = [min_val / x if x != 0 else 0 for x in col]
        normalized.append(norm_col)

    return list(map(list, zip(*normalized))) 

# Matriks Normalisasi x bobot kriteria 
def calculate_saw(matrix, weights, types):
    normalized = normalize(matrix, types)
    weighted_matrix = []
    scores = []
    for row in normalized:
        weighted_row = [w * r for w, r in zip(weights, row)]
        weighted_matrix.append(weighted_row)
        scores.append(sum(weighted_row))
    return scores, normalized, weighted_matrix

@app.route('/')
def home():
    return render_template('home.html')

# Inputan dari form 
@app.route('/saw', methods=['GET', 'POST'])
def saw():
    errors = []
    alternatives = []
    matrix = []
    normalized_matrix = []
    weighted_matrix = []
    scores = []
    ranked = []

    if request.method == 'POST':
        alt_count = int(request.form.get('alt_count', 0))
        for i in range(alt_count):
            alt_name = request.form.get(f'alt_name_{i}', '').strip()
            if alt_name == '':
                alt_name = f'A{i+1}'
            alternatives.append(alt_name)
            row = []
            for j in range(len(criteria)):
                val_str = request.form.get(f'value_{i}_{j}', '0').strip()
                try:
                    val = float(val_str)
                except:
                    val = 0
                row.append(val)
            matrix.append(row)

        if alternatives and matrix:
            weights = [c['bobot'] for c in criteria]
            types = [c['tipe'] for c in criteria]
            try:
                scores, normalized_matrix, weighted_matrix = calculate_saw(matrix, weights, types)
                ranked = sorted(zip(alternatives, scores), key=lambda x: x[1], reverse=True)
            except Exception as e:
                errors.append("Error dalam perhitungan SAW: " + str(e))
        else:
            errors.append("Data input tidak tersedia.")

        if errors:
            flash(' '.join(errors), 'error')

    return render_template('saw.html',
                           criteria=criteria,
                           alternatives=alternatives,
                           matrix=matrix,
                           normalized_matrix=normalized_matrix,
                           weighted_matrix=weighted_matrix,
                           scores=scores,
                           ranked=ranked)


# dematel
@app.route('/dematel', methods=['GET', 'POST'])
def dematel():
    if request.method == 'POST':
        try:
            num_criteria = int(request.json['num_criteria'])
            criteria_labels = request.json.get('criteria_labels', [])

            # Bersihkan label: gunakan default jika kosong
            criteria_labels = [label.strip() or f'Kriteria {i+1}' for i, label in enumerate(criteria_labels)]
            # Pastikan criteria_labels memiliki panjang yang benar (jika ada yang terlewat dari frontend)
            if len(criteria_labels) < num_criteria:
                for i in range(len(criteria_labels), num_criteria):
                    criteria_labels.append(f'Kriteria {i+1}')

            if num_criteria <= 1:
                return jsonify({'success': False, 'message': 'Jumlah kriteria harus lebih dari 1.'}), 400

            matrix_data = []
            for i in range(num_criteria):
                row = []
                for j in range(num_criteria):
                    val = float(request.json[f'matrix_{i}_{j}'])
                    row.append(val)
                matrix_data.append(row)

            initial_matrix = np.array(matrix_data)

            # --- Langkah-langkah Perhitungan DEMATEL ---
            max_sum = np.sum(initial_matrix, axis=1).max()
            normalized_matrix = initial_matrix / max_sum

            identity_matrix = np.identity(num_criteria)
            inv_part = np.linalg.inv(identity_matrix - normalized_matrix)
            total_relation_matrix = normalized_matrix @ inv_part

            D = np.sum(total_relation_matrix, axis=1)
            R = np.sum(total_relation_matrix, axis=0)

            prominence = D + R
            causal = D - R

            # --- Hitung Type of Identity ---
            identity_types = []
            for val in causal:
                if val > 0.0001:  # Menggunakan sedikit toleransi untuk floating point
                    identity_types.append('Influencer (Penyebab)')
                elif val < -0.0001: # Menggunakan sedikit toleransi untuk floating point
                    identity_types.append('Influenced (Akibat)')
                else:
                    identity_types.append('Neutral')

            results = {
                'initial_matrix': initial_matrix.tolist(),
                'normalized_matrix': normalized_matrix.tolist(),
                'total_relation_matrix': total_relation_matrix.tolist(),
                'prominence': prominence.tolist(),
                'causal': causal.tolist(),
                'criteria_labels': criteria_labels,
                'identity_types': identity_types # Tambahkan Type of Identity di sini
            }
            return jsonify({'success': True, 'results': results})

        except ValueError:
            return jsonify({'success': False, 'message': 'Pastikan semua input adalah angka yang valid.'}), 400
        except np.linalg.LinAlgError:
            return jsonify({'success': False, 'message': 'Matriks tidak dapat dibalik. Periksa kembali input Anda (mungkin ada dependensi linear atau nilai yang salah).'}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': f'Terjadi kesalahan tak terduga: {str(e)}'}), 500

    return render_template('dematel.html')

@app.route('/read-excel', methods=['POST'])
def phpexample():
     
    file = request.files['excel_file']

    if not file:
        return jsonify({"error": "No selected file"}), 400
    
    filename = file.filename

    if filename.endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({"error": f"Error reading Excel file: {e}"}), 500
    elif filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({"error": f"Error reading CSV file: {e}"}), 500
    else:
        return jsonify({"error": "Unsupported file format. Please upload .xlsx, .xls, or .csv"}), 400
    
    data = df.values.tolist()

    for idx1, row in enumerate(data):
        for idx2, val in enumerate(row):
            if idx2 != 0:
                try:
                    converted_val = float(val)

                    # Now, check if the converted float is NaN
                    # Use np.isnan() as it's designed for NumPy NaNs (which pandas uses)
                    if np.isnan(converted_val):
                        data[idx1][idx2] = 0.0 # Replace NaN with 0.0
                    else:
                        data[idx1][idx2] = converted_val # Keep the converted float
                except (ValueError, TypeError):
                    # This 'except' block catches:
                    # - Strings that cannot be converted to float (e.g., "hello", "N/A")
                    # - None values (float(None) raises TypeError)
                    data[idx1][idx2] = 0.0

    return jsonify(data)


    # out = sp.run(["php", "excelreader.php"], stdout=sp.PIPE)
    # return out.stdout

if __name__ == '__main__':
    app.run(debug=True)
