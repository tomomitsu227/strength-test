# backend/app.py - ビッグファイブ7次元対応版（PDFエンドポイント修正済み）

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
# pdf_generator_final.py が同じディレクトリにあることを確認
from pdf_generator_final import generate_pdf_report_final

app = Flask(__name__)
CORS(app)

# --- ファイルパスの定義 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'questions.json')
TYPE_LOGIC_PATH = os.path.join(BASE_DIR, '..', 'data', 'type_logic.json')
ANALYSIS_PATTERNS_PATH = os.path.join(BASE_DIR, '..', 'data', 'analysis_patterns.json')

# --- 設定ファイルの読み込み ---
try:
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        QUESTIONS_DATA = json.load(f)
    with open(TYPE_LOGIC_PATH, 'r', encoding='utf-8') as f:
        TYPE_LOGIC = json.load(f)
    with open(ANALYSIS_PATTERNS_PATH, 'r', encoding='utf-8') as f:
        ANALYSIS_PATTERNS = json.load(f)
except Exception as e:
    print(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
    exit()

# --- 診断ロジック(ビッグファイブ7次元対応) ---
def calculate_creator_personality_bigfive(answers, questions_data, logic_data):
    # 1. ビッグファイブ5次元のスコアを計算
    big_five = {
        "Openness": 0, "Conscientiousness": 0, "Extraversion": 0,
        "Agreeableness": 0, "Neuroticism": 0
    }
    
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]
        dimension = question['dimension']
        score = answer - 3
        if question['direction'] == '+':
            big_five[dimension] += score
        else:
            big_five[dimension] -= score
    
    # 2. 7次元スコアを作成（0-10スケール）
    def normalize_score(raw_score, min_val=-8, max_val=8):
        # スコアが範囲外に出ないようにクリップ
        raw_score = max(min_val, min(raw_score, max_val))
        return ((raw_score - min_val) / (max_val - min_val)) * 10
    
    seven_dimensions = {
        "独創性": normalize_score(big_five["Openness"]),
        "計画性": normalize_score(big_five["Conscientiousness"]),
        "社交性": normalize_score(big_five["Extraversion"]),
        "共感力": normalize_score(big_five["Agreeableness"]),
        "精神的安定性": normalize_score(-big_five["Neuroticism"]),
        "創作スタイル": normalize_score((big_five["Openness"] - big_five["Conscientiousness"])),
        "協働適性": normalize_score((big_five["Extraversion"] + big_five["Agreeableness"]))
    }
    
    # 3. メインコアタイプの判定
    dimension_order = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
    user_vector = np.array([big_five[dim] for dim in dimension_order]).reshape(1, -1)
    
    similarity_scores = {}
    for core_type, core_data in logic_data['main_core_profiles'].items():
        ideal_bf = core_data.get('ideal_scores', {})
        ideal_vector = np.array([ideal_bf.get(dim, 0) for dim in dimension_order]).reshape(1, -1)
        similarity = cosine_similarity(user_vector, ideal_vector)[0][0]
        similarity_scores[core_type] = similarity
    
    main_core = max(similarity_scores, key=similarity_scores.get) if similarity_scores else 'Practical Entertainer'
    
    # 4. サブコアの判定
    sub_core_scores = {}
    for sub_core, details in logic_data['sub_cores'].items():
        score_sum = sum(big_five.get(dim, 0) * weight for dim, weight in details.get('scores', {}).items())
        sub_core_scores[sub_core] = score_sum
    
    sub_core = max(sub_core_scores, key=sub_core_scores.get) if sub_core_scores else "The Planner"
    
    return main_core, sub_core, seven_dimensions, big_five, similarity_scores

# --- APIエンドポイント ---
@app.route('/api/questions', methods=['GET'])
def get_questions():
    return jsonify(QUESTIONS_DATA)

@app.route('/api/start', methods=['POST'])
def start_test():
    return jsonify({'user_id': str(uuid.uuid4()), 'started_at': datetime.now().isoformat()})

@app.route('/api/submit', methods=['POST'])
def submit_answers():
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    if not all([user_id, answers, len(answers) == 20]):
        return jsonify({'error': '無効なデータです'}), 400
    
    main_core, sub_core, seven_dimensions, big_five, similarity_scores = \
        calculate_creator_personality_bigfive(answers, QUESTIONS_DATA, TYPE_LOGIC)
    
    analysis_data = ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {})
    
    response = {
        'user_id': user_id,
        'main_core_name': ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core),
        'sub_core_title': analysis_data.get("sub_core_title", sub_core),
        'suited_for': analysis_data.get("suited_for", ""),
        'not_suited_for': analysis_data.get("not_suited_for", ""),
        'synthesis': analysis_data.get("synthesis", ""),
        'radar_scores': {k: round(v, 1) for k, v in seven_dimensions.items()},
        'completed_at': datetime.now().isoformat()
    }
    
    if app.debug:
        response['debug_info'] = {
            'similarity_scores': {k: round(v, 3) for k, v in similarity_scores.items()},
            'top_match': sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)[:1],
            'big_five_raw': big_five
        }
    
    return jsonify(response)

# 【重要】PDFダウンロード用のエンドポイントを修正
@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    """PDF生成"""
    result_data = request.json
    
    if not result_data:
        return jsonify({'error': 'PDF生成用のデータがありません'}), 400
    
    # PDF生成用のデータを整形
    pdf_data = {
        'main_core_name': result_data.get('main_core_name'),
        'sub_core_title': result_data.get('sub_core_title'),
        'suited_for': result_data.get('suited_for'),
        'not_suited_for': result_data.get('not_suited_for'),
        'synthesis': result_data.get('synthesis'),
        'radar_scores': result_data.get('radar_scores'),
    }
    
    try:
        # pdf_generator_final.pyの関数を呼び出す
        pdf_buffer = generate_pdf_report_final("report", pdf_data)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='creator_core_report.pdf'
        )
    except Exception as e:
        # エラーログを出力
        app.logger.error(f"PDF generation failed: {e}")
        return jsonify({'error': f'PDF生成中にエラーが発生しました: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)