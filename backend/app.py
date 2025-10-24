# backend/app.py - ビッグファイブベースの完全改訂版

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

# --- ビッグファイブベースの診断ロジック ---
def calculate_bigfive_scores(answers, questions_data):
    """
    ビッグファイブ5特性のスコアを計算
    """
    scores = {
        "Openness": 0,
        "Conscientiousness": 0,
        "Extraversion": 0,
        "Agreeableness": 0,
        "Neuroticism": 0
    }
    
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]
        dimension = question['dimension']
        # 1-5のスケールを-2から+2に変換
        score = answer - 3
        # 方向に応じてスコアを加算
        if question['direction'] == '+':
            scores[dimension] += score
        else:
            scores[dimension] -= score
    
    # 各特性は4問ずつなので、-8〜+8の範囲
    # これを0〜5のスケールに正規化
    normalized_scores = {}
    for dim, raw_score in scores.items():
        # -8〜+8を0〜5に変換
        normalized_scores[dim] = ((raw_score + 8) / 16) * 5
    
    return normalized_scores


def calculate_derived_scores(bigfive_scores):
    """
    ビッグファイブから派生指標を計算
    """
    derived = {}
    
    # 基本5特性（日本語名にマッピング）
    derived['独創性'] = bigfive_scores['Openness']
    derived['計画性'] = bigfive_scores['Conscientiousness']
    derived['社交性'] = bigfive_scores['Extraversion']
    derived['共感力'] = bigfive_scores['Agreeableness']
    derived['精神的安定性'] = 5 - bigfive_scores['Neuroticism']  # 神経症傾向は逆転
    
    # 派生指標
    derived['創作スタイル'] = (bigfive_scores['Openness'] * 0.6) + \
                              ((5 - bigfive_scores['Conscientiousness']) * 0.4)
    derived['協働適性'] = (bigfive_scores['Extraversion'] * 0.5) + \
                          (bigfive_scores['Agreeableness'] * 0.5)
    
    return derived


def determine_main_core(derived_scores, logic_data):
    """
    コサイン類似度で最適なメインコアを判定
    """
    dimension_order = ['独創性', '計画性', '社交性', '共感力', '精神的安定性', '創作スタイル', '協働適性']
    user_vector = np.array([derived_scores[dim] for dim in dimension_order])
    
    similarity_scores = {}
    for core_type, core_data in logic_data['main_core_profiles'].items():
        ideal_vector = np.array([
            core_data['ideal_scores'][dim] for dim in dimension_order
        ])
        similarity = cosine_similarity(
            user_vector.reshape(1, -1),
            ideal_vector.reshape(1, -1)
        )[0][0]
        similarity_scores[core_type] = similarity
    
    main_core = max(similarity_scores, key=similarity_scores.get)
    return main_core, similarity_scores


def determine_sub_core(derived_scores, logic_data):
    """
    派生スコアからサブコアを判定（簡易ルールベース）
    """
    if derived_scores['計画性'] > 3.5:
        return 'The Planner'
    elif derived_scores['精神的安定性'] > 3.5 and derived_scores['独創性'] > 3.0:
        return 'The Analyst'
    elif derived_scores['共感力'] > 3.5:
        return 'The Harmonizer'
    elif derived_scores['計画性'] < 2.5 and derived_scores['社交性'] > 3.0:
        return 'The Accelerator'
    elif derived_scores['独創性'] > 3.5 and derived_scores['社交性'] < 3.0:
        return 'The Deep-Diver'
    else:
        # デフォルトは最も高いスコアの特性から判定
        max_trait = max(derived_scores, key=derived_scores.get)
        if max_trait == '独創性':
            return 'The Deep-Diver'
        elif max_trait == '計画性':
            return 'The Planner'
        elif max_trait == '共感力':
            return 'The Harmonizer'
        else:
            return 'The Accelerator'


# --- APIエンドポイント ---

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """質問リストを返す"""
    return jsonify(QUESTIONS_DATA)


@app.route('/api/start', methods=['POST'])
def start_test():
    """診断開始"""
    return jsonify({
        'user_id': str(uuid.uuid4()),
        'started_at': datetime.now().isoformat()
    })


@app.route('/api/submit', methods=['POST'])
def submit_answers():
    """回答を受け取り、診断結果を返す"""
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    # バリデーション
    if not all([user_id, answers, len(answers) == 20]):
        return jsonify({'error': '無効なデータです'}), 400
    
    # ステップ1: ビッグファイブスコアの計算
    bigfive_scores = calculate_bigfive_scores(answers, QUESTIONS_DATA)
    
    # ステップ2: 派生指標の計算
    derived_scores = calculate_derived_scores(bigfive_scores)
    
    # ステップ3: メインコアの判定
    main_core, similarity_scores = determine_main_core(derived_scores, TYPE_LOGIC)
    
    # ステップ4: サブコアの判定
    sub_core = determine_sub_core(derived_scores, TYPE_LOGIC)
    
    # 分析データの取得
    analysis_data = ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {})
    
    # レーダーチャート用のスコア（0-10スケールに変換）
    radar_scores = {k: round(v * 2, 1) for k, v in derived_scores.items()}
    
    # レスポンスの構築
    response = {
        'user_id': user_id,
        'main_core_name': ANALYSIS_PATTERNS.get(main_core, {}).get("name", main_core),
        'sub_core_title': analysis_data.get("sub_core_title", sub_core),
        'suited_for': analysis_data.get("suited_for"),
        'not_suited_for': analysis_data.get("not_suited_for"),
        'synthesis': analysis_data.get("synthesis"),
        'radar_scores': radar_scores,
        'bigfive_scores': {k: round(v, 2) for k, v in bigfive_scores.items()},
        'completed_at': datetime.now().isoformat()
    }
    
    # デバッグ情報(開発時のみ)
    if app.debug and similarity_scores:
        response['debug_info'] = {
            'similarity_scores': {
                k: round(v, 3) for k, v in similarity_scores.items()
            },
            'top_3_matches': sorted(
                similarity_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        }
    
    return jsonify(response)


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
        'radar_scores': result_data.get('radar_scores')
    }
    
    try:
        # PDF生成
        pdf_buffer = generate_pdf_report_final("report", pdf_data)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='creator_core_report.pdf'
        )
    except Exception as e:
        return jsonify({'error': f'PDF生成中にエラーが発生しました: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
