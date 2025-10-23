# backend/app.py - 高精度診断ロジック ＆ ファイル名修正版
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os
from models_mbti import save_response, get_all_responses
from pdf_generator_mbti_improved import generate_pdf_report

app = Flask(__name__)
CORS(app)

# --- ファイルパスの定義 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ★★★ 変更点：読み込むJSONファイル名を'questions.json'に変更 ★★★
QUESTIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'questions.json') 
TYPE_LOGIC_PATH = os.path.join(BASE_DIR, '..', 'data', 'type_logic.json')

# --- 設定ファイルの読み込み ---
try:
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        QUESTIONS_DATA = json.load(f)
    with open(TYPE_LOGIC_PATH, 'r', encoding='utf-8') as f:
        TYPE_LOGIC = json.load(f)
except FileNotFoundError as e:
    print(f"エラー: 設定ファイルが見つかりません。- {e}")
    exit()
except json.JSONDecodeError as e:
    print(f"エラー: JSONファイルの形式が正しくありません。 - {e}")
    exit()


# --- 診断タイプの詳細データ ---
# (app.py内に保持することで、ロジックと表示内容を分離)
TYPE_DETAILS = {
    "Solitary Artist": {"name": "孤高のアーティスト", "icon": "🎨", "compass": "独創的な世界観を持ち、一人で黙々と作品制作に打ち込む内向的な革新者。あなたの深い内省から生まれるユニークな視点が、最大の武器です。", "focus_area": "作り込まれた映像作品、専門性の高い解説、アート系Vlogなど、独自の世界観を表現するコンテンツ制作。", "selective_focus": "大人数のコラボや頻繁なライブ配信よりも、作品のクオリティを追求することに時間を使いましょう。", "recommended_style": "映像作品、専門解説、アート系Vlog"},
    "Trend Hacker": {"name": "トレンドハッカー", "icon": "📈", "compass": "流行を冷静に分析し、効率的に成果を出す方法を模索する内向的な効率家。データに基づいた戦略で、最短ルートを切り開きます。", "focus_area": "切り抜き動画、データに基づいた考察、効率化ノウハウなど、需要が証明されているフォーマットのコンテンツ制作。", "selective_focus": "ゼロから企画を生み出すよりも、成功事例を分析・応用することに集中するのが成功の鍵です。", "recommended_style": "切り抜き、データ考察、効率化ノウハウ"},
    "Knowledge Seeker": {"name": "知の探求者", "icon": "📚", "compass": "深いリサーチと論理的思考で戦略を練り上げる、内向的なイノベーター。あなたの知的好奇心が、質の高いコンテンツの源泉です。", "focus_area": "複雑なテーマの長尺解説、教育系コンテンツ、書評など、深い知識を要するジャンルでの戦略設計。", "selective_focus": "表面的なトレンド追従よりも、一つのテーマを深く掘り下げ、専門家としての地位を築くことに集中しましょう。", "recommended_style": "長尺解説、教育コンテンツ、書評"},
    "System Architect": {"name": "再現性の巨匠", "icon": "⚙️", "compass": "成功法則をシステム化し、安定したチャンネル成長を設計する内向的な戦略家。再現性のある仕組み作りで、盤石な基盤を築きます。", "focus_area": "チャンネル運営ノウハウ、再現性の高いチュートリアル、AI動画の量産など、運営をシステム化する戦略。", "selective_focus": "単発のバズを狙うより、継続的に成果を出せる仕組み作りにリソースを投下することが重要です。", "recommended_style": "運営ノウハウ、チュートリアル、AI活用"},
    "Empathetic Storyteller": {"name": "共感のストーリーテラー", "icon": "🖋️", "compass": "人の心に寄り添い、丁寧なコミュニケーションでファンを育てる内向的なサポーター。あなたの共感力が、強いコミュニティを形成します。", "focus_area": "丁寧な暮らしVlog、視聴者の悩みに答えるコンテンツ、コミュニティ運営など、ファンとの深い関係構築。", "selective_focus": "過度な自己主張よりも、視聴者の心に寄り添うストーリーを語ることで、あなたの価値は最大化されます。", "recommended_style": "暮らしVlog、お悩み相談、コミュニティ運営"},
    "Supportive Producer": {"name": "縁の下のプロデューサー", "icon": "🤝", "compass": "他のクリエイターやチームを後方から支え、成功に導く内向的なマネージャー。あなたのサポートが、チームの力を最大化します。", "focus_area": "チーム運営、編集代行、裏方としてのチャンネルサポートなど、他者の成功を支援する役割。", "selective_focus": "自分が表舞台に立つことよりも、チーム全体の成功をデザインすることに集中すると輝きます。", "recommended_style": "チーム運営、編集代行、裏方サポート"},
    "Spotlight Pioneer": {"name": "スポットライトの開拓者", "icon": "🌟", "compass": "常に新しい企画に挑戦し、人々を惹きつけるカリスマを持つ外向的な革新者。あなたの行動力が、新たなトレンドを生み出します。", "focus_area": "顔出しでのチャレンジ企画、最新ガジェットレビューなど、自分が主役となるエンタメコンテンツ制作。", "selective_focus": "緻密なデータ分析よりも、直感と行動力を信じて、前例のないことに挑戦し続けることが成功への道です。", "recommended_style": "チャレンジ企画、最新ガジェットレビュー"},
    "Practical Entertainer": {"name": "実践的エンターテイナー", "icon": "🎬", "compass": "視聴者が求めるものを的確に捉え、高いクオリティで提供し続ける外向的な実践家。安定した面白さが、多くのファンを惹きつけます。", "focus_area": "商品紹介、視聴者参加型企画など、需要が明確で再現性の高いエンタメコンテンツ制作。", "selective_focus": "奇抜なアイデアを追うよりも、定番のフォーマットを高いレベルで実行することに集中しましょう。", "recommended_style": "商品紹介、視聴者参加型企画"},
    "Visionary Leader": {"name": "ビジョナリー・リーダー", "icon": "🚀", "compass": "未来のビジョンを掲げ、チームを率いて大きなプロジェクトを動かす外向的な戦略家。あなたのリーダーシップが、不可能を可能にします。", "focus_area": "大規模コラボの主宰、プロダクト開発、事業展開を見据えたチャンネル戦略の設計と実行。", "selective_focus": "一人でのコンテンツ制作よりも、チームを組成し、大きなビジョンを実現するためのマネジメントに集中すべきです。", "recommended_style": "大規模コラボ、プロダクト開発、事業展開"},
    "Community Organizer": {"name": "コミュニティ・オーガナイザー", "icon": "🎉", "compass": "人と人をつなぎ、活気あるコミュニティを形成・運営する外向的な戦略家。あなたの求心力が、熱狂的なファンベースを築きます。", "focus_area": "オンラインサロン運営、イベント主催、ファンコミュニティの活性化など、人と繋がる戦略。", "selective_focus": "コンテンツの質を追求するだけでなく、視聴者同士が交流できる「場」作りに力を入れると成功します。", "recommended_style": "オンラインサロン、イベント主催"},
    "Passionate Evangelist": {"name": "情熱の伝道師", "icon": "🔥", "compass": "好きなモノやコトへの愛を熱く語り、その魅力をファンに伝染させる外向的なサポーター。あなたの情熱が、視聴者の心を動かします。", "focus_area": "趣味特化型チャンネル（ゲーム実況、アニメ考察）、ファンとの交流がメインのライブ配信。", "selective_focus": "客観的なレビューよりも、あなたの「好き」という主観的な熱量を前面に出すことが最大の武器です。", "recommended_style": "趣味特化チャンネル、ライブ配信"},
    "Team Captain": {"name": "チームの司令塔", "icon": "🏆", "compass": "チーム全体の目標達成にコミットし、メンバーの能力を最大限に引き出す外向的なマネージャー。あなたの指揮が、チームを勝利に導きます。", "focus_area": "複数人でのチャンネル運営、MCNのマネジメントなど、チームを率いて成果を出す役割。", "selective_focus": "プレイヤーとして活躍するよりも、チームメンバーが輝ける環境を整える監督役に徹すると真価を発揮します。", "recommended_style": "複数人チャンネル運営、MCNマネジメント"}
}
SUB_CORE_DATA = {
    "The Planner": {"name": "プランナータイプ", "desc": "計画性に優れ、目標達成までの道のりを着実に実行します。"}, "The Analyst": {"name": "アナリストタイプ", "desc": "データと論理を重視し、客観的な事実から最適解を導き出します。"}, "The Harmonizer": {"name": "ハーモナイザータイプ", "desc": "共感力が高く、チームやコミュニティに一体感をもたらします。"}, "The Accelerator": {"name": "アクセラレータータイプ", "desc": "行動力とスピードを重視し、実践と改善を繰り返しながら前進します。"}, "The Deep-Diver": {"name": "ディープダイバータイプ", "desc": "探求心が強く、物事の本質を深く掘り下げて専門性を武器にします。"}
}

# --- 高精度診断ロジック ---
def calculate_creator_personality_advanced(answers, questions_data, logic_data):
    """回答とロジック定義に基づき、10次元スコアとタイプを計算する"""
    scores = {
        "Openness": 0, "Conscientiousness": 0, "Extraversion": 0, "Agreeableness": 0,
        "StressTolerance": 0, "InformationStyle": 0, "DecisionMaking": 0,
        "MotivationSource": 0, "ValuePursuit": 0, "WorkStyle": 0
    }
    
    for i, answer in enumerate(answers):
        question = questions_data['questions'][i]
        dimension = question['dimension']
        score = answer - 3
        
        if question['direction'] == '+':
            scores[dimension] += score
        else:
            scores[dimension] -= score

    # --- メインコアの決定ロジック ---
    matched_cores = []
    for core_rule in logic_data['main_cores']:
        is_match = True
        if 'all' in core_rule['conditions']:
            for condition in core_rule['conditions']['all']:
                dim, op, val = condition['dimension'], condition['operator'], condition['value']
                if op == '>' and not scores[dim] > val: is_match = False; break
                if op == '<' and not scores[dim] < val: is_match = False; break
                if op == '>=' and not scores[dim] >= val: is_match = False; break
                if op == '<=' and not scores[dim] <= val: is_match = False; break
        if is_match:
            matched_cores.append(core_rule)
    
    if matched_cores:
        # 優先度が最も高いものを選択
        matched_cores.sort(key=lambda x: x['priority'], reverse=True)
        main_core = matched_cores[0]['type']
    else:
        # 一致するものがなければフォールバック
        main_core = logic_data['fallback_main_core']

    # --- サブコアの決定ロジック ---
    sub_core_scores = {}
    for sub_core, details in logic_data['sub_cores'].items():
        total_score = 0
        for dim, weight in details['scores'].items():
            total_score += scores[dim] * weight
        sub_core_scores[sub_core] = total_score
    
    sub_core = max(sub_core_scores, key=sub_core_scores.get)

    return main_core, sub_core, scores


# --- APIエンドポイント ---
@app.route('/api/questions', methods=['GET'])
def get_questions():
    return jsonify(QUESTIONS_DATA)

@app.route('/api/start', methods=['POST'])
def start_test():
    user_id = str(uuid.uuid4())
    return jsonify({'user_id': user_id, 'started_at': datetime.now().isoformat()})

@app.route('/api/submit', methods=['POST'])
def submit_answers():
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    if not user_id or not answers or len(answers) != 20:
        return jsonify({'error': '無効なデータ'}), 400
    
    save_response(user_id, answers)
    
    main_core, sub_core, scores = calculate_creator_personality_advanced(answers, QUESTIONS_DATA, TYPE_LOGIC)
    
    main_core_info = TYPE_DETAILS[main_core]
    sub_core_info = SUB_CORE_DATA[sub_core]

    motivation_type = "内発的動機づけ（探求型）" if scores['MotivationSource'] > 0 else "外発的動機づけ（達成型）"
    motivation_guide = "あなたの情熱は、自分の内側から湧き上がる「知りたい」「面白い」という気持ちから生まれます。短期的な成果よりも、長期的に探求できるテーマを見つけることが成功の鍵です。" if scores['MotivationSource'] > 0 else "あなたの情熱は、目に見える「成果」によって燃え上がります。具体的で測定可能な短期目標を積み重ねていくアプローチが最適です。"

    radar_scores = {k: round(((v + 4) / 8) * 10, 1) for k, v in scores.items()}
    
    sorted_scores = sorted(scores.items(), key=lambda x: abs(x[1]), reverse=True)
    strength_labels = {'Openness': '開放性・創造力', 'Conscientiousness': '誠実性・計画力', 'Extraversion': '外向性・社交性', 'Agreeableness': '協調性・共感力', 'StressTolerance': 'ストレス耐性・冷静沈着', 'InformationStyle': '情報処理スタイル', 'DecisionMaking': '意思決定スタイル', 'MotivationSource': 'モチベーション源泉', 'ValuePursuit': '価値追求スタイル', 'WorkStyle': '作業スタイル'}
    top_strengths = [strength_labels[key] for key, value in sorted_scores[:3]]

    return jsonify({
        'user_id': user_id,
        'animal_name': f"{main_core_info['name']} - {sub_core_info['name']}",
        'animal_icon': main_core_info['icon'],
        'animal_description': f"{main_core_info['compass']} {sub_core_info['desc']}",
        'top_strengths': top_strengths,
        'youtube_strategy': {"genre": main_core_info['recommended_style'], "direction": main_core_info['focus_area'], "success_tips": main_core_info['selective_focus']},
        'overall_summary': f"【モチベーションの源泉と指針】\nタイプ: {motivation_type}\n\n{motivation_guide}",
        'radar_scores': radar_scores,
        'completed_at': datetime.now().isoformat()
    })

@app.route('/api/pdf/<user_id>', methods=['GET'])
def download_pdf(user_id):
    responses = get_all_responses()
    user_data = next((r for r in responses if r['user_id'] == user_id), None)
    
    if not user_data:
        return jsonify({'error': 'ユーザーが見つかりません'}), 404
    
    main_core, sub_core, scores = calculate_creator_personality_advanced(user_data['answers'], QUESTIONS_DATA, TYPE_LOGIC)
    main_core_info = TYPE_DETAILS[main_core]
    sub_core_info = SUB_CORE_DATA[sub_core]
    
    motivation_type = "内発的動機づけ（探求型）" if scores['MotivationSource'] > 0 else "外発的動機づけ（達成型）"
    motivation_guide = "あなたの情熱は、自分の内側から湧き上がる「知りたい」「面白い」という気持ちから生まれます。短期的な成果よりも、長期的に探求できるテーマを見つけることが成功の鍵です。" if scores['MotivationSource'] > 0 else "あなたの情熱は、目に見える「成果」によって燃え上がります。具体的で測定可能な短期目標を積み重ねていくアプローチが最適です。"
    radar_scores = {k: round(((v + 4) / 8) * 10, 1) for k, v in scores.items()}

    result = {
        'animal_name': f"{main_core_info['name']} - {sub_core_info['name']}",
        'animal_icon': main_core_info['icon'],
        'animal_description': f"{main_core_info['compass']} {sub_core_info['desc']}",
        'youtube_strategy': {"genre": main_core_info['recommended_style'], "direction": main_core_info['focus_area'], "success_tips": main_core_info['selective_focus']},
        'overall_summary': f"【モチベーションの源泉と指針】\nタイプ: {motivation_type}\n\n{motivation_guide}",
        'radar_scores': radar_scores
    }
    
    pdf_buffer = generate_pdf_report(user_id, result)
    
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=f'youtube_strength_report_{user_id[:8]}.pdf')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)