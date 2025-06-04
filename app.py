from flask import Flask, render_template, request, flash, session 
import os

app = Flask(__name__)
app.secret_key = 'secret-key' 

# Daftar kriteria dengan bobot dan tipe
default_criteria = [
    {'kode': 'C1', 'nama': 'IPS', 'tipe': 'Benefit', 'bobot': 0.15},
    {'kode': 'C2', 'nama': 'Aktif Kemahasiswaan', 'tipe': 'Benefit', 'bobot': 0.10},
    {'kode': 'C3', 'nama': 'Kondisi Ekonomi', 'tipe': 'Cost', 'bobot': 0.35},
    {'kode': 'C4', 'nama': 'Semester', 'tipe': 'Benefit', 'bobot': 0.05},
    {'kode': 'C5', 'nama': 'Berprestasi', 'tipe': 'Benefit', 'bobot': 0.15},
    {'kode': 'C6', 'nama': 'Motivasi', 'tipe': 'Benefit', 'bobot': 0.20},
]






# @app.route('/submit-criteria', methods=['POST'])
# def submit_criteria():
#     data = request.get_json()
#     criteria = data.get('criteria', [])
#     print("Data kriteria diterima:", criteria)

#     # Lakukan sesuatu dengan data, misalnya simpan ke database
#     return jsonify({'message': 'Kriteria berhasil diterima!', 'jumlah': len(criteria)})

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

# @app.route('/logout')
# def logout():
#     session.clear()  # Hapus semua session, atau bisa juga session.pop('criteria', None)
#     return render_template('home.html')# Ganti 'login' sesuai nama route login kamu

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
    # criteria = session.get('criteria', []) 
    

    if 'criteria' not in session:
        session['criteria'] = default_criteria.copy()

    criteria = session['criteria']

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'criteria':
            submitted_criteria = [] # Tampung kriteria baru dari form
            criteria_count_str = request.form.get('criteria_count_input') # Anda perlu field ini di form kriteria
            if not criteria_count_str:
                flash("Jumlah kriteria tidak terkirim.", "error")
                return render_template('saw.html',
                           criteria=criteria,
                           alternatives=alternatives,
                           matrix=matrix,
                           normalized_matrix=normalized_matrix,
                           weighted_matrix=weighted_matrix,
                           scores=scores,
                           ranked=ranked) 
                           # Render ulang dengan kriteria saat ini

            try:
                criteria_count = int(criteria_count_str)
            except ValueError:
                flash("Jumlah kriteria tidak valid.", "error")
                return render_template('saw.html',
                           criteria=criteria,
                           alternatives=alternatives,
                           matrix=matrix,
                           normalized_matrix=normalized_matrix,
                           weighted_matrix=weighted_matrix,
                           scores=scores,
                           ranked=ranked)

            total_bobot = 0
            for i in range(criteria_count):
                name = request.form.get(f'criteria_name_{i}', '').strip()
                bobot_str = request.form.get(f'criteria_weight_{i}', '0')
                tipe = request.form.get(f'criteria_type_{i}', 'Benefit').strip() # Perhatikan 'criteria_type_i' bukan 'tipe'

                if not name:
                    errors.append(f"Kriteria harus diisi.")
                    # name = f'K{i+10}' # Default name jika kosong
                if not bobot_str:
                    errors.append(f"Bobot untuk kriteria '{name or f'ke-{i+1}'}' harus diisi.")
                if not tipe:
                    errors.append(f"Tipe untuk kriteria '{name or f'ke-{i+1}'}' harus dipilih.")
                try:
                    bobot = float(bobot_str)
                    if not (0 <= bobot <= 1):
                        errors.append(f"Bobot untuk {name} harus antara 0 dan 1.")
                    total_bobot += bobot
                except ValueError:
                    bobot = 0
                    errors.append(f"Bobot untuk {name} tidak valid.")
                submitted_criteria.append({'kode': f'CC{i+1}', 'nama': name, 'bobot': bobot, 'tipe': tipe})

            if abs(total_bobot - 1.0) > 0.001 and submitted_criteria: # Toleransi kecil
                 errors.append(f"Total bobot kriteria ({total_bobot}) harus sama dengan 1.")

            if errors:
                flash(' '.join(errors), 'error')
                # Tetap gunakan submitted_criteria agar user bisa koreksi, jangan revert ke session lama
                criteria = submitted_criteria
            else:
                criteria = submitted_criteria # Gunakan kriteria baru yg disubmit
                session['criteria'] = criteria # Simpan ke session
                flash('Kriteria berhasil disubmit!', 'success')
            # Setelah submit kriteria, biasanya kita ingin user lanjut isi alternatif
            # Jadi, render template dengan kriteria yang baru disubmit
            return render_template('saw.html',
                           criteria=criteria,
                           alternatives=alternatives,
                           matrix=matrix,
                           normalized_matrix=normalized_matrix,
                           weighted_matrix=weighted_matrix,
                           scores=scores,
                           ranked=ranked)



        elif form_type == 'saw':
    # Ambil 'criteria' dari session di awal fungsi 'saw()'
            if not criteria:
                errors.append("Kriteria belum ada. Silakan input kriteria dulu.")
            else:
                alt_count_str = request.form.get('alt_count', '0')
                try:
                    alt_count = int(alt_count_str)
                    if alt_count <= 0:
                        errors.append("Jumlah alternatif harus lebih dari 0.")
                except ValueError:
                    errors.append("Jumlah alternatif tidak valid.")
                    alt_count = 0 # Set ke 0 jika tidak valid

                if not errors: # Lanjutkan hanya jika tidak ada error dasar seperti jumlah alternatif
                    for i in range(alt_count):
                        alt_name = request.form.get(f'alt_name_{i}', '').strip()
                        if not alt_name:
                            alt_name = f'A{i+1}'
                        alternatives.append(alt_name)
                        row = []
                        for j in range(len(criteria)):
                            val_str = request.form.get(f'value_{i}_{j}', '0').strip()
                            try:
                                val = float(val_str)
                                if val < 0: # Asumsi nilai tidak boleh negatif
                                    errors.append(f"Nilai untuk {alt_name} - {criteria[j]['nama']} tidak boleh negatif.")
                                    val = 0 # Atau handle error lebih lanjut
                            except ValueError:
                                val = 0
                                errors.append(f"Nilai untuk {alt_name} - {criteria[j]['nama']} tidak valid.")
                            row.append(val)
                        matrix.append(row)

                    if not alternatives or not matrix:
                        errors.append("Data alternatif atau matrix tidak lengkap/kosong.")

                # Pindahkan kalkulasi SAW ke luar blok error input, tapi setelah input dibaca
                if not errors and alternatives and matrix and criteria: # Pastikan semua ada dan tidak ada error sebelumnya
                    weights = [c['bobot'] for c in criteria]
                    types = [c['tipe'] for c in criteria]
                    try:
                        scores, normalized_matrix, weighted_matrix = calculate_saw(matrix, weights, types)
                        ranked = sorted(zip(alternatives, scores), key=lambda x: x[1], reverse=True)
                    except Exception as e:
                        errors.append("Error dalam perhitungan SAW: " + str(e))
                elif not errors: # Jika tidak ada error input, tapi salah satu dari alternatives, matrix, criteria kosong
                    errors.append("Data input tidak lengkap untuk perhitungan SAW.")

            if errors:
                flash(' '.join(errors), 'error')
            # Jangan ada pass di sini, biarkan flow ke return render_template
        # ...
    
    return render_template('saw.html',
                           criteria=criteria,
                           alternatives=alternatives,
                           matrix=matrix,
                           normalized_matrix=normalized_matrix,
                           weighted_matrix=weighted_matrix,
                           scores=scores,
                           ranked=ranked)

if __name__ == '__main__':
    app.run(debug=True)
