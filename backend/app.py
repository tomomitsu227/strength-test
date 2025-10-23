# backend/app.py - 最終完成版 (データ分析機能搭載)
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os
import numpy as np # データ分析のためにnumpyをインポート
from pdf_generator_final import generate_pdf_report_final

app = Flask(__name__)
CORS(app)

# --- ファイルパスの定義 (変更なし) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'questions.json')
TYPE_LOGIC_PATH = os.path.join(BASE_DIR, '..', 'data', 'type_logic.json')
ANALYSIS_PATTERNS_PATH = os.path.join(BASE_DIR, '..', 'data', 'analysis_patterns.json')

# --- 設定ファイルの読み込み (変更なし) ---
try:
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        QUESTIONS_DATA = json.load(f)
    with open(TYPE_LOGIC_PATH, 'r', encoding='utf-8') as f:
        TYPE_LOGIC = json.load(f)
    with open(ANALYSIS_PATTERNS_PATH, 'r', encoding='utf-8') as f:
        ANALYSIS_PATTERNS = json.load(f)
except Exception as e:
    print(f"設定ファイルの読み込み中にエラーが発生しました: {e}"); exit()

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
    
    # ★★★ 追加：データ分析ロジック ★★★
    # 1. 回答の極端さスコア (0-100)
    extreme_answers = sum(1 for ans in answers if ans == 1 or ans == 5)
    extremeness_score = (extreme_answers / 20) * 100
    if extremeness_score >= 75:
        extremeness_comment = "あなたは、自分の考えやスタイルが非常に明確で、白黒はっきりさせる傾向があります。この「尖った」姿勢が、熱狂的なファンを生む一方で、時には敵を作る可能性も秘めています。"
    elif extremeness_score >= 50:
        extremeness_comment = "あなたは、多くの事柄に対して自分の意見をしっかり持っているタイプです。その明確なスタンスが、あなたのクリエイターとしての個性や「色」に繋がっています。"
    else:
        extremeness_comment = "あなたは、物事を多角的に捉え、バランスの取れた判断をする傾向があります。その柔軟性は、多くの人に受け入れられやすい一方で、強い個性を出しにくい側面もあるかもしれません。"

    # 2. ビッグファイブの特異性分析
    bf_scores = {
        "開放性": scores['Openness'],
        "誠実性": scores['Conscientiousness'],
        "外向性": scores['Extraversion'],
        "協調性": scores['Agreeableness'],
        "ストレス耐性": scores['StressTolerance']
    }
    # 平均(0)からの距離（絶対値）で特異性を評価
    deviations = {k: abs(v) for k, v in bf_scores.items()}
    most_unique_trait = max(deviations, key=deviations.get)
    uniqueness_comment = f"あなたのビッグファイブ特性の中で、平均的な傾向から最も大きく離れているのは「{most_unique_trait}」です。これは、あなたのパーソナリティを特徴づける最もユニークな才能であり、他の人にはない強力な武器となる可能性を秘めています。"
    
    return jsonify({
        'user_id': user_id,
        'main_core_name': ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core),
        'sub_core_title': analysis_data.get("sub_core_title", sub_core),
        'suited_for': analysis_data.get("suited_for"),
        'not_suited_for': analysis_data.get("not_suited_for"),
        'synthesis': analysis_data.get("synthesis"),
        'radar_scores': {k: round(((v + 4) / 8) * 10, 1) for k, v in scores.items()},
        # ★★★ 追加：データ分析結果 ★★★
        'data_analysis': {
            'extremeness_score': round(extremeness_score),
            'extremeness_comment': extremeness_comment,
            'most_unique_trait': most_unique_trait,
            'uniqueness_comment': uniqueness_comment
        },
        'completed_at': datetime.now().isoformat()
    })

# PDF機能はデータ分析結果に未対応のため、一旦そのまま
@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf():
    result_data = request.json
    if not result_data: return jsonify({'error': 'PDF生成用のデータがありません'}), 400
    pdf_data = {
        'main_core_name': result_data.get('main_core_name'), 'sub_core_title': result_data.get('sub_core_title'),
        'suited_for': result_data.get('suited_for'), 'not_suited_for': result_data.get('not_suited_for'),
        'synthesis': result_data.get('synthesis'), 'radar_scores': result_data.get('radar_scores'),
    }
    pdf_buffer = generate_pdf_report_final("report", pdf_data)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='creator_core_report.pdf')

@app.route('/api/health', methods=['GET'])
def health_check(): return jsonify({'status': 'ok'})

if __name__ == '__main__': app.run(debug=True, port=5000)