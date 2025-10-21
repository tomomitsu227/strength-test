# backend/app.py
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import io
from models import save_response, get_all_responses, calculate_scores
from pdf_generator import generate_pdf_report

app = Flask(__name__)
CORS(app)

# 質問データの読み込み
with open('data/questions.json', 'r', encoding='utf-8') as f:
    QUESTIONS_DATA = json.load(f)

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """質問データを返す"""
    return jsonify(QUESTIONS_DATA)

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
    answers = data.get('answers')  # [1, 3, 5, 2, ...] 20個の回答
    
    if not user_id or not answers or len(answers) != 20:
        return jsonify({'error': '無効なデータ'}), 400
    
    # 回答を保存
    save_response(user_id, answers)
    
    # スコア計算
    scores = calculate_scores(answers, QUESTIONS_DATA)
    
    return jsonify({
        'user_id': user_id,
        'scores': scores,
        'completed_at': datetime.now().isoformat()
    })

@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    """PDF診断レポートを生成してダウンロード"""
    # 該当ユーザーの回答とスコアを取得
    responses = get_all_responses()
    user_data = next((r for r in responses if r['user_id'] == user_id), None)
    
    if not user_data:
        return jsonify({'error': 'ユーザーが見つかりません'}), 404
    
    # スコア再計算
    scores = calculate_scores(user_data['answers'], QUESTIONS_DATA)
    
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
