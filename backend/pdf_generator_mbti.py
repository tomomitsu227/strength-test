# backend/pdf_generator_mbti.py - MBTI診断PDF生成（Tailwindデザイン風）
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import io

# 日本語フォント設定
try:
    pdfmetrics.registerFont(TTFont('Japanese', 'ipaexg.ttf'))
    FONT_NAME = 'Japanese'
except:
    try:
        pdfmetrics.registerFont(TTFont('Japanese', 'C:/Windows/Fonts/msgothic.ttc'))
        FONT_NAME = 'Japanese'
    except:
        FONT_NAME = 'Helvetica'

def generate_pdf_report(user_id, result):
    """
    MBTI診断結果のPDFレポートを生成
    
    Args:
        user_id: ユーザーID
        result: 診断結果（mbti_type, animal_name, animal_icon, youtube_strategy等）
    
    Returns:
        BytesIO: PDF バイナリデータ
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # カスタムスタイル定義
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=28,
        textColor=colors.HexColor('#EF4444'),  # Tailwind red-500
        spaceAfter=10,
        alignment=TA_CENTER,
        leading=36
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=14,
        textColor=colors.HexColor('#6B7280'),  # Tailwind gray-500
        spaceAfter=30,
        alignment=TA_CENTER,
        leading=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=18,
        textColor=colors.HexColor('#1F2937'),  # Tailwind gray-800
        spaceAfter=12,
        spaceBefore=20,
        leading=24
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=18,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#374151')  # Tailwind gray-700
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=12,
        leading=20,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#4B5563')  # Tailwind gray-600
    )
    
    # ========== タイトルページ ==========
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph('YouTube強み診断レポート', title_style))
    story.append(Paragraph('あなたの才能を「稼げる動画」に変える', subtitle_style))
    
    # 診断ID
    story.append(Paragraph(f'診断ID: {user_id[:12]}', normal_style))
    story.append(Spacer(1, 1*cm))
    
    # ========== 診断結果サマリー ==========
    # 動物タイプ表示（大きく）
    animal_display = f'<font size="48">{result["animal_icon"]}</font>'
    animal_para = Paragraph(animal_display, ParagraphStyle(
        'AnimalIcon',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        spaceAfter=10
    ))
    story.append(animal_para)
    
    animal_name_style = ParagraphStyle(
        'AnimalName',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=24,
        textColor=colors.HexColor('#EF4444'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph(f'あなたは「{result["animal_name"]}」タイプ', animal_name_style))
    story.append(Paragraph(result["animal_description"], body_style))
    story.append(Spacer(1, 1*cm))
    
    # ========== MBTIタイプ表示 ==========
    story.append(Paragraph(f'診断タイプ: <b>{result["mbti_type"]}</b>', heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    # ========== あなたに最適なYouTube戦略 ==========
    story.append(Paragraph('🎯 あなたに最適なYouTube戦略', heading_style))
    
    strategy = result['youtube_strategy']
    
    # 戦略テーブル
    strategy_data = [
        ['項目', '内容'],
        ['おすすめジャンル', strategy['genre']],
        ['コンテンツの方向性', strategy['direction']],
        ['成功のポイント', strategy['success_tips']]
    ]
    
    strategy_table = Table(strategy_data, colWidths=[4*cm, 12*cm])
    strategy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FEF2F2')),  # red-50
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
    ]))
    
    story.append(strategy_table)
    story.append(Spacer(1, 1*cm))
    
    # ========== 具体的なアクションプラン ==========
    story.append(Paragraph('📋 今日から始める具体的アクション', heading_style))
    
    action_points = [
        f'<b>ステップ1:</b> {strategy["genre"]}のジャンルで、既存の人気チャンネルを3つ以上リサーチしましょう。',
        f'<b>ステップ2:</b> {strategy["direction"]}この方向性で、自分なりの切り口を考えてみましょう。',
        '<b>ステップ3:</b> まずは3本の動画を試作してみる。完璧を求めず、まず行動することが成功への近道です。',
        f'<b>ステップ4:</b> {strategy["success_tips"]}この成功ポイントを常に意識して動画を作りましょう。'
    ]
    
    for point in action_points:
        story.append(Paragraph(point, body_style))
        story.append(Spacer(1, 0.3*cm))
    
    story.append(Spacer(1, 1*cm))
    
    # ========== あなたのタイプに合った成功事例 ==========
    story.append(Paragraph('✨ あなたのタイプに合った成功パターン', heading_style))
    
    # タイプ別の成功パターン（例）
    success_patterns = {
        'INTJ': '長期的な視点で、専門性の高いコンテンツを体系的に発信。視聴者からの信頼を積み重ねて収益化に成功。',
        'INTP': 'ニッチな専門分野を深掘りし、熱狂的なファンを獲得。広告収益＋メンバーシップで安定収入を実現。',
        'ENTJ': '強いメッセージ性とビジョンで多くのフォロワーを獲得。企業案件やコンサルティングに展開し高収益化。',
        'ENTP': 'トレンドを素早くキャッチし、バラエティ豊かなコンテンツで視聴数を伸ばす。複数の収益源を確保。',
        'INFJ': '深いストーリーテリングで視聴者の心を掴み、熱心なコミュニティを形成。グッズ販売やオンライン講座で収益化。',
        'INFP': '独自の世界観とオリジナリティで差別化。クリエイティブな作品をファンが支援する形で収益を得る。',
        'ENFJ': 'コミュニティ運営力を活かし、視聴者との強い絆を構築。ライブ配信やイベントで高いエンゲージメントを実現。',
        'ENFP': '多様なコンテンツで幅広い層にアプローチ。複数の収益モデルを組み合わせて成功。',
        'ISTJ': '継続的な投稿と高品質なコンテンツで信頼を獲得。SEO最適化で検索流入を増やし安定収益。',
        'ISFJ': '視聴者に寄り添う温かいコンテンツで固定ファンを獲得。コミュニティの力で長期的に成功。',
        'ESTJ': '効率的な運営と実用的なコンテンツで視聴者数を拡大。ビジネス展開で高収益化。',
        'ESFJ': '視聴者との交流を大切にし、参加型企画で人気を獲得。コラボやイベントで収益を多角化。',
        'ISTP': '専門技術を活かしたHow-toコンテンツで差別化。企業案件や教材販売で収益化。',
        'ISFP': '芸術的センスを活かした美しいコンテンツで独自のポジションを確立。クリエイター案件で高収益。',
        'ESTP': 'ダイナミックな企画とスピード感で注目を集める。トレンド対応力で広告収益を最大化。',
        'ESFP': 'エンタメ性の高いコンテンツで多くの視聴者を魅了。スポンサー案件や商品紹介で収益化。'
    }
    
    success_text = success_patterns.get(result['mbti_type'], '自分の強みを活かして、継続的にコンテンツを発信することで成功を掴みましょう。')
    story.append(Paragraph(success_text, body_style))
    story.append(Spacer(1, 1*cm))
    
    # ========== 最後のメッセージ ==========
    story.append(Paragraph('🚀 さあ、あなたのYouTubeチャンネルを始めよう！', heading_style))
    final_message = '''
    この診断結果は、あなたの強みとYouTubeでの可能性を示すものです。
    成功への道は一つではありません。このレポートを参考にしながら、
    自分らしいスタイルで動画作りを楽しんでください。
    
    最初の一歩を踏み出すことが、何よりも大切です。
    完璧を求めず、まずは行動を始めましょう。
    
    あなたのチャンネルが成功することを心から応援しています！
    '''
    story.append(Paragraph(final_message, body_style))
    
    # PDF生成
    doc.build(story)
    buffer.seek(0)
    return buffer
