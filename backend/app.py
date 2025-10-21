# backend/app.py - 改善版（総合評価・レーダースコア追加）
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
from models_mbti import save_response, get_all_responses, calculate_mbti_result
from pdf_generator_mbti_improved import generate_pdf_report
import os



app = Flask(__name__)
CORS(app)

# MBTI質問データの読み込み
# ファイルパスを動的に取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'mbti_questions.json')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
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

# 総合評価テンプレート（メリデメ含む5行要約）
OVERALL_SUMMARIES = {
    "INTJ": """あなたは戦略的思考と長期的視点に優れた「戦略家」タイプです。専門性の高いコンテンツで確実にファンを獲得できる一方、完璧主義が行動を遅らせる可能性があります。計画的なアプローチは強みですが、柔軟性も意識することで更に成長できます。ニッチ分野での深い解説は競合が少なく、収益化しやすい特徴があります。まずは完璧を求めず、小さく始めて改善を重ねる姿勢が成功への鍵となるでしょう。""",
    
    "INTP": """あなたは知的好奇心と分析力に優れた「思索家」タイプです。複雑なテーマを深く掘り下げるコンテンツで熱狂的なファンを獲得できますが、完璧主義やこだわりが投稿頻度を下げるリスクがあります。独自の視点は大きな強みですが、視聴者目線でのわかりやすさも意識しましょう。マニアック過ぎないバランスが取れれば、高単価の専門分野で安定収益が期待できます。興味の赴くままに多様なテーマを扱える柔軟性も武器になります。""",
    
    "ENTJ": """あなたはリーダーシップと目標達成力に優れた「指揮官」タイプです。強いメッセージ性で多くの視聴者を惹きつけられる一方、主張が強すぎるとアンチを生む可能性もあります。ビジネス系コンテンツは収益性が高く、企業案件も獲得しやすい特徴があります。実績や成功体験を示すことで説得力が増し、信頼を築けます。ただし、視聴者との双方向コミュニケーションも意識することで、さらに強固なコミュニティを形成できるでしょう。""",
    
    "ENTP": """あなたは創造性と即興力に優れた「発明家」タイプです。トレンドに敏感で斬新な企画を次々生み出せる強みがある一方、継続性に課題を感じることもあります。バラエティ豊かなコンテンツは幅広い層にアプローチできますが、チャンネルの方向性が定まりにくいリスクもあります。議論や討論形式は高エンゲージメントを生み、熱心なファンを獲得しやすい特徴があります。好奇心を武器に、複数の収益モデルを組み合わせることで安定した成功が期待できます。""",
    
    "INFJ": """あなたは洞察力と共感力に優れた「提唱者」タイプです。深いメッセージで視聴者の心に響くコンテンツを作れる一方、完璧主義や理想の高さが投稿を遅らせる可能性があります。ストーリーテリングの才能は大きな武器で、熱心なコミュニティを形成しやすい特徴があります。ライフスタイルやメンタルヘルス分野は需要が高く、長期的な信頼関係で安定収益が見込めます。ただし、自己開示とプライバシーのバランスを保つことも重要です。""",
    
    "INFP": """あなたは創造性と独自性に優れた「仲介者」タイプです。個性的な世界観で唯一無二のコンテンツを作れる強みがある一方、批判への敏感さが活動の妨げになることもあります。芸術的センスとオリジナリティは熱狂的なファンを獲得しやすく、グッズ販売やクリエイター案件との相性も抜群です。ニッチな分野で確固たるポジションを築けば、競合が少なく収益化しやすい環境を作れます。自分らしさを貫く勇気が、最大の成功要因となるでしょう。""",
    
    "ENFJ": """あなたはカリスマ性とコミュニティ形成力に優れた「主人公」タイプです。人を惹きつける魅力で強固なファンベースを築ける一方、他者への配慮が過度になりストレスを感じることもあります。エンゲージメント重視のスタイルは高い視聴者満足度を生み、メンバーシップやライブ配信での収益化に強みがあります。教育やインスパイア系コンテンツは需要が安定しており、長期的な成功が期待できます。視聴者との対話を楽しみながら、自分のペースを保つことも大切です。""",
    
    "ENFP": """あなたはエネルギーと情熱に溢れた「広報運動家」タイプです。多様なコンテンツで幅広い視聴者を獲得できる強みがある一方、飽きやすさや計画性の欠如が課題になることもあります。バラエティ豊かなアプローチは複数の収益源を確保しやすく、柔軟な戦略展開が可能です。視聴者参加型企画は高いエンゲージメントを生み、コミュニティが活性化しやすい特徴があります。好奇心を活かしつつ、コアとなるテーマを持つことで、さらに安定した成長が見込めます。""",
    
    "ISTJ": """あなたは信頼性と継続力に優れた「管理者」タイプです。堅実な投稿スケジュールと質の高いコンテンツで確実にファンを増やせる一方、柔軟性や即興性に課題を感じることもあります。How-toやレビュー系は検索流入が多く、長期的に安定した視聴数が見込めます。SEO最適化との相性が良く、広告収益を着実に積み上げられる特徴があります。信頼の積み重ねは大きな武器ですが、時にはトレンドへの対応も意識することで、さらなる成長が期待できます。""",
    
    "ISFJ": """あなたは思いやりと丁寧さに優れた「擁護者」タイプです。視聴者に寄り添う温かいコンテンツで信頼を築ける一方、自己主張の弱さが成長を遅らせる可能性もあります。料理や育児など実用系コンテンツは需要が安定しており、長期的なファン獲得に適しています。視聴者との丁寧なコミュニケーションは高い満足度を生み、口コミでの拡散も期待できます。ただし、自分の意見や個性も積極的に出すことで、さらに魅力的なチャンネルになるでしょう。""",
    
    "ESTJ": """あなたは組織力と実行力に優れた「幹部」タイプです。効率的な運営と明確な成果提示で確実にチャンネルを成長させられる一方、柔軟性の欠如や厳格さが視聴者を遠ざけることもあります。ビジネス効率化や実践的スキル系コンテンツは収益性が高く、企業案件も獲得しやすい特徴があります。体系的な学習シリーズは高い価値を提供し、リピーターを増やしやすい強みがあります。データ重視のアプローチは説得力抜群ですが、時には感情や共感も意識するとバランスが取れます。""",
    
    "ESFJ": """あなたは社交性と協調性に優れた「領事官」タイプです。親しみやすいコンテンツで幅広い層にアプローチできる一方、批判への敏感さや他者依存が課題になることもあります。視聴者参加型企画やコラボは高いエンゲージメントを生み、コミュニティが活性化しやすい特徴があります。トレンド紹介やイベントレポートは需要が高く、広告収益と企業案件の両方を狙いやすい強みがあります。明るく前向きな姿勢は視聴者に元気を与え、長期的なファン獲得に繋がります。""",
    
    "ISTP": """あなたは実践力と技術力に優れた「巨匠」タイプです。専門的なHow-toコンテンツで確固たるポジションを築ける一方、感情表現や視聴者との交流が苦手なこともあります。DIYやメカニック系は競合が少なく、高単価の企業案件を獲得しやすい特徴があります。手を動かす過程を見せる動画は高い満足度を生み、熱心なファンを獲得しやすい強みがあります。専門性は大きな武器ですが、わかりやすい説明と視覚的な編集を意識することで、さらに多くの視聴者にリーチできます。""",
    
    "ISFP": """あなたは芸術性と感性に優れた「冒険家」タイプです。美しいビジュアルと独自の世界観で視聴者を魅了できる一方、自己主張の弱さや計画性の欠如が課題になることもあります。アートやクラフト系コンテンツはクリエイター案件との相性が抜群で、グッズ販売などの収益化手段も豊富です。創作過程の共有は高いエンゲージメントを生み、熱心なコミュニティを形成しやすい特徴があります。自分らしさを大切にしながら、定期的な投稿を心がけることで、安定した成長が見込めます。""",
    
    "ESTP": """あなたは行動力と即応力に優れた「起業家」タイプです。トレンドに即座に反応し話題を集められる強みがある一方、計画性の欠如や飽きやすさが課題になることもあります。スポーツやチャレンジ企画は高い注目を集めやすく、短期間での急成長が期待できます。ダイナミックなコンテンツは広告収益とスポンサー案件の両方を狙いやすい特徴があります。スピード感は武器ですが、チャンネルの方向性や継続性も意識することで、さらに安定した成功を掴めるでしょう。""",
    
    "ESFP": """あなたはエンタメ性と明るさに優れた「エンターテイナー」タイプです。視聴者を笑顔にする才能で多くのファンを獲得できる一方、計画性の欠如や感情的な投稿が課題になることもあります。エンタメ系コンテンツは需要が非常に高く、広告収益とスポンサー案件の両方を狙いやすい強みがあります。視聴者との距離が近いスタイルは高いエンゲージメントを生み、コミュニティが活性化しやすい特徴があります。楽しむ姿勢を保ちつつ、戦略的な視点も持つことで、更なる飛躍が期待できます。"""
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
    overall_summary = OVERALL_SUMMARIES.get(mbti_type, OVERALL_SUMMARIES["INFP"])
    
    # レーダーチャート用スコア正規化（0-10スケール）
    max_score = max(abs(v) for v in scores.values()) or 1
    radar_scores = {k: round((abs(v) / max_score) * 10, 1) for k, v in scores.items()}
    
    # トップ3の強みを抽出（スコアが高い順）
    sorted_scores = sorted(scores.items(), key=lambda x: abs(x[1]), reverse=True)
    strength_labels = {
        'E': '社交性・外向性', 'I': '内省性・独立性',
        'S': '現実主義・実用性', 'N': '想像力・直感力',
        'T': '論理性・分析力', 'F': '共感力・調和性',
        'J': '計画性・組織力', 'P': '柔軟性・適応力'
    }
    top_strengths = [strength_labels[key] for key, value in sorted_scores[:3]]
    
    return jsonify({
        'user_id': user_id,
        'animal_name': animal_data['name'],
        'animal_icon': animal_data['icon'],
        'animal_description': animal_data['description'],
        'top_strengths': top_strengths,
        'youtube_strategy': youtube_strategy,
        'overall_summary': overall_summary,
        'radar_scores': radar_scores,
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
    overall_summary = OVERALL_SUMMARIES.get(mbti_type, OVERALL_SUMMARIES["INFP"])
    
    # レーダーチャート用スコア
    max_score = max(abs(v) for v in scores.values()) or 1
    radar_scores = {k: round((abs(v) / max_score) * 10, 1) for k, v in scores.items()}
    
    result = {
        'animal_name': animal_data['name'],
        'animal_icon': animal_data['icon'],
        'animal_description': animal_data['description'],
        'youtube_strategy': youtube_strategy,
        'overall_summary': overall_summary,
        'radar_scores': radar_scores
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
