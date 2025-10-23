# backend/app.py - 最終完成版 (ステートレスPDF対応)
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os
# models_mbti.py はもう回答保存に使わないが、エラー回避のため一旦残す
from models_mbti import save_response, get_all_responses
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

# --- 診断ロジック (変更なし) ---
def calculate_creator_personality_advanced(answers, questions_data, logic_data):
    scores = {"Openness": 0, "Conscientiousness": 0, "Extraversion": 0, "Agreeableness": 0, "StressTolerance": 0, "InformationStyle": 0, "DecisionMaking": 0, "MotivationSource": 0, "ValuePursuit": 0, "WorkStyle": 0}
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]; dimension, score = question['dimension'], answer - 3
        scores[dimension] += score if question['direction'] == '+' else -score
    matched_cores = []
    for core_rule in logic_data['main_cores']:
        is_match = True
        if 'all' in core_rule['conditions']:
            for condition in core_rule['conditions']['all']:
                dim, op, val = condition['dimension'], condition['operator'], condition['value']
                if op == '>' and not scores[dim] > val: is_match = False; break
                if op == '<' and not scores[dim] < val: is_match = False; break
        if is_match: matched_cores.append(core_rule)
    if matched_cores:
        matched_cores.sort(key=lambda x: x['priority'], reverse=True)
        main_core = matched_cores[0]['type']
    else: main_core = logic_data['fallback_main_core']
    sub_core_scores = {sub_core: sum(scores[dim] * weight for dim, weight in details['scores'].items()) for sub_core, details in logic_data['sub_cores'].items()}
    sub_core = max(sub_core_scores, key=sub_core_scores.get)
    return main_core, sub_core, scores

# --- APIエンドポイント ---
@app.route('/api/questions', methods=['GET'])
def get_questions(): return jsonify(QUESTIONS_DATA)

@app.route('/api/start', methods=['POST'])
def start_test(): return jsonify({'user_id': str(uuid.uuid4()), 'started_at': datetime.now().isoformat()})

@app.route('/api/submit', methods=['POST'])
def submit_answers():
    data = request.json
    user_id, answers = data.get('user_id'), data.get('answers')
    if not all([user_id, answers, len(answers) == 20]): return jsonify({'error': '無効なデータ'}), 400
    
    main_core, sub_core, scores = calculate_creator_personality_advanced(answers, QUESTIONS_DATA, TYPE_LOGIC)
    analysis_data = ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {})
    
    # app.pyから直接メインコア名を取得 (jsonからではなく)
    main_core_name = analysis_data.get("name", main_core) # analysis_patterns.jsonにnameキーを追加することを想定
    if not analysis_data:
        # 60パターンJSONにない場合のフォールバック
        main_core_name = main_core
        analysis_data = {
            "sub_core_title": sub_core,
            "focus_on": "詳細な分析結果は現在準備中です。",
            "let_go_of": "詳細な分析結果は現在準備中です。",
            "synthesis": "詳細な分析結果は現在準備中です。"
        }
    else:
        main_core_name = ANALYSIS_PATTERNS[main_core][sub_core].get("name", main_core)


    return jsonify({
        'user_id': user_id,
        'main_core_name': main_core_name,
        'sub_core_title': analysis_data.get("sub_core_title", sub_core),
        'focus_on': analysis_data.get("focus_on"),
        'let_go_of': analysis_data.get("let_go_of"),
        'synthesis': analysis_data.get("synthesis"),
        'radar_scores': {k: round(((v + 4) / 8) * 10, 1) for k, v in scores.items()},
        'completed_at': datetime.now().isoformat()
    })

# ★★★ 変更点：新しいPDF生成エンドポイント ★★★
@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    result_data = request.json
    if not result_data:
        return jsonify({'error': 'PDF生成用のデータがありません'}), 400
    
    # PDF生成に必要なデータを再構成
    pdf_data = {
        'type_name': f"{result_data.get('sub_core_title')} {result_data.get('main_core_name')}",
        'focus_on': result_data.get('focus_on'),
        'let_go_of': result_data.get('let_go_of'),
        'synthesis': result_data.get('synthesis'),
        'radar_scores': result_data.get('radar_scores'), # 正規化後のスコアをそのまま使用
    }

    pdf_buffer = generate_pdf_report_final("report", pdf_data)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='creator_core_report.pdf'
    )

@app.route('/api/health', methods=['GET'])
def health_check(): return jsonify({'status': 'ok'})

if __name__ == '__main__': app.run(debug=True, port=5000)