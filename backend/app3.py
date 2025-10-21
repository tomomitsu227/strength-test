# backend/app.py (改善版)
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import io
from models import save_response, get_all_responses, calculate_scores
from pdf_generator import generate_pdf_report
import base64

app = Flask(__name__)
CORS(app)

# 質問データの読み込み
with open('data/questions.json', 'r', encoding='utf-8') as f:
    QUESTIONS_DATA = json.load(f)

# ユーザー向けドメイン名マッピング（専門用語を非表示）
USER_FRIENDLY_NAMES = {
    '4brain': {
        'name': '思考スタイル',
        'description': 'あなたの思考の特徴や情報処理の傾向を示します。論理的思考と直感的思考のバランス、計画性や視覚的理解力など、思考の個性が表れています。'
    },
    'VIA': {
        'name': '性格の強み',
        'description': 'ポジティブ心理学に基づく、あなたの性格における強みです。好奇心、希望、親切心、忍耐力、誠実性など、人格的な長所を示します。'
    },
    'strengths': {
        'name': '才能と資質',
        'description': '自然に発揮できる才能や特性です。影響力、分析力、創造性、人間関係構築力、達成志向など、あなたの得意分野を表しています。'
    },
    'motivation': {
        'name': 'モチベーション特性',
        'description': '目標達成や継続力に関する特性です。困難への対処、挑戦意欲、自信、目標設定能力、サポート活用力などが含まれます。'
    }
}

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """質問データを返す（ユーザー向けに加工）"""
    # ドメイン名を分かりやすく変換
    user_data = QUESTIONS_DATA.copy()
    return jsonify(user_data)

@app.route('/api/start', methods=['POST'])
def start_test():
    """新しいテストセッションを開始（匿名ID生成）"""
    user_id = str(uuid.uuid4())
    return jsonify({
        'user_id': user_id,
        'started_at': datetime.now().isoformat()
    })

@app.route('/api/submit', methods=['POST'])
def submit_answers():
    """回答を保存してスコアを計算"""
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    if not user_id or not answers or len(answers) != 20:
        return jsonify({'error': '無効なデータ'}), 400
    
    # 回答を保存
    save_response(user_id, answers)
    
    # スコア計算
    scores = calculate_scores(answers, QUESTIONS_DATA)
    
    # ユーザー向けに名称を変換
    for domain_key in scores['domain_scores']:
        if domain_key in USER_FRIENDLY_NAMES:
            scores['domain_scores'][domain_key]['name'] = USER_FRIENDLY_NAMES[domain_key]['name']
            scores['domain_scores'][domain_key]['description'] = USER_FRIENDLY_NAMES[domain_key]['description']
    
    return jsonify({
        'user_id': user_id,
        'scores': scores,
        'completed_at': datetime.now().isoformat()
    })

@app.route('/api/charts/<user_id>', methods=['GET'])
def get_charts(user_id):
    """グラフ画像をBase64で返す"""
    from pdf_generator import create_radar_chart, create_domain_bar_chart
    
    responses = get_all_responses()
    user_data = next((r for r in responses if r['user_id'] == user_id), None)
    
    if not user_data:
        return jsonify({'error': 'ユーザーが見つかりません'}), 404
    
    scores = calculate_scores(user_data['answers'], QUESTIONS_DATA)
    
    # グラフ生成
    radar_buffer = create_radar_chart(scores['category_scores'])
    bar_buffer = create_domain_bar_chart(scores['domain_scores'])
    
    # Base64エンコード
    radar_b64 = base64.b64encode(radar_buffer.read()).decode('utf-8')
    bar_b64 = base64.b64encode(bar_buffer.read()).decode('utf-8')
    
    return jsonify({
        'radar_chart': f'data:image/png;base64,{radar_b64}',
        'bar_chart': f'data:image/png;base64,{bar_b64}'
    })

@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    """PDF診断レポートを生成してダウンロード"""
    responses = get_all_responses()
    user_data = next((r for r in responses if r['user_id'] == user_id), None)
    
    if not user_data:
        return jsonify({'error': 'ユーザーが見つかりません'}), 404
    
    # スコア再計算
    scores = calculate_scores(user_data['answers'], QUESTIONS_DATA)
    
    # ユーザー向け名称に変換
    for domain_key in scores['domain_scores']:
        if domain_key in USER_FRIENDLY_NAMES:
            scores['domain_scores'][domain_key]['name'] = USER_FRIENDLY_NAMES[domain_key]['name']
            scores['domain_scores'][domain_key]['description'] = USER_FRIENDLY_NAMES[domain_key]['description']
    
    # PDF生成
    pdf_buffer = generate_pdf_report(user_id, scores, QUESTIONS_DATA)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'strength_report_{user_id[:8]}.pdf'
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
