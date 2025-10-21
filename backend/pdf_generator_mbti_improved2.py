# backend/pdf_generator_mbti_improved.py - PDF生成改善版
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.spider import SpiderChart
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

def create_radar_chart(radar_scores):
    """レーダーチャート画像を生成"""
    drawing = Drawing(400, 400)
    
    spider = SpiderChart()
    spider.x = 50
    spider.y = 50
    spider.width = 300
    spider.height = 300
    
    spider.data = [[
        radar_scores.get('E', 0),
        radar_scores.get('I', 0),
        radar_scores.get('S', 0),
        radar_scores.get('N', 0),
        radar_scores.get('T', 0),
        radar_scores.get('F', 0),
        spider.get('J', 0),
        radar_scores.get('P', 0),
    ]]
    
    spider.labels = ['外向性(E)', '内向性(I)', '感覚(S)', '直感(N)', '思考(T)', '感情(F)', '判断(J)', '知覚(P)']
    spider.strands[0].fillColor = colors.HexColor('#EF4444')
    spider.strands[0].strokeColor = colors.HexColor('#DC2626')
    spider.strands[0].strokeWidth = 2
    
    drawing.add(spider)
    return drawing

def generate_pdf_report(user_id, result):
    """
    MBTI診断結果のPDFレポートを生成（改善版）
    - 動物アイコン画像化
    - テーブル幅調整
    - 総合評価追加
    - レーダーチャート追加
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
        textColor=colors.HexColor('#EF4444'),
        spaceAfter=10,
        alignment=TA_CENTER,
        leading=36
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=14,
        textColor=colors.HexColor('#6B7280'),
        spaceAfter=30,
        alignment=TA_CENTER,
        leading=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=18,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=12,
        spaceBefore=20,
        leading=24
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=18,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#4B5563')
    )
    
    # ========== タイトルページ ==========
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph('YouTube強み診断レポート', title_style))
    story.append(Paragraph('あなたの才能を「稼げる動画」に変える', subtitle_style))
    
    # 診断ID
    story.append(Paragraph(f'診断ID: {user_id[:12]}', body_style))
    story.append(Spacer(1, 1*cm))
    
    # ========== 診断結果サマリー ==========
    # 動物アイコン（テキストとして大きく表示）
    animal_icon_style = ParagraphStyle(
        'AnimalIconLarge',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=72,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    story.append(Paragraph(result["animal_icon"], animal_icon_style))
    
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
    
    # ========== レーダーチャート ==========
    story.append(Paragraph('📊 あなたの性格分析', heading_style))
    radar_drawing = create_radar_chart(result.get('radar_scores', {}))
    story.append(radar_drawing)
    story.append(Spacer(1, 1*cm))
    
    # ========== あなたに最適なYouTube戦略 ==========
    story.append(Paragraph('🎯 あなたに最適なYouTube戦略', heading_style))
    
    strategy = result['youtube_strategy']
    
    # 戦略テーブル（列幅拡大・フォントサイズ調整）
    strategy_data = [
        ['項目', '内容'],
        ['おすすめジャンル', strategy['genre']],
        ['コンテンツの方向性', strategy['direction']],
        ['成功のポイント', strategy['success_tips']]
    ]
    
    strategy_table = Table(strategy_data, colWidths=[3.5*cm, 13*cm])
    strategy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FEF2F2')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    
    story.append(strategy_table)
    story.append(Spacer(1, 1*cm))
    
    # ========== 診断結果の総合評価 ==========
    story.append(Paragraph('📋 診断結果の総合評価', heading_style))
    
    summary_style = ParagraphStyle(
        'SummaryText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=20,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#374151'),
        spaceBefore=10,
        spaceAfter=10
    )
    
    story.append(Paragraph(result['overall_summary'], summary_style))
    story.append(Spacer(1, 1.5*cm))
    
    # ========== 具体的なアクションプラン ==========
    story.append(Paragraph('📋 今日から始める具体的アクション', heading_style))
    
    action_points = [
        f'<b>ステップ1:</b> {strategy["genre"]}のジャンルで、既存の人気チャンネルを3つ以上リサーチしましょう。',
        f'<b>ステップ2:</b> {strategy["direction"]}この方向性で、自分なりの切り口を考えてみましょう。',
        '<b>ステップ3:</b> まずは3本の動画を試作してみる。完璧を求めず、まず行動することが成功への近道です。',
        f'<b>ステップ4:</b> {strategy["success_tips"]}この成功ポイントを常に意識して動画を作りましょう。'
    ]
    
    action_style = ParagraphStyle(
        'ActionText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=16,
        textColor=colors.HexColor('#4B5563'),
        spaceBefore=5,
        spaceAfter=5
    )
    
    for point in action_points:
        story.append(Paragraph(point, action_style))
    
    story.append(Spacer(1, 1*cm))
    
    # ========== フッター ==========
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        textColor=colors.HexColor('#9CA3AF'),
        alignment=TA_CENTER
    )
    
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph('このレポートがあなたのYouTube成功への第一歩となることを願っています。', footer_style))
    story.append(Paragraph('© 2025 強み発見ナビ All Rights Reserved', footer_style))
    
    # PDF生成
    doc.build(story)
    buffer.seek(0)
    return buffer
