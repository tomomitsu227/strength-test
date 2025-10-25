from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
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
TRAIT_DEFINITIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'trait_definitions.json')

# --- 設定ファイルの読み込み ---
try:
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        QUESTIONS_DATA = json.load(f)
    with open(TYPE_LOGIC_PATH, 'r', encoding='utf-8') as f:
        TYPE_LOGIC = json.load(f)
    with open(ANALYSIS_PATTERNS_PATH, 'r', encoding='utf-8') as f:
        ANALYSIS_PATTERNS = json.load(f)
    with open(TRAIT_DEFINITIONS_PATH, 'r', encoding='utf-8') as f:
        TRAIT_DEFINITIONS = json.load(f)
except Exception as e:
    print(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
    exit()

# --- 診断ロジック ---
def calculate_creator_personality_final(answers, questions_data, logic_data):
    big_five_raw = { "Openness": 0, "Conscientiousness": 0, "Extraversion": 0, "Agreeableness": 0, "Neuroticism": 0 }
    
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]
        score = answer - 3
        if question['direction'] == '+':
            big_five_raw[question['dimension']] += score
        else:
            big_five_raw[question['dimension']] -= score
    
    def normalize_score(raw_score, min_val=-8, max_val=8):
        return ((raw_score - min_val) / (max_val - min_val)) * 10
    
    seven_dimensions = {
        "独創性": normalize_score(big_five_raw["Openness"]),
        "計画性": normalize_score(big_five_raw["Conscientiousness"]),
        "社交性": normalize_score(big_five_raw["Extraversion"]),
        "共感力": normalize_score(big_five_raw["Agreeableness"]), 
        "精神的安定性": normalize_score(-big_five_raw["Neuroticism"]),
        "創作スタイル": normalize_score((big_five_raw["Openness"] - big_five_raw["Conscientiousness"]) / 2),
        "協働適性": normalize_score((big_five_raw["Extraversion"] + big_five_raw["Agreeableness"]) / 2)
    }
    
    dimension_order = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
    user_vector = np.array([big_five_raw[dim] for dim in dimension_order])
    
    similarity_scores = {}
    if 'main_core_profiles' in logic_data:
        for core_type, core_data in logic_data['main_core_profiles'].items():
            ideal_vector_list = [core_data['ideal_scores'].get(dim, 0) for dim in dimension_order]
            ideal_vector = np.array(ideal_vector_list)
            similarity = cosine_similarity(user_vector.reshape(1, -1), ideal_vector.reshape(1, -1))[0][0]
            similarity_scores[core_type] = similarity
    
    main_core = max(similarity_scores, key=similarity_scores.get) if similarity_scores else 'Practical Entertainer'
    
    sub_core_scores = {}
    sub_core = "The Planner"
    if 'sub_cores' in logic_data and isinstance(logic_data['sub_cores'], dict):
        for sub_core_name, details in logic_data['sub_cores'].items():
            score_sum = 0
            scores_dict = details.get('scores', {})
            if isinstance(scores_dict, dict):
                for dim, weight in scores_dict.items():
                    if dim in big_five_raw:
                        score_sum += big_five_raw[dim] * weight
            sub_core_scores[sub_core_name] = score_sum
    if sub_core_scores:
        sub_core = max(sub_core_scores, key=sub_core_scores.get)

    return main_core, sub_core, seven_dimensions

# --- 分析結果生成ロジック ---
def generate_dynamic_analysis(main_core, sub_core, seven_dimensions, definitions):
    # 箇条書きリスト生成ロジックの改善
    base_traits = ["独創性", "計画性", "社交性", "共感力", "精神的安定性"]
    sorted_scores = sorted(seven_dimensions.items(), key=lambda item: abs(item[1] - 5), reverse=True)

    high_scores = sorted([item for item in sorted_scores if item[0] in base_traits and item[1] >= 5.0], key=lambda item: item[1], reverse=True)
    low_scores = sorted([item for item in sorted_scores if item[0] in base_traits and item[1] < 5.0], key=lambda item: item[1])

    suited_for_set = set()
    not_suited_for_set = set()

    tendencies = definitions["tendencies"]
    
    # 上位2つの高い特性から箇条書きを追加
    for trait, score in high_scores[:2]:
        suited_for_set.update(tendencies[trait]["high"]["suited"])
        not_suited_for_set.update(tendencies[trait]["high"]["not_suited"])
    # 上位2つの低い特性から箇条書きを追加
    for trait, score in low_scores[:2]:
        suited_for_set.update(tendencies[trait]["low"]["suited"])
        not_suited_for_set.update(tendencies[trait]["low"]["not_suited"])

    # 分析結果のまとめを生成（コピーライター視点で改善）
    templates = definitions["synthesis_templates"]
    main_core_name = ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core)
    sub_core_description = definitions["sub_core_descriptions"].get(sub_core, "")

    trait1_name, trait1_score = sorted_scores[0]
    trait2_name, trait2_score = sorted_scores[1]

    trait1_level = "high" if trait1_score >= 5 else "low"
    trait2_level = "high" if trait2_score >= 5 else "low"
    
    trait1_desc = templates["traits"][trait1_name][trait1_level]
    trait2_desc = templates["traits"][trait2_name][trait2_level]

    conclusion = templates["conclusions"].get(main_core, "個性的なクリエイター")

    synthesis = templates["base"].format(
        main_core_name=main_core_name,
        sub_core_description=sub_core_description,
        trait1_name=trait1_name,
        trait1_desc=trait1_desc,
        trait2_name=trait2_name,
        trait2_desc=trait2_desc,
        conclusion=conclusion
    )

    return list(suited_for_set), list(not_suited_for_set), synthesis

# グローバル変数でセッション管理
USER_SESSIONS = {}

# --- APIエンドポイント ---
@app.route('/api/questions', methods=['GET'])
def get_questions():
    return jsonify(QUESTIONS_DATA)

@app.route('/api/submit', methods=['POST'])
def submit_answers():
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    if not all([user_id, answers, len(answers) == 20]):
        return jsonify({'error': '無効なデータです'}), 400
    
    main_core, sub_core, seven_dimensions = calculate_creator_personality_final(answers, QUESTIONS_DATA, TYPE_LOGIC)
    suited_for, not_suited_for, synthesis = generate_dynamic_analysis(main_core, sub_core, seven_dimensions, TRAIT_DEFINITIONS)

    response = {
        'user_id': user_id,
        'main_core_name': ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core),
        'sub_core_title': ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {}).get("sub_core_title", sub_core),
        'suited_for': suited_for,
        'not_suited_for': not_suited_for,
        'synthesis': synthesis,
        'radar_scores': {k: round(v, 1) for k, v in seven_dimensions.items()},
        'completed_at': datetime.now().isoformat()
    }
    
    USER_SESSIONS[user_id] = response
    return jsonify(response)

@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    if user_id in USER_SESSIONS:
        result_data = USER_SESSIONS[user_id]
    else:
        # サーバー再起動などでセッションが消えた場合のダミーデータ
        return jsonify({'error': '診断セッションが見つかりません。もう一度診断してください。'}), 404
    
    pdf_buffer = generate_pdf_report_final("動画クリエイター特性診断レポート", result_data)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer, 
        mimetype='application/pdf', 
        as_attachment=True, 
        download_name=f'creator_core_report_{user_id}.pdf'
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)