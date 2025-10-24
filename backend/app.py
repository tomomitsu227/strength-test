# backend/app.py - 新しいtype_logic.jsonに完全対応した最終版

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
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

# --- 診断ロジック ---
def calculate_creator_personality_final(answers, questions_data, logic_data):
    # 1. ビッグファイブ5次元の生スコアを計算 (-8 〜 +8 の範囲)
    big_five_raw = {
        "Openness": 0, "Conscientiousness": 0, "Extraversion": 0,
        "Agreeableness": 0, "Neuroticism": 0
    }
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]
        dimension = question['dimension']
        score = answer - 3 # -2 〜 +2
        if question['direction'] == '+':
            big_five_raw[dimension] += score
        else:
            big_five_raw[dimension] -= score

    # 2. レーダーチャート用の7次元スコアを計算 (0-10スケール)
    def normalize_score(raw_score, min_val=-8, max_val=8):
        raw_score = max(min_val, min(raw_score, max_val))
        return ((raw_score - min_val) / (max_val - min_val)) * 10

    radar_scores = {
        "独創性": normalize_score(big_five_raw["Openness"]),
        "計画性": normalize_score(big_five_raw["Conscientiousness"]),
        "社交性": normalize_score(big_five_raw["Extraversion"]),
        "共感力": normalize_score(big_five_raw["Agreeableness"]),
        "精神的安定性": normalize_score(-big_five_raw["Neuroticism"]),
        "創作スタイル": normalize_score(big_five_raw["Openness"] - big_five_raw["Conscientiousness"]),
        "協働適性": normalize_score(big_five_raw["Extraversion"] + big_five_raw["Agreeableness"])
    }

    # 3. メインコアタイプの判定（7次元スコアでコサイン類似度を計算）
    radar_dimension_order = list(logic_data["radar_dimensions"].keys())
    user_vector = np.array([radar_scores[dim] for dim in radar_dimension_order]).reshape(1, -1)

    similarity_scores = {}
    for core_type, core_data in logic_data['main_core_profiles'].items():
        ideal_scores = core_data.get('ideal_scores', {})
        ideal_vector = np.array([ideal_scores.get(dim, 5.0) for dim in radar_dimension_order]).reshape(1, -1)
        similarity = cosine_similarity(user_vector, ideal_vector)[0][0]
        similarity_scores[core_type] = similarity

    main_core = max(similarity_scores, key=similarity_scores.get) if similarity_scores else logic_data.get("fallback_main_core", "Practical Entertainer")

    # 4. サブコアの判定（条件式を評価）
    sub_core = "The Planner"
    # サブコアの条件を評価するためのスコープ
    eval_scope = radar_scores.copy()
    
    # 優先順位をつけるため、キーのリストを定義 (必要に応じて変更)
    sub_core_priority = ["The Deep-Diver", "The Accelerator", "The Analyst", "The Planner", "The Harmonizer"]
    
    found_sub_core = False
    for core_name in sub_core_priority:
        details = logic_data.get("sub_cores", {}).get(core_name)
        if not details: continue
        
        condition = details.get("condition")
        if condition:
            try:
                # ANDで条件を分割してすべて満たすかチェック
                all_conditions_met = True
                for part_condition in condition.split('AND'):
                    part_condition = part_condition.strip()
                    # evalを安全に使うために、スコープを限定する
                    if not eval(part_condition, {"__builtins__": None}, eval_scope):
                        all_conditions_met = False
                        break
                
                if all_conditions_met:
                    sub_core = core_name
                    found_sub_core = True
                    break
            except Exception:
                continue
    # もしどの条件にも一致しなかった場合、デフォルトのHarmonizerにするなどルールを決めても良い
    if not found_sub_core:
        sub_core = "The Harmonizer"


    return main_core, sub_core, radar_scores, big_five_raw, similarity_scores

# (APIエンドポイント部分は変更なし)
@app.route('/api/questions', methods=['GET'])
def get_questions():
    return jsonify(QUESTIONS_DATA)
@app.route('/api/start', methods=['POST'])
def start_test():
    return jsonify({'user_id': str(uuid.uuid4()), 'started_at': datetime.now().isoformat()})
@app.route('/api/submit', methods=['POST'])
def submit_answers():
    try:
        data = request.json
        user_id, answers = data.get('user_id'), data.get('answers')
        if not all([user_id, answers, len(answers) == 20]):
            return jsonify({'error': '無効なデータです'}), 400
        main_core, sub_core, radar_scores, _, _ = calculate_creator_personality_final(answers, QUESTIONS_DATA, TYPE_LOGIC)
        analysis_data = ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {})
        response = {
            'user_id': user_id,
            'main_core_name': ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core),
            'sub_core_title': analysis_data.get("sub_core_title", sub_core),
            'suited_for': analysis_data.get("suited_for", ""),
            'not_suited_for': analysis_data.get("not_suited_for", ""),
            'synthesis': analysis_data.get("synthesis", ""),
            'radar_scores': {k: round(v, 1) for k, v in radar_scores.items()},
            'completed_at': datetime.now().isoformat()
        }
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error in /api/submit: {e}")
        return jsonify({'error': 'サーバー内部でエラーが発生しました。'}), 500
@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    result_data = request.json
    if not result_data: return jsonify({'error': 'PDF生成用のデータがありません'}), 400
    try:
        pdf_buffer = generate_pdf_report_final("report", result_data)
        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='creator_core_report.pdf')
    except Exception as e:
        app.logger.error(f"PDF generation failed: {e}")
        return jsonify({'error': f'PDF生成中にエラーが発生しました: {str(e)}'}), 500
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})
if __name__ == '__main__':
    app.run(debug=True, port=5000)