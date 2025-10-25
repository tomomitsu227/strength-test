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
# 新しいJSONファイルのパスを追加
TRAIT_DEFINITIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'trait_definitions.json')

# --- 設定ファイルの読み込み ---
try:
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        QUESTIONS_DATA = json.load(f)
    with open(TYPE_LOGIC_PATH, 'r', encoding='utf-8') as f:
        TYPE_LOGIC = json.load(f)
    with open(ANALYSIS_PATTERNS_PATH, 'r', encoding='utf-8') as f:
        ANALYSIS_PATTERNS = json.load(f)
    # 新しいJSONファイルを読み込む
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
    # 箇条書きリストの生成
    suited_for = []
    not_suited_for = []
    
    # 精神的安定性以外の5つの基本特性でループ
    base_traits = ["独創性", "計画性", "社交性", "共感力", "精神的安定性"]
    for trait in base_traits:
        score = seven_dimensions.get(trait, 5)
        trait_info = definitions["tendencies"].get(trait, {})
        
        if score >= 7.0 and "high" in trait_info:
            suited_for.extend(trait_info["high"].get("suited", []))
            not_suited_for.extend(trait_info["high"].get("not_suited", []))
        elif score <= 3.0 and "low" in trait_info:
            suited_for.extend(trait_info["low"].get("suited", []))
            not_suited_for.extend(trait_info["low"].get("not_suited", []))

    # 分析結果のまとめを生成
    synthesis_phrases = definitions["synthesis_phrases"]
    
    main_core_name = ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core)
    sub_core_description = definitions["sub_core_descriptions"].get(sub_core, "")
    
    intro = synthesis_phrases["intro"].format(
        main_core_name=main_core_name, 
        sub_core_description=sub_core_description
    )
    
    # 最も特徴的な特性を決定
    sorted_scores = sorted(seven_dimensions.items(), key=lambda item: abs(item[1] - 5), reverse=True)
    most_significant_trait_name = sorted_scores[0][0]
    most_significant_score = sorted_scores[0][1]
    
    level = "high" if most_significant_score >= 5 else "low"
    most_significant_trait_phrase = synthesis_phrases["traits"][most_significant_trait_name][level]

    bridge = synthesis_phrases["bridge"].format(
        most_significant_trait=most_significant_trait_phrase
    )

    # 結論部分の組み立て
    trait_parts = []
    # 上位2つの特性を文章に含める
    for trait_name, score in sorted_scores[:2]:
        level = "high" if score >= 5 else "low"
        trait_parts.append(synthesis_phrases["traits"][trait_name][level])

    synthesis_conclusion = f"{trait_parts[0]}と{trait_parts[1]}を併せ持つクリエイター"

    outro = synthesis_phrases["outro"].format(synthesis_conclusion=synthesis_conclusion)
    
    synthesis = f"{intro} {bridge} {outro}"

    return suited_for, not_suited_for, synthesis

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
    
    # 診断実行
    main_core, sub_core, seven_dimensions = calculate_creator_personality_final(answers, QUESTIONS_DATA, TYPE_LOGIC)
    
    # 動的な分析結果を生成
    suited_for, not_suited_for, synthesis = generate_dynamic_analysis(main_core, sub_core, seven_dimensions, TRAIT_DEFINITIONS)

    # レスポンスの構築
    response = {
        'user_id': user_id,
        'main_core_name': ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core),
        'sub_core_title': ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {}).get("sub_core_title", sub_core),
        'suited_for': suited_for,
        'not_suited_for': not_suited_for,
        'synthesis': synthesis,
        'radar_scores': {
            k: round(v, 1) for k, v in seven_dimensions.items()
        },
        'completed_at': datetime.now().isoformat()
    }
    
    USER_SESSIONS[user_id] = response
    return jsonify(response)

@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    if user_id in USER_SESSIONS:
        result_data = USER_SESSIONS[user_id]
    else:
        # ダミーデータ
        result_data = {
            'main_core_name': '孤高のアーティスト',
            'sub_core_title': '静かな共感の表現者',
            'suited_for': ['新しい表現方法の探求', 'オリジナリティの高い企画立案'],
            'not_suited_for': ['定型的な作業の繰り返し', '既存ルールの厳守'],
            'synthesis': 'あなたは『孤高のアーティスト』で、静かなる共感の表現者傾向があります。 斬新なアイデアを生み出す独創性を持っており、特に物事を計画通りに進める緻密さがあなたの強みです。 これらの特性を総合すると、あなたは斬新なアイデアを生み出す独創性と物事を計画通りに進める緻密さを併せ持つクリエイターと言えるでしょう。',
            'radar_scores': {'独創性': 8.5, '計画性': 7.0, '社交性': 2.5, '共感力': 5.0, '精神的安定性': 5.5, '創作スタイル': 8.0, '協働適性': 3.5}
        }
    
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