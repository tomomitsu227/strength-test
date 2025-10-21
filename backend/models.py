# backend/models.py
import json
import os
from datetime import datetime
from pathlib import Path

# データファイルのパス
DATA_DIR = Path('data')
RESPONSES_FILE = DATA_DIR / 'responses.json'

def init_data_dir():
    """dataディレクトリとファイルの初期化"""
    DATA_DIR.mkdir(exist_ok=True)
    if not RESPONSES_FILE.exists():
        with open(RESPONSES_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

# 初期化
init_data_dir()

def save_response(user_id, answers):
    """
    回答をJSONファイルに保存
    将来的にDB操作に置き換え可能な構造
    """
    # 既存データの読み込み
    with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
        responses = json.load(f)
    
    # 新しい回答を追加
    response_data = {
        'user_id': user_id,
        'answers': answers,
        'timestamp': datetime.now().isoformat()
    }
    responses.append(response_data)
    
    # ファイルに保存
    with open(RESPONSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)
    
    return response_data

def get_all_responses():
    """全回答データを取得（DB移行時はSELECT文に置き換え）"""
    with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_response_by_user_id(user_id):
    """特定ユーザーの回答を取得（DB移行時はWHERE句に置き換え）"""
    responses = get_all_responses()
    return next((r for r in responses if r['user_id'] == user_id), None)

def calculate_scores(answers, questions_data):
    """
    回答から各ドメインのスコアを計算
    エビデンスの強さによる重み付けを適用
    """
    questions = questions_data['questions']
    domains = questions_data['domains']
    
    # ドメインごとのスコア集計
    domain_scores = {}
    domain_counts = {}
    category_scores = {}
    
    for i, answer in enumerate(answers):
        q = questions[i]
        domain = q['domain']
        category = q['category']
        weight = q['weight']
        
        # ドメインスコアの集計
        if domain not in domain_scores:
            domain_scores[domain] = 0
            domain_counts[domain] = 0
        
        domain_scores[domain] += answer * weight
        domain_counts[domain] += 1
        
        # カテゴリスコアの集計
        if category not in category_scores:
            category_scores[category] = []
        category_scores[category].append(answer)
    
    # 平均スコアの計算とエビデンス重み付け適用
    results = {}
    for domain, total in domain_scores.items():
        count = domain_counts[domain]
        avg_score = total / count if count > 0 else 0
        evidence_weight = domains[domain]['evidence_weight']
        
        # 最終スコア = 平均スコア × エビデンス重み
        weighted_score = avg_score * evidence_weight
        
        results[domain] = {
            'name': domains[domain]['name'],
            'raw_score': round(avg_score, 2),
            'weighted_score': round(weighted_score, 2),
            'evidence_weight': evidence_weight,
            'description': domains[domain]['description']
        }
    
    # カテゴリ別の詳細スコア
    category_details = {}
    for category, scores in category_scores.items():
        avg = sum(scores) / len(scores) if scores else 0
        category_details[category] = round(avg, 2)
    
    return {
        'domain_scores': results,
        'category_scores': category_details,
        'total_responses': len(answers)
    }
