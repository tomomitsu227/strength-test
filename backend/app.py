# backend/app.py - 表示内容分離＆新フォーマット対応版
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os
from models_mbti import save_response, get_all_responses
from pdf_generator_mbti_improved import generate_pdf_report

app = Flask(__name__)
CORS(app)

# --- ファイルパスの定義 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'questions.json')
TYPE_LOGIC_PATH = os.path.join(BASE_DIR, '..', 'data', 'type_logic.json')
# ★★★ 追加：新しい詳細データファイルのパス ★★★
TYPE_DETAILS_PATH = os.path.join(BASE_DIR, '..', 'data', 'type_details.json')

# --- 設定ファイルの読み込み ---
try:
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        QUESTIONS_DATA = json.load(f)
    with open(TYPE_LOGIC_PATH, 'r', encoding='utf-8') as f:
        TYPE_LOGIC = json.load(f)
    # ★★★ 追加：新しい詳細データファイルの読み込み ★★★
    with open(TYPE_DETAILS_PATH, 'r', encoding='utf-8') as f:
        TYPE_DETAILS = json.load(f)

except FileNotFoundError as e:
    print(f"エラー: 設定ファイルが見つかりません。- {e}")
    exit()
except json.JSONDecodeError as e:
    print(f"エラー: JSONファイルの形式が正しくありません。 - {e}")
    exit()

# --- 診断タイプの詳細データ ---
# (app.py内から削除し、type_details.jsonから読み込むように変更)
SUB_CORE_DATA = {
    "The Planner": {"name": "プランナータイプ"}, "The Analyst": {"name": "アナリストタイプ"}, "The Harmonizer": {"name": "ハーモナイザータイプ"}, "The Accelerator": {"name": "アクセラレータータイプ"}, "The Deep-Diver": {"name": "ディープダイバータイプ"}
}

# --- 高精度診断ロジック (変更なし) ---
def calculate_creator_personality_advanced(answers, questions_data, logic_data):
    scores = {"Openness": 0, "Conscientiousness": 0, "Extraversion": 0, "Agreeableness": 0, "StressTolerance": 0, "InformationStyle": 0, "DecisionMaking": 0, "MotivationSource": 0, "ValuePursuit": 0, "WorkStyle": 0}
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]
        dimension, score = question['dimension'], answer - 3
        scores[dimension] += score if question['direction'] == '+' else -score
    matched_cores = []
    for core_rule in logic_data['main_cores']:
        is_match = True
        if 'all' in core_rule['conditions']:
            for condition in core_rule['conditions']['all']:
                dim, op, val = condition['dimension'], condition['operator'], condition['value']
                if op == '>' and not scores[dim] > val: is_match = False; break
                if op == '<' and not scores[dim] < val: is_match = False; break
                if op == '>=' and not scores[dim] >= val: is_match = False; break
                if op == '<=' and not scores[dim] <= val: is_match = False; break
        if is_match: matched_cores.append(core_rule)
    if matched_cores:
        matched_cores.sort(key=lambda x: x['priority'], reverse=True)
        main_core = matched_cores[0]['type']
    else:
        main_core = logic_data['fallback_main_core']
    sub_core_scores = {}
    for sub_core, details in logic_data['sub_cores'].items():
        total_score = sum(scores[dim] * weight for dim, weight in details['scores'].items())
        sub_core_scores[sub_core] = total_score
    sub_core = max(sub_core_scores, key=sub_core_scores.get)
    return main_core, sub_core, scores

# --- APIエンドポイント ---
@app.route('/api/questions', methods=['GET'])
def get_questions():
    return jsonify(QUESTIONS_DATA)

@app.route('/api/start', methods=['POST'])
def start_test():
    user_id = str(uuid.uuid4())
    return jsonify({'user_id': user_id, 'started_at': datetime.now().isoformat()})

@app.route('/api/submit', methods=['POST'])
def submit_answers():
    data = request.json
    user_id, answers = data.get('user_id'), data.get('answers')
    if not all([user_id, answers, len(answers) == 20]):
        return jsonify({'error': '無効なデータ'}), 400
    
    save_response(user_id, answers)
    
    main_core, sub_core, scores = calculate_creator_personality_advanced(answers, QUESTIONS_DATA, TYPE_LOGIC)
    
    main_core_details = TYPE_DETAILS[main_core]
    sub_core_info = SUB_CORE_DATA[sub_core]
    
    # ★★★ 変更点：フロントに返すJSONの構造を新しいフォーマットに変更 ★★★
    return jsonify({
        'user_id': user_id,
        'type_name': f"{main_core_details['name']} - {sub_core_info['name']}",
        'icon': main_core_details['icon'],
        'description': main_core_details['description'],
        'focus_on': main_core_details['focus_on'],
        'let_go_of': main_core_details['let_go_of'],
        'synthesis': main_core_details['synthesis'],
        'radar_scores': {k: round(((v + 4) / 8) * 10, 1) for k, v in scores.items()},
        'completed_at': datetime.now().isoformat()
    })

# PDF生成は現在新しいフォーマットに対応していませんが、エラーが出ないように残しておきます
@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    # (PDF生成は別途改修が必要なため、この部分は簡易的なまま)
    return jsonify({'message': 'PDF generation is not updated for the new format yet.'})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)