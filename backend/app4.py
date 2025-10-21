# backend/app.py - MBTI診断＋YouTube戦略バージョン
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
from models_mbti import save_response, get_all_responses, calculate_mbti_result
from pdf_generator_mbti import generate_pdf_report

app = Flask(__name__)
CORS(app)

# MBTI質問データの読み込み
with open('data/mbti_questions.json', 'r', encoding='utf-8') as f:
    QUESTIONS_DATA = json.load(f)

# 動物タイプデータ
ANIMAL_TYPES = {
    "INTJ": {"name": "戦略家フクロウ", "icon": "🦉", "description": "論理的で独創的な戦略家。長期的なビジョンと緻密な計画でYouTubeを構築します。"},
    "INTP": {"name": "思索家ネコ", "icon": "🐱", "description": "知的好奇心旺盛な分析家。深い洞察と独自の視点でニッチな分野で輝きます。"},
    "ENTJ": {"name": "指揮官ライオン", "icon": "🦁", "description": "カリスマ的なリーダー。目標達成力と説得力でチャンネルを成長させます。"},
    "ENTP": {"name": "発明家キツネ", "icon": "🦊", "description": "創造的でチャレンジ精神旺盛。新しいアイデアで視聴者を魅了します。"},
    "INFJ": {"name": "提唱者シカ", "icon": "🦌", "description": "洞察力があり理想主義的。深いメッセージで人々の心に響く動画を作ります。"},
    "INFP": {"name": "仲介者ウサギ", "icon": "🐰", "description": "創造的で共感力が高い。個性的な世界観で独自のファンベースを築きます。"},
    "ENFJ": {"name": "主人公イルカ", "icon": "🐬", "description": "人を惹きつけるカリスマ性。コミュニティ作りとエンゲージメントが得意です。"},
    "ENFP": {"name": "広報運動家コアラ", "icon": "🐨", "description": "エネルギッシュで情熱的。多様なコンテンツで幅広い視聴者を獲得します。"},
    "ISTJ": {"name": "管理者ビーバー", "icon": "🦫", "description": "堅実で信頼性が高い。継続的な投稿と質の高いコンテンツで成功します。"},
    "ISFJ": {"name": "擁護者パンダ", "icon": "🐼", "description": "思いやりがあり丁寧。視聴者に寄り添うコンテンツで信頼を築きます。"},
    "ESTJ": {"name": "幹部ゾウ", "icon": "🐘", "description": "組織力と実行力が強み。効率的な運営でチャンネルを拡大します。"},
    "ESFJ": {"name": "領事官イヌ", "icon": "🐕", "description": "社交的で協調性が高い。視聴者との交流を大切にするスタイルで成功します。"},
    "ISTP": {"name": "巨匠オオカミ", "icon": "🐺", "description": "実践的で技術志向。How-to系や専門技術で独自のポジションを確立します。"},
    "ISFP": {"name": "冒険家リス", "icon": "🐿️", "description": "芸術的で自由な精神。美的センスとオリジナリティで魅了します。"},
    "ESTP": {"name": "起業家サル", "icon": "🐵", "description": "行動力があり臨機応変。トレンドを捉えた即応力で伸びるチャンネルを作ります。"},
    "ESFP": {"name": "エンターテイナートラ", "icon": "🐯", "description": "陽気で人を楽しませる才能。エンタメ性の高いコンテンツで人気を集めます。"}
}

# YouTube戦略テンプレート
YOUTUBE_STRATEGIES = {
    "INTJ": {
        "genre": "教育・解説系、戦略分析、投資・ビジネス解説",
        "direction": "深い分析と独自の視点を活かした長期的な価値を提供するコンテンツ。データに基づいた説得力のある解説動画。",
        "success_tips": "専門性を高め、ニッチな分野でNo.1を目指す。計画的な動画シリーズで体系的な知識を提供しましょう。"
    },
    "INTP": {
        "genre": "科学・技術解説、哲学・思想、プログラミング・IT",
        "direction": "複雑なテーマをわかりやすく解説する知的好奇心をくすぐるコンテンツ。理論と実践のバランスが鍵。",
        "success_tips": "マニアックな深掘りコンテンツで熱狂的なファンを獲得。好奇心の赴くままに幅広いテーマを扱いましょう。"
    },
    "ENTJ": {
        "genre": "ビジネス・起業、リーダーシップ、自己啓発",
        "direction": "目標達成や成功法則を力強く語るモチベーショナルコンテンツ。視聴者を行動に駆り立てる動画作り。",
        "success_tips": "強いメッセージ性とビジョンを打ち出す。成功事例や実践的なステップを提示してエンゲージメントを高めましょう。"
    },
    "ENTP": {
        "genre": "エンタメ・バラエティ、時事ネタ解説、チャレンジ企画",
        "direction": "斬新なアイデアと即興性を活かしたバラエティ豊かなコンテンツ。議論や討論形式も効果的。",
        "success_tips": "トレンドに敏感に反応し、常に新しい企画を試す。視聴者参加型の企画でコミュニティを活性化しましょう。"
    },
    "INFJ": {
        "genre": "ライフスタイル・価値観、メンタルヘルス、スピリチュアル",
        "direction": "深い共感と洞察を込めた心に響くメッセージ。人生や社会についての意味深いコンテンツ。",
        "success_tips": "ストーリーテリングを活用し、視聴者の人生に寄り添う動画を作る。長期的な信頼関係を築きましょう。"
    },
    "INFP": {
        "genre": "クリエイティブ・アート、ライフログ、ストーリーテリング",
        "direction": "個性的な世界観と感性を表現するオリジナルコンテンツ。美しい映像と音楽でブランドを構築。",
        "success_tips": "自分らしさを貫き、ニッチなファン層を大切にする。創造的な表現で独自のポジションを確立しましょう。"
    },
    "ENFJ": {
        "genre": "コミュニティ運営、教育・インスパイア、人間関係",
        "direction": "人を繋ぎ、ポジティブな影響を与えるコンテンツ。視聴者との対話を重視したエンゲージメント重視型。",
        "success_tips": "ライブ配信やQ&Aで視聴者と密なコミュニケーションを。共感を呼ぶストーリーで感動を提供しましょう。"
    },
    "ENFP": {
        "genre": "ライフスタイル・Vlog、旅行・冒険、多彩なエンタメ",
        "direction": "エネルギッシュで多様なコンテンツ。情熱と好奇心が視聴者を引き込む。",
        "success_tips": "複数のテーマを組み合わせたバラエティ豊かなチャンネル運営。視聴者を巻き込む参加型企画を増やしましょう。"
    },
    "ISTJ": {
        "genre": "How-to・チュートリアル、レビュー、実用情報",
        "direction": "正確で詳細な情報提供。信頼性の高いレビューや手順解説で視聴者の問題を解決。",
        "success_tips": "継続的な投稿スケジュールを守り、信頼を積み重ねる。SEOを意識した検索に強いコンテンツ作りを心がけましょう。"
    },
    "ISFJ": {
        "genre": "料理・レシピ、育児・家事、お悩み相談",
        "direction": "視聴者に寄り添う温かいコンテンツ。実用的で親しみやすい動画作り。",
        "success_tips": "視聴者のコメントに丁寧に対応し、コミュニティを育てる。日常の工夫やライフハックで共感を得ましょう。"
    },
    "ESTJ": {
        "genre": "ビジネス効率化、プロジェクト管理、実践的スキル",
        "direction": "効率性と実用性を重視した実践的コンテンツ。明確な成果を示す動画作り。",
        "success_tips": "データや実績を提示して説得力を高める。体系的な学習シリーズで価値を提供しましょう。"
    },
    "ESFJ": {
        "genre": "ライフスタイル・交流、イベント・レポート、トレンド紹介",
        "direction": "社交的で親しみやすいコンテンツ。視聴者と一緒に楽しむスタイル。",
        "success_tips": "視聴者参加型企画やコラボを積極的に。明るく前向きなトーンでファンを増やしましょう。"
    },
    "ISTP": {
        "genre": "DIY・工作、メカニック・技術、ガジェットレビュー",
        "direction": "実践的な技術やスキルを披露するコンテンツ。手を動かす過程を見せる動画。",
        "success_tips": "専門技術を活かしたHow-toで差別化。視覚的にわかりやすい編集でファンを獲得しましょう。"
    },
    "ISFP": {
        "genre": "アート・クラフト、音楽・パフォーマンス、自然・風景",
        "direction": "芸術的センスを活かした美しいコンテンツ。感性に訴える映像作り。",
        "success_tips": "ビジュアルの美しさにこだわる。創作過程を共有してファンとの繋がりを深めましょう。"
    },
    "ESTP": {
        "genre": "スポーツ・アクション、チャレンジ企画、時事ネタ即応",
        "direction": "ダイナミックで刺激的なコンテンツ。トレンドに即座に反応する機動力。",
        "success_tips": "話題性のある企画で注目を集める。スピード感とエンタメ性で視聴者を飽きさせない工夫を。"
    },
    "ESFP": {
        "genre": "エンターテイメント全般、リアクション動画、ゲーム実況",
        "direction": "陽気で楽しい雰囲気のコンテンツ。視聴者を笑顔にする動画作り。",
        "success_tips": "エンタメ性を最大限に発揮。視聴者との距離感を近づけ、一緒に楽しむスタイルで人気を獲得しましょう。"
    }
}

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """MBTI質問データを返す"""
    return jsonify(QUESTIONS_DATA)

@app.route('/api/start', methods=['POST'])
def start_test():
    """新しいテストセッションを開始"""
    user_id = str(uuid.uuid4())
    return jsonify({
        'user_id': user_id,
        'started_at': datetime.now().isoformat()
    })

@app.route('/api/submit', methods=['POST'])
def submit_answers():
    """回答を保存してMBTI結果を計算"""
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    if not user_id or not answers or len(answers) != 20:
        return jsonify({'error': '無効なデータ'}), 400
    
    # 回答を保存
    save_response(user_id, answers)
    
    # MBTI結果計算
    mbti_type, scores = calculate_mbti_result(answers, QUESTIONS_DATA)
    
    # 動物タイプとYouTube戦略を取得
    animal_data = ANIMAL_TYPES.get(mbti_type, ANIMAL_TYPES["INFP"])
    youtube_strategy = YOUTUBE_STRATEGIES.get(mbti_type, YOUTUBE_STRATEGIES["INFP"])
    
    # トップ3の強みを抽出（スコアが高い順）
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_strengths = [
        f"{key}型の特性（スコア: {value:.1f}）" 
        for key, value in sorted_scores[:3]
    ]
    
    return jsonify({
        'user_id': user_id,
        'mbti_type': mbti_type,
        'animal_name': animal_data['name'],
        'animal_icon': animal_data['icon'],
        'animal_description': animal_data['description'],
        'top_strengths': top_strengths,
        'youtube_strategy': youtube_strategy,
        'completed_at': datetime.now().isoformat()
    })

@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    """PDF診断レポートを生成してダウンロード"""
    responses = get_all_responses()
    user_data = next((r for r in responses if r['user_id'] == user_id), None)
    
    if not user_data:
        return jsonify({'error': 'ユーザーが見つかりません'}), 404
    
    # MBTI結果再計算
    mbti_type, scores = calculate_mbti_result(user_data['answers'], QUESTIONS_DATA)
    animal_data = ANIMAL_TYPES.get(mbti_type, ANIMAL_TYPES["INFP"])
    youtube_strategy = YOUTUBE_STRATEGIES.get(mbti_type, YOUTUBE_STRATEGIES["INFP"])
    
    result = {
        'mbti_type': mbti_type,
        'animal_name': animal_data['name'],
        'animal_icon': animal_data['icon'],
        'animal_description': animal_data['description'],
        'youtube_strategy': youtube_strategy
    }
    
    # PDF生成
    pdf_buffer = generate_pdf_report(user_id, result)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'youtube_strength_report_{user_id[:8]}.pdf'
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
