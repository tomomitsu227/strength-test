# backend/models_mbti.py - MBTI診断ロジック
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path('data')
RESPONSES_FILE = DATA_DIR / 'responses.json'

def init_data_dir():
    """dataディレクトリとファイルの初期化"""
    DATA_DIR.mkdir(exist_ok=True)
    if not RESPONSES_FILE.exists():
        with open(RESPONSES_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

init_data_dir()

def save_response(user_id, answers):
    """回答をJSONファイルに保存"""
    with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
        responses = json.load(f)
    
    response_data = {
        'user_id': user_id,
        'answers': answers,
        'timestamp': datetime.now().isoformat()
    }
    responses.append(response_data)
    
    with open(RESPONSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)
    
    return response_data

def get_all_responses():
    """全回答データを取得"""
    with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_mbti_result(answers, questions_data):
    """
    MBTI結果を計算
    E/I, S/N, T/F, J/P の4軸スコアを算出し、MBTI 4文字を決定
    """
    questions = questions_data['questions']
    
    # 各タイプのスコア集計
    type_scores = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
    
    for i, answer in enumerate(answers):
        q = questions[i]
        q_type = q['type']
        weight = q['weight']
        
        # 回答値（1-5）をスコアに変換
        # 5: 強くそう思う = +2, 4: そう思う = +1, 3: 中立 = 0, 2: そう思わない = -1, 1: 全くそう思わない = -2
        score = (answer - 3) * weight
        type_scores[q_type] += score
    
    # MBTI 4文字を決定
    mbti_type = ''
    mbti_type += 'E' if type_scores['E'] >= type_scores['I'] else 'I'
    mbti_type += 'S' if type_scores['S'] >= type_scores['N'] else 'N'
    mbti_type += 'T' if type_scores['T'] >= type_scores['F'] else 'F'
    mbti_type += 'J' if type_scores['J'] >= type_scores['P'] else 'P'
    
    return mbti_type, type_scores
