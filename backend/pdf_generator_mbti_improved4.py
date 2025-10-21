# backend/pdf_generator_mbti_final.py - 完全改善版（美しいレイアウト）
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.graphics import renderPDF
import io

# 日本語フォント設定
try:
    pdfmetrics.registerFont(TTFont('Japanese', 'ipaexg.ttf'))
    pdfmetrics.registerFont(TTFont('JapaneseBold', 'ipaexg.ttf'))
    FONT_NAME = 'Japanese'
    FONT_BOLD = 'JapaneseBold'
except:
    try:
        pdfmetrics.registerFont(TTFont('Japanese', 'C:/Windows/Fonts/msgothic.ttc'))
        pdfmetrics.registerFont(TTFont('JapaneseBold', 'C:/Windows/Fonts/msgothic.ttc'))
        FONT_NAME = 'Japanese'
        FONT_BOLD = 'JapaneseBold'
    except:
        FONT_NAME = 'Helvetica'
        FONT_BOLD = 'Helvetica-Bold'

def create_radar_chart(radar_scores):
    """美しいレーダーチャートを生成"""
    drawing = Drawing(350, 350)
    
    spider = SpiderChart()
    spider.x = 25
    spider.y = 25
    spider.width = 300
    spider.height = 300
    
    spider.data = [[
        radar_scores.get('E', 5),
        radar_scores.get('I', 5),
        radar_scores.get('S', 5),
        radar_scores.get('N', 5),
        radar_scores.get('T', 5),
        radar_scores.get('F', 5),
        radar_scores.get('J', 5),
        radar_scores.get('P', 5),
    ]]
    
    spider.labels = ['外向性', '内向性', '感覚', '直感', '思考', '感情', '判断', '知覚']
    spider.strands[0].fillColor = colors.HexColor('#EF4444')
    spider.strands[0].fillColor.alpha = 0.3
    spider.strands[0].strokeColor = colors.HexColor('#DC2626')
    spider.strands[0].strokeWidth = 2.5
    
    # ラベルスタイル
    spider.labelFontSize = 10
    spider.labelFontName = FONT_NAME
    
    drawing.add(spider)
    return drawing

def create_header_box(title, icon):
    """セクションヘッダーボックスを作成"""
    drawing = Drawing(500, 50)
    
    # 背景ボックス
    rect = Rect(0, 10, 500, 35)
    rect.fillColor = colors.HexColor('#FEF2F2')
    rect.strokeColor = colors.HexColor('#EF4444')
    rect.strokeWidth = 2
    drawing.add(rect)
    
    # アイコン
    icon_text = String(15, 22, icon)
    icon_text.fontName = FONT_NAME
    icon_text.fontSize = 20
    drawing.add(icon_text)
    
    # タイトル
    title_text = String(50, 25, title)
    title_text.fontName = FONT_BOLD
    title_text.fontSize = 16
    title_text.fillColor = colors.HexColor('#DC2626')
    drawing.add(title_text)
    
    return drawing

def generate_pdf_report(user_id, result):
    """
    完全改善版PDFレポート生成
    - 美しいレイアウト
    - 適切な余白とスペーシング
    - プロフェッショナルなデザイン
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=15*mm,
        leftMargin=20*mm,
        rightMargin=20*mm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ========== カスタムスタイル定義 ==========
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_BOLD,
        fontSize=26,
        textColor=colors.HexColor('#DC2626'),
        spaceAfter=8,
        alignment=TA_CENTER,
        leading=32
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=13,
        textColor=colors.HexColor('#6B7280'),
        spaceAfter=20,
        alignment=TA_CENTER,
        leading=18
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_BOLD,
        fontSize=16,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=10,
        spaceBefore=15,
        leading=22
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10.5,
        leading=16,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#374151')
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName=FONT_BOLD,
        fontSize=11
    )
    
    # ========== カバーページ ==========
    story.append(Spacer(1, 20*mm))
    
    # タイトル
    story.append(Paragraph('YouTube強み診断レポート', title_style))
    story.append(Paragraph('あなたの才能を「稼げる動画」に変える', subtitle_style))
    
    story.append(Spacer(1, 15*mm))
    
    # 動物アイコン（超大きく）
    animal_icon_style = ParagraphStyle(
        'AnimalIconHuge',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=80,
        alignment=TA_CENTER,
        spaceAfter=8
    )
    story.append(Paragraph(result["animal_icon"], animal_icon_style))
    
    # 動物タイプ名
    animal_name_style = ParagraphStyle(
        'AnimalNameLarge',
        parent=styles['Heading1'],
        fontName=FONT_BOLD,
        fontSize=22,
        textColor=colors.HexColor('#DC2626'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    story.append(Paragraph(f'あなたは「{result["animal_name"]}」タイプ', animal_name_style))
    
    # 説明
    description_style = ParagraphStyle(
        'Description',
        parent=body_style,
        fontSize=11,
        alignment=TA_CENTER,
        leading=18
    )
    story.append(Paragraph(result["animal_description"], description_style))
    
    story.append(Spacer(1, 10*mm))
    
    # 診断ID（小さく）
    id_style = ParagraphStyle(
        'IDText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        textColor=colors.HexColor('#9CA3AF'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(f'診断ID: {user_id[:12]}', id_style))
    
    story.append(PageBreak())
    
    # ========== レーダーチャート ==========
    story.append(Spacer(1, 10*mm))
    header_box = create_header_box('あなたの性格分析', '📊')
    story.append(header_box)
    story.append(Spacer(1, 8*mm))
    
    try:
        radar_drawing = create_radar_chart(result.get('radar_scores', {}))
        story.append(radar_drawing)
    except Exception as e:
        story.append(Paragraph('※チャート生成エラー', body_style))
    
    story.append(Spacer(1, 10*mm))
    
    # ========== YouTube戦略 ==========
    header_box2 = create_header_box('あなたに最適なYouTube戦略', '🎯')
    story.append(header_box2)
    story.append(Spacer(1, 8*mm))
    
    strategy = result['youtube_strategy']
    
    # 戦略テーブル（改善版）
    strategy_data = [
        [Paragraph('<b>おすすめジャンル</b>', bold_body_style), 
         Paragraph(strategy['genre'], body_style)],
        [Paragraph('<b>コンテンツの方向性</b>', bold_body_style), 
         Paragraph(strategy['direction'], body_style)],
        [Paragraph('<b>成功のポイント</b>', bold_body_style), 
         Paragraph(strategy['success_tips'], body_style)]
    ]
    
    strategy_table = Table(strategy_data, colWidths=[45*mm, 120*mm])
    strategy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FEE2E2')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#DC2626')),
    ]))
    
    story.append(strategy_table)
    story.append(Spacer(1, 12*mm))
    
    # ========== 総合評価 ==========
    header_box3 = create_header_box('診断結果の総合評価', '📋')
    story.append(header_box3)
    story.append(Spacer(1, 8*mm))
    
    summary_style = ParagraphStyle(
        'SummaryBox',
        parent=body_style,
        fontSize=10.5,
        leading=18,
        alignment=TA_JUSTIFY,
        leftIndent=8,
        rightIndent=8,
        spaceBefore=8,
        spaceAfter=8
    )
    
    # 総合評価ボックス
    summary_text = result.get('overall_summary', '')
    summary_para = Paragraph(summary_text, summary_style)
    
    summary_table = Table([[summary_para]], colWidths=[165*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#F59E0B')),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 12*mm))
    
    # ========== アクションプラン ==========
    header_box4 = create_header_box('今日から始める具体的アクション', '✅')
    story.append(header_box4)
    story.append(Spacer(1, 8*mm))
    
    action_points = [
        f'<b>ステップ1:</b> {strategy["genre"]}のジャンルで、既存の人気チャンネルを3つ以上リサーチしましょう。',
        f'<b>ステップ2:</b> {strategy["direction"]}この方向性で、自分なりの切り口を考えてみましょう。',
        '<b>ステップ3:</b> まずは3本の動画を試作してみる。完璧を求めず、まず行動することが成功への近道です。',
        f'<b>ステップ4:</b> {strategy["success_tips"]}この成功ポイントを常に意識して動画を作りましょう。'
    ]
    
    action_style = ParagraphStyle(
        'ActionItem',
        parent=body_style,
        fontSize=10,
        leading=16,
        leftIndent=5,
        spaceBefore=4,
        spaceAfter=4
    )
    
    for i, point in enumerate(action_points, 1):
        action_data = [[Paragraph(f'<b>{i}</b>', bold_body_style), Paragraph(point, action_style)]]
        action_table = Table(action_data, colWidths=[12*mm, 153*mm])
        action_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#DBEAFE')),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3B82F6')),
        ]))
        story.append(action_table)
        story.append(Spacer(1, 4*mm))
    
    story.append(Spacer(1, 15*mm))
    
    # ========== フッター ==========
    footer_style = ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        textColor=colors.HexColor('#9CA3AF'),
        alignment=TA_CENTER,
        leading=14
    )
    
    story.append(Paragraph('このレポートがあなたのYouTube成功への第一歩となることを願っています。', footer_style))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('© 2025 強み発見ナビ All Rights Reserved', footer_style))
    
    # PDF生成
    doc.build(story)
    buffer.seek(0)
    return buffer
