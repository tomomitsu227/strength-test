# backend/app.py - 改善版 (コサイン類似度ベースの診断ロジック)

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

# --- 診断ロジック(改善版) ---
def calculate_creator_personality_advanced(answers, questions_data, logic_data):
    """
    コサイン類似度ベースの診断ロジック
    各メインコアタイプの理想プロファイルとの類似度を計算し、最も近いタイプを判定
    """
    # 1. 各ディメンションのスコアを計算
    scores = {
        "Openness": 0,
        "Conscientiousness": 0,
        "Extraversion": 0,
        "Agreeableness": 0,
        "StressTolerance": 0,
        "InformationStyle": 0,
        "DecisionMaking": 0,
        "MotivationSource": 0,
        "ValuePursuit": 0,
        "WorkStyle": 0
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
    
    # 2. ユーザーのスコアベクトルを作成
    dimension_order = [
        "Openness", "Conscientiousness", "Extraversion", "Agreeableness", 
        "StressTolerance", "InformationStyle", "DecisionMaking", 
        "MotivationSource", "ValuePursuit", "WorkStyle"
    ]
    user_vector = np.array([scores[dim] for dim in dimension_order])
    
    # 3. 各メインコアタイプとの類似度を計算
    similarity_scores = {}
    
    # 新しいロジック形式の場合
    if 'main_core_profiles' in logic_data:
        for core_type, core_data in logic_data['main_core_profiles'].items():
            ideal_vector = np.array([
                core_data['ideal_scores'][dim] for dim in dimension_order
            ])
            # コサイン類似度を計算
            similarity = cosine_similarity(
                user_vector.reshape(1, -1),
                ideal_vector.reshape(1, -1)
            )[0][0]
            similarity_scores[core_type] = similarity
    
    # 古いロジック形式の場合(後方互換性)
    else:
        matched_cores = []
        for core_rule in logic_data['main_cores']:
            is_match = True
            if 'all' in core_rule['conditions']:
                for condition in core_rule['conditions']['all']:
                    dim = condition['dimension']
                    op = condition['operator']
                    val = condition['value']
                    if op == '>' and not scores[dim] > val:
                        is_match = False
                        break
                    if op == '<' and not scores[dim] < val:
                        is_match = False
                        break
            if is_match:
                matched_cores.append(core_rule)
        
        if matched_cores:
            matched_cores.sort(key=lambda x: x['priority'], reverse=True)
            main_core = matched_cores[0]['type']
        else:
            main_core = logic_data.get('fallback_main_core', 'Practical Entertainer')
    
    # 4. 最も類似度の高いタイプを判定
    if similarity_scores:
        main_core = max(similarity_scores, key=similarity_scores.get)
        max_similarity = similarity_scores[main_core]
    else:
        max_similarity = None
    
    # 5. サブコアの判定(従来通り)
    sub_core_scores = {}
    for sub_core, details in logic_data['sub_cores'].items():
        score_sum = sum(
            scores[dim] * weight 
            for dim, weight in details['scores'].items()
        )
        sub_core_scores[sub_core] = score_sum
    
    sub_core = max(sub_core_scores, key=sub_core_scores.get)
    
    return main_core, sub_core, scores, similarity_scores

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
    main_core, sub_core, scores, similarity_scores = calculate_creator_personality_advanced(
        answers, QUESTIONS_DATA, TYPE_LOGIC
    )
    
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
    bf_scores = {
        "開放性": scores['Openness'],
        "誠実性": scores['Conscientiousness'],
        "外向性": scores['Extraversion'],
        "協調性": scores['Agreeableness'],
        "ストレス耐性": scores['StressTolerance']
    }
    
    deviations = {k: abs(v) for k, v in bf_scores.items()}
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
        'suited_for': analysis_data.get("suited_for"),
        'not_suited_for': analysis_data.get("not_suited_for"),
        'synthesis': analysis_data.get("synthesis"),
        'radar_scores': {
            k: round(((v + 4) / 8) * 10, 1) 
            for k, v in scores.items()
        },
        'raw_scores': scores,  # デバッグ用に生スコアも含める
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
        'radar_scores': result_data.get('radar_scores'),
        'data_analysis': result_data.get('data_analysis', {})
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
