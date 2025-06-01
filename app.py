# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import numpy as np
import pandas as pd
from werkzeug.utils import secure_filename
import os
import csv
import io


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# def normalize_matrix(matrix, criteria_types):
#     norm_matrix = np.zeros_like(matrix, dtype=float)
#     for j in range(matrix.shape[1]):
#         if criteria_types[j] == 'benefit':
#             norm_matrix[:, j] = matrix[:, j] / np.max(matrix[:, j])
#         else:
#             norm_matrix[:, j] = np.min(matrix[:, j]) / matrix[:, j]
#     return norm_matrix

# def calculate_saw_score(norm_matrix, weights):
#     return np.dot(norm_matrix, weights)

# def normalize_direct_relation_matrix(matrix):
#     max_row_sum = np.max(np.sum(matrix, axis=1))
#     return matrix / max_row_sum

# def total_relation_matrix(Y):
#     I = np.identity(Y.shape[0])
#     return np.dot(Y, np.linalg.inv(I - Y))

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


import subprocess as sp

@app.route('/read-excel', methods=['GET', 'POST'])
def phpexample():
    out = sp.run(["php", "excelreader.php"], stdout=sp.PIPE)
    return out.stdout



#saw
# Define your criteria info somewhere accessible
CRITERIA = [
    {'kode': 'C1', 'nama': 'IPS', 'tipe': 'Benefit', 'bobot': 0.15},
    {'kode': 'C2', 'nama': 'Aktif Kemahasiswaan', 'tipe': 'Benefit', 'bobot': 0.10},
    {'kode': 'C3', 'nama': 'Kondisi Ekonomi', 'tipe': 'Cost', 'bobot': 0.35},
    {'kode': 'C4', 'nama': 'Semester Atas', 'tipe': 'Benefit', 'bobot': 0.05},
    {'kode': 'C5', 'nama': 'Berprestasi', 'tipe': 'Benefit', 'bobot': 0.15},
    {'kode': 'C6', 'nama': 'Motivasi', 'tipe': 'Benefit', 'bobot': 0.20},
]

def normalize(matrix, types):
    # matrix: list of list of float (rows: alternatives, cols: criteria)
    # types: list of 'Benefit' or 'Cost'
    normalized = []
    matrix_T = list(zip(*matrix))  # transpose to work column-wise

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
    
    return list(map(list, zip(*normalized)))  # transpose back

def calculate_saw(matrix, weights, types):
    normalized = normalize(matrix, types)
    results = []
    for row in normalized:
        score = sum(w * r for w, r in zip(weights, row))
        results.append(score)
    return results, normalized

@app.route('/saw', methods=['GET', 'POST'])
def saw():
    results = None
    normalized_matrix = None
    alternatives = []
    errors = []
    
    if request.method == 'POST':
        # Handle CSV upload
        if 'csv_file' in request.files and request.files['csv_file'].filename != '':
            csv_file = request.files['csv_file']
            try:
                stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
                reader = csv.reader(stream)
                header = next(reader)
                
                # Expecting header: Alternatif, IPS, Aktif Kemahasiswaan, Ekonomi, Semester, Prestasi, Motivasi
                alternatives = []
                matrix = []
                for row in reader:
                    alternatives.append(row[0])
                    # Convert criteria values to float
                    matrix.append([float(x) for x in row[1:]])
            except Exception as e:
                errors.append("Error reading CSV file: " + str(e))
        else:
            # Manual input parsing
            # Number of alternatives
            alt_count = int(request.form.get('alt_count', 0))
            alternatives = []
            matrix = []
            for i in range(alt_count):
                alt_name = request.form.get(f'alt_name_{i}', '').strip()
                if alt_name == '':
                    alt_name = f'A{i+1}'
                alternatives.append(alt_name)
                row = []
                for j in range(len(CRITERIA)):
                    val_str = request.form.get(f'value_{i}_{j}', '0').strip()
                    try:
                        val = float(val_str)
                    except:
                        val = 0
                    row.append(val)
                matrix.append(row)

        # If matrix and alternatives loaded
        if alternatives and matrix:
            weights = [c['bobot'] for c in CRITERIA]
            types = [c['tipe'] for c in CRITERIA]
            try:
                results, normalized_matrix = calculate_saw(matrix, weights, types)
                # Sort alternatives by descending score
                ranked = sorted(zip(alternatives, results), key=lambda x: x[1], reverse=True)
            except Exception as e:
                errors.append("Error calculating SAW: " + str(e))
        else:
            errors.append("No input data provided.")

        if errors:
            flash(' '.join(errors), 'error')
    else:
        # Default manual alternatives to display initially (your example data)
        alternatives = ['A1', 'A2', 'A3', 'A4', 'A5']
        matrix = [
            [3.8, 4, 2, 7, 4, 5],
            [3.5, 5, 1, 6, 5, 4],
            [3.2, 3, 3, 5, 3, 4],
            [3.9, 2, 4, 4, 4, 5],
            [3.6, 3, 2, 7, 5, 3],
        ]
        weights = [c['bobot'] for c in CRITERIA]
        types = [c['tipe'] for c in CRITERIA]
        results, normalized_matrix = calculate_saw(matrix, weights, types)
        ranked = sorted(zip(alternatives, results), key=lambda x: x[1], reverse=True)

    return render_template('saw.html', criteria=CRITERIA, alternatives=alternatives, matrix=matrix if 'matrix' in locals() else None,
                           normalized=normalized_matrix, results=results, ranked=ranked if 'ranked' in locals() else None)






if __name__ == '__main__':
    app.run(debug=True)
