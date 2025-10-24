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
    # ビッグファイブの生スコアを計算
    big_five_raw = {
        "Openness": 0,
        "Conscientiousness": 0, 
        "Extraversion": 0,
        "Agreeableness": 0,
        "Neuroticism": 0
    }
    
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]
        dimension = question['dimension']
        direction = question['direction']
        
        # 1-5のスケールを-2から+2に変換
        score = answer - 3
        
        # 方向に応じてスコアを加算
        if direction == '+':
            big_five_raw[dimension] += score
        else:
            big_five_raw[dimension] -= score
    
    # 7次元スコアを計算（0-10スケール）
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
    
    # メインコアタイプの判定（コサイン類似度）
    dimension_order = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
    user_vector = np.array([big_five_raw[dim] for dim in dimension_order])
    
    similarity_scores = {}
    
    if 'main_core_profiles' in logic_data:
        for core_type, core_data in logic_data['main_core_profiles'].items():
            ideal_bf = {
                "Openness": core_data['ideal_scores'].get('Openness', 0),
                "Conscientiousness": core_data['ideal_scores'].get('Conscientiousness', 0),
                "Extraversion": core_data['ideal_scores'].get('Extraversion', 0),
                "Agreeableness": core_data['ideal_scores'].get('Agreeableness', 0),
                "Neuroticism": core_data['ideal_scores'].get('Neuroticism', 0)
            }
            ideal_vector = np.array([ideal_bf[dim] for dim in dimension_order])
            
            similarity = cosine_similarity(
                user_vector.reshape(1, -1),
                ideal_vector.reshape(1, -1)
            )[0][0]
            similarity_scores[core_type] = similarity
    
    main_core = max(similarity_scores, key=similarity_scores.get) if similarity_scores else 'Practical Entertainer'
    
    # サブコアの判定
    sub_core_scores = {}
    sub_core = "The Planner"  # デフォルト値を先に設定

    if 'sub_cores' in logic_data and isinstance(logic_data['sub_cores'], dict):
        for sub_core_name, details in logic_data['sub_cores'].items():
            score_sum = 0
            # .get() を使い、'scores' キーが無くてもエラーにならないようにする
            scores_dict = details.get('scores', {})
            
            if isinstance(scores_dict, dict):
                for dim, weight in scores_dict.items():
                    if dim in big_five_raw:
                        score_sum += big_five_raw[dim] * weight
            sub_core_scores[sub_core_name] = score_sum
    
    # sub_core_scoresが空でないことを確認してからmax()を呼び出す
    if sub_core_scores:
        sub_core = max(sub_core_scores, key=sub_core_scores.get)

    return main_core, sub_core, seven_dimensions, big_five_raw, similarity_scores

# グローバル変数でセッション管理（簡易実装）
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
    main_core, sub_core, seven_dimensions, big_five_raw, similarity_scores = \
        calculate_creator_personality_final(answers, QUESTIONS_DATA, TYPE_LOGIC)
    
    # 分析データの取得
    analysis_data = ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {})
    
    # データ分析
    extreme_answers = sum(1 for ans in answers if ans == 1 or ans == 5)
    extremeness_score = (extreme_answers / 20) * 100
    
    if extremeness_score >= 75:
        extremeness_comment = "あなたは自分の考えやスタイルが非常に明確で、白黒はっきりさせる傾向があります。"
    elif extremeness_score >= 50:
        extremeness_comment = "あなたは多くの事柄に対して自分の意見をしっかり持っているタイプです。"
    else:
        extremeness_comment = "あなたは物事を多角的に捉え、バランスの取れた判断をする傾向があります。"
    
    bf_scores_jp = {
        "独創性": big_five_raw['Openness'],
        "計画性": big_five_raw['Conscientiousness'],
        "社交性": big_five_raw['Extraversion'],
        "共感力": big_five_raw['Agreeableness'],
        "精神的安定性": -big_five_raw['Neuroticism']
    }
    
    deviations = {k: abs(v) for k, v in bf_scores_jp.items()}
    most_unique_trait = max(deviations, key=deviations.get)
    
    uniqueness_comment = f"あなたのビッグファイブ特性の中で、平均的な傾向から最も大きく離れているのは「{most_unique_trait}」です。"
    
    # レスポンスの構築
    response = {
        'user_id': user_id,
        'main_core_name': ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core),
        'sub_core_title': analysis_data.get("sub_core_title", sub_core),
        'suited_for': analysis_data.get("suited_for", ""),
        'not_suited_for': analysis_data.get("not_suited_for", ""),
        'synthesis': analysis_data.get("synthesis", ""),
        'radar_scores': {
            k: round(v, 1) for k, v in seven_dimensions.items()
        },
        'data_analysis': {
            'extremeness_score': round(extremeness_score),
            'extremeness_comment': extremeness_comment,
            'most_unique_trait': most_unique_trait,
            'uniqueness_comment': uniqueness_comment
        },
        'completed_at': datetime.now().isoformat()
    }
    
    # セッションに保存
    USER_SESSIONS[user_id] = response
    
    return jsonify(response)

@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    # セッションからデータを取得
    if user_id in USER_SESSIONS:
        result_data = USER_SESSIONS[user_id]
    else:
        # ダミーデータ（セッションが無い場合）
        result_data = {
            'main_core_name': '孤高のアーティスト',
            'sub_core_title': '静かな共感の表現者',
            'suited_for': 'あなたの独創性の高さから、他の人には思いつかない斬新な表現を生み出すことに長けている傾向があります。',
            'not_suited_for': '集団での作業や、既存の枠組みに縛られる活動は、あなたの特性とは合わないかもしれません。',
            'synthesis': 'あなたは独自の世界観を持ち、一人の時間を大切にしながら深く考え、創作に取り組むタイプです。',
            'radar_scores': {
                '独創性': 8.5,
                '計画性': 7.0,
                '社交性': 2.5,
                '共感力': 5.0,
                '精神的安定性': 5.5,
                '創作スタイル': 8.0,
                '協働適性': 3.5
            }
        }
    
    # PDF生成
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