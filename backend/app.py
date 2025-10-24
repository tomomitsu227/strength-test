# backend/app.py - ビッグファイブ7次元対応版（レイアウト完全保持）

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

# --- 診断ロジック(ビッグファイブ7次元対応) ---
def calculate_creator_personality_bigfive(answers, questions_data, logic_data):
    """
    ビッグファイブ理論に基づく7次元診断ロジック
    - 独創性（Openness）
    - 計画性（Conscientiousness）
    - 社交性（Extraversion）
    - 共感力（Agreeableness）
    - 精神的安定性（Emotional Stability）
    - 創作スタイル（Openness + Conscientiousness複合）
    - 協働適性（Extraversion + Agreeableness複合）
    """
    
    # 1. ビッグファイブ5次元のスコアを計算
    big_five = {
        "Openness": 0,
        "Conscientiousness": 0,
        "Extraversion": 0,
        "Agreeableness": 0,
        "Neuroticism": 0  # 逆転して「精神的安定性」になる
    }
    
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]
        dimension = question['dimension']
        direction = question['direction']
        
        # 1-5のスケールを-2から+2に変換
        score = answer - 3
        
        # 方向に応じてスコアを加算
        if direction == '+':
            big_five[dimension] += score
        else:
            big_five[dimension] -= score
    
    # 2. 7次元スコアを作成（0-10スケール）
    def normalize_score(raw_score, min_val=-8, max_val=8):
        """生スコアを0-10スケールに正規化"""
        return ((raw_score - min_val) / (max_val - min_val)) * 10
    
    seven_dimensions = {
        "独創性": normalize_score(big_five["Openness"]),
        "計画性": normalize_score(big_five["Conscientiousness"]),
        "社交性": normalize_score(big_five["Extraversion"]),
        "共感力": normalize_score(big_five["Agreeableness"]),
        "精神的安定性": normalize_score(-big_five["Neuroticism"]),  # 逆転
        "創作スタイル": normalize_score((big_five["Openness"] - big_five["Conscientiousness"]) / 2),
        "協働適性": normalize_score((big_five["Extraversion"] + big_five["Agreeableness"]) / 2)
    }
    
    # 3. メインコアタイプの判定（コサイン類似度ベース）
    dimension_order = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
    user_vector = np.array([big_five[dim] for dim in dimension_order])
    
    similarity_scores = {}
    
    # 新しいロジック形式の場合
    if 'main_core_profiles' in logic_data:
        for core_type, core_data in logic_data['main_core_profiles'].items():
            # ideal_scoresからビッグファイブ5次元を抽出
            ideal_bf = {
                "Openness": core_data['ideal_scores'].get('Openness', 0),
                "Conscientiousness": core_data['ideal_scores'].get('Conscientiousness', 0),
                "Extraversion": core_data['ideal_scores'].get('Extraversion', 0),
                "Agreeableness": core_data['ideal_scores'].get('Agreeableness', 0),
                "Neuroticism": core_data['ideal_scores'].get('Neuroticism', 0)
            }
            ideal_vector = np.array([ideal_bf[dim] for dim in dimension_order])
            
            # コサイン類似度を計算
            similarity = cosine_similarity(
                user_vector.reshape(1, -1),
                ideal_vector.reshape(1, -1)
            )[0][0]
            similarity_scores[core_type] = similarity
    
    # 最も類似度の高いタイプを判定
    if similarity_scores:
        main_core = max(similarity_scores, key=similarity_scores.get)
    else:
        main_core = 'Practical Entertainer'  # フォールバック
    
    # 4. サブコアの判定
    sub_core_scores = {}
    
    if 'sub_cores' in logic_data:
        for sub_core, details in logic_data['sub_cores'].items():
            score_sum = 0
            for dim, weight in details['scores'].items():
                if dim in big_five:
                    score_sum += big_five[dim] * weight
            sub_core_scores[sub_core] = score_sum
        
        sub_core = max(sub_core_scores, key=sub_core_scores.get)
    else:
        sub_core = "The Planner"  # フォールバック
    
    return main_core, sub_core, seven_dimensions, big_five, similarity_scores


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
    
    # 診断実行
    main_core, sub_core, seven_dimensions, big_five, similarity_scores = \
        calculate_creator_personality_bigfive(answers, QUESTIONS_DATA, TYPE_LOGIC)
    
    # 分析データの取得
    analysis_data = ANALYSIS_PATTERNS.get(main_core, {}).get(sub_core, {})
    
    # データ分析:回答の明確さ
    extreme_answers = sum(1 for ans in answers if ans == 1 or ans == 5)
    extremeness_score = (extreme_answers / 20) * 100
    
    if extremeness_score >= 75:
        extremeness_comment = (
            "あなたは自分の考えやスタイルが非常に明確で、白黒はっきりさせる傾向があります。"
            "この「尖った」姿勢が熱狂的なファンを生む一方で、時には賛否が分かれる可能性も秘めています。"
        )
    elif extremeness_score >= 50:
        extremeness_comment = (
            "あなたは多くの事柄に対して自分の意見をしっかり持っているタイプです。"
            "その明確なスタンスが、あなたのクリエイターとしての個性や「色」に繋がっています。"
        )
    else:
        extremeness_comment = (
            "あなたは物事を多角的に捉え、バランスの取れた判断をする傾向があります。"
            "その柔軟性は多くの人に受け入れられやすい一方で、強い個性を出すには意識的な工夫が必要かもしれません。"
        )
    
    # データ分析:最も特徴的な才能
    bf_scores_jp = {
        "独創性": big_five['Openness'],
        "計画性": big_five['Conscientiousness'],
        "社交性": big_five['Extraversion'],
        "共感力": big_five['Agreeableness'],
        "精神的安定性": -big_five['Neuroticism']
    }
    
    deviations = {k: abs(v) for k, v in bf_scores_jp.items()}
    most_unique_trait = max(deviations, key=deviations.get)
    
    uniqueness_comment = (
        f"あなたのビッグファイブ特性の中で、平均的な傾向から最も大きく離れているのは"
        f"「{most_unique_trait}」です。これはあなたのパーソナリティを特徴づける最もユニークな才能であり、"
        f"他の人にはない強力な武器となる可能性を秘めています。"
    )
    
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
            )[:3],
            'big_five_raw': big_five
        }
    
    return jsonify(response)


@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    """PDF生成とダウンロード"""
    # TODO: user_idから結果データを取得する実装が必要
    # 現在は仮の実装
    return jsonify({'error': 'PDF生成機能は開発中です'}), 501


@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
