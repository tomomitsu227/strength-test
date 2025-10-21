# backend/pdf_generator_cross_platform.py - クロスプラットフォーム対応絵文字版
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.spider import SpiderChart
from PIL import Image, ImageDraw, ImageFont
import io
import os
import platform

# 日本語フォント設定
try:
    pdfmetrics.registerFont(TTFont('Japanese', 'ipaexg.ttf'))
    FONT_NAME = 'Japanese'
except:
    try:
        pdfmetrics.registerFont(TTFont('Japanese', 'C:/Windows/Fonts/msgothic.ttc'))
        FONT_NAME = 'Japanese'
    except:
        try:
            pdfmetrics.registerFont(TTFont('Japanese', 'C:/Windows/Fonts/meiryo.ttc'))
            FONT_NAME = 'Japanese'
        except:
            FONT_NAME = 'Helvetica'

def get_emoji_font_path():
    """
    OSに応じた絵文字フォントパスを取得（クロスプラットフォーム対応）
    """
    system = platform.system()
    
    # 候補フォントパスのリスト
    font_paths = []
    
    if system == 'Windows':
        font_paths = [
            'C:/Windows/Fonts/seguiemj.ttf',
            'seguiemj.ttf',
        ]
    elif system == 'Darwin':  # Mac
        font_paths = [
            '/System/Library/Fonts/Apple Color Emoji.ttc',
            '/Library/Fonts/Apple Color Emoji.ttc',
            '/System/Library/Fonts/AppleColorEmoji.ttf',
        ]
    elif system == 'Linux':
        font_paths = [
            '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
            '/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf',
            '/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf',
        ]
    
    # 存在するフォントを返す
    for path in font_paths:
        if os.path.exists(path):
            return path
    
    # フォールバック：システムフォント
    return 'arial.ttf' if system == 'Windows' else None

def emoji_to_image(emoji_char, size=(150, 150)):
    """
    絵文字をPNG画像に変換（全OS対応）
    """
    try:
        # 透明背景の画像を作成
        img = Image.new('RGBA', size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # OSに応じた絵文字フォントを取得
        font_path = get_emoji_font_path()
        
        if font_path and os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size[0] - 30)
            except Exception as e:
                print(f"フォント読み込みエラー: {e}")
                # フォールバック
                font = ImageFont.load_default()
        else:
            print("絵文字フォントが見つかりません。デフォルトフォントを使用します。")
            font = ImageFont.load_default()
        
        # 絵文字を描画（中央配置）
        try:
            bbox = draw.textbbox((0, 0), emoji_char, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2 - 10
            
            draw.text((x, y), emoji_char, font=font, embedded_color=True)
        except:
            # フォールバック：中央に大きく描画
            draw.text((size[0]//4, size[1]//4), emoji_char, font=font, fill=(0, 0, 0, 255))
        
        # BytesIOに保存
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"絵文字画像化エラー: {e}")
        # エラー時：白い画像を返す
        img = Image.new('RGBA', size, (255, 255, 255, 0))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

def create_section_header(title, bg_color='#FEF2F2', border_color='#EF4444'):
    """セクションヘッダー"""
    drawing = Drawing(480, 45)
    
    rect = Rect(0, 5, 480, 35)
    rect.fillColor = colors.HexColor(bg_color)
    rect.strokeColor = colors.HexColor(border_color)
    rect.strokeWidth = 2.5
    drawing.add(rect)
    
    from reportlab.graphics.shapes import String
    title_text = String(15, 18, title, textAnchor='start')
    title_text.fontName = FONT_NAME
    title_text.fontSize = 14
    title_text.fillColor = colors.HexColor(border_color)
    drawing.add(title_text)
    
    return drawing

def create_radar_chart(radar_scores):
    """レーダーチャート"""
    drawing = Drawing(360, 360)
    spider = SpiderChart()
    spider.x = 30
    spider.y = 30
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
    
    spider.labels = ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']
    spider.strands[0].fillColor = colors.HexColor('#EF4444')
    spider.strands[0].strokeColor = colors.HexColor('#DC2626')
    spider.strands[0].strokeWidth = 2.5
    spider.labelFontSize = 11
    spider.labelFontName = FONT_NAME
    
    drawing.add(spider)
    return drawing

def generate_pdf_report(user_id, result):
    """
    クロスプラットフォーム対応PDF生成
    Windows / Mac / Linux / Android / iOS全対応
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=15*mm,
        leftMargin=18*mm,
        rightMargin=18*mm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # スタイル定義
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=24,
        textColor=colors.HexColor('#DC2626'),
        spaceAfter=8,
        alignment=TA_CENTER,
        leading=30
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontName=FONT_NAME,
        fontSize=12,
        textColor=colors.HexColor('#6B7280'),
        spaceAfter=18,
        alignment=TA_CENTER,
        leading=16
    )
    
    body_style = ParagraphStyle(
        'Body',
        fontName=FONT_NAME,
        fontSize=10,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#374151')
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=body_style,
        fontName=FONT_NAME,
        fontSize=11
    )
    
    # ========== カバーページ ==========
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph('YouTube強み診断レポート', title_style))
    story.append(Paragraph('あなたの才能を「稼げる動画」に変える', subtitle_style))
    story.append(Spacer(1, 12*mm))
    
    # 動物絵文字を画像として挿入
    try:
        emoji_img_buffer = emoji_to_image(result["animal_icon"], size=(180, 180))
        emoji_img = RLImage(emoji_img_buffer, width=40*mm, height=40*mm)
        story.append(emoji_img)
    except Exception as e:
        print(f"動物アイコン挿入エラー: {e}")
    
    story.append(Spacer(1, 8*mm))
    
    # タイプ名
    type_style = ParagraphStyle(
        'TypeName',
        fontName=FONT_NAME,
        fontSize=20,
        textColor=colors.HexColor('#DC2626'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    story.append(Paragraph(f'あなたは「{result["animal_name"]}」タイプ', type_style))
    
    # 説明
    desc_style = ParagraphStyle(
        'Description',
        fontName=FONT_NAME,
        fontSize=10.5,
        alignment=TA_CENTER,
        leading=16,
        textColor=colors.HexColor('#4B5563')
    )
    story.append(Paragraph(result["animal_description"], desc_style))
    story.append(Spacer(1, 8*mm))
    
    # ID
    id_style = ParagraphStyle(
        'ID',
        fontName=FONT_NAME,
        fontSize=8,
        textColor=colors.HexColor('#9CA3AF'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(f'診断ID: {user_id[:12]}', id_style))
    
    story.append(PageBreak())
    
    # ========== 性格分析 ==========
    story.append(Spacer(1, 8*mm))
    
    # アイコン
    try:
        icon1_buffer = emoji_to_image('📊', size=(70, 70))
        icon1 = RLImage(icon1_buffer, width=14*mm, height=14*mm)
        story.append(icon1)
    except:
        pass
    
    header1 = create_section_header('あなたの性格分析')
    story.append(header1)
    story.append(Spacer(1, 8*mm))
    
    try:
        radar = create_radar_chart(result.get('radar_scores', {}))
        story.append(radar)
    except:
        story.append(Paragraph('※チャート生成エラー', body_style))
    
    story.append(Spacer(1, 10*mm))
    
    # ========== YouTube戦略 ==========
    try:
        icon2_buffer = emoji_to_image('🎯', size=(70, 70))
        icon2 = RLImage(icon2_buffer, width=14*mm, height=14*mm)
        story.append(icon2)
    except:
        pass
    
    header2 = create_section_header('あなたに最適なYouTube戦略', '#E0F2FE', '#0EA5E9')
    story.append(header2)
    story.append(Spacer(1, 8*mm))
    
    strategy = result['youtube_strategy']
    
    strategy_data = [
        [Paragraph('<b>おすすめジャンル</b>', bold_style), 
         Paragraph(strategy['genre'], body_style)],
        [Paragraph('<b>コンテンツの方向性</b>', bold_style), 
         Paragraph(strategy['direction'], body_style)],
        [Paragraph('<b>成功のポイント</b>', bold_style), 
         Paragraph(strategy['success_tips'], body_style)]
    ]
    
    strategy_table = Table(strategy_data, colWidths=[48*mm, 120*mm])
    strategy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#DBEAFE')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#0EA5E9')),
    ]))
    
    story.append(strategy_table)
    story.append(Spacer(1, 10*mm))
    
    # ========== 総合評価 ==========
    try:
        icon3_buffer = emoji_to_image('📋', size=(70, 70))
        icon3 = RLImage(icon3_buffer, width=14*mm, height=14*mm)
        story.append(icon3)
    except:
        pass
    
    header3 = create_section_header('診断結果の総合評価', '#FEF3C7', '#F59E0B')
    story.append(header3)
    story.append(Spacer(1, 8*mm))
    
    summary_para = Paragraph(result.get('overall_summary', ''), body_style)
    summary_table = Table([[summary_para]], colWidths=[168*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#F59E0B')),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 10*mm))
    
    # ========== アクションプラン ==========
    try:
        icon4_buffer = emoji_to_image('✅', size=(70, 70))
        icon4 = RLImage(icon4_buffer, width=14*mm, height=14*mm)
        story.append(icon4)
    except:
        pass
    
    header4 = create_section_header('今日から始める具体的アクション', '#E0E7FF', '#6366F1')
    story.append(header4)
    story.append(Spacer(1, 8*mm))
    
    action_points = [
        f'{strategy["genre"]}のジャンルで、既存の人気チャンネルを3つ以上リサーチしましょう。',
        f'{strategy["direction"]} この方向性で、自分なりの切り口を考えてみましょう。',
        'まずは3本の動画を試作してみる。完璧を求めず、まず行動することが成功への近道です。',
        f'{strategy["success_tips"]} この成功ポイントを常に意識して動画を作りましょう。'
    ]
    
    for i, point in enumerate(action_points, 1):
        step_data = [[Paragraph(f'<b>STEP {i}</b>', bold_style), Paragraph(point, body_style)]]
        step_table = Table(step_data, colWidths=[22*mm, 146*mm])
        step_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#C7D2FE')),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor('#6366F1')),
        ]))
        story.append(step_table)
        story.append(Spacer(1, 3*mm))
    
    story.append(Spacer(1, 12*mm))
    
    # ========== フッター ==========
    footer = ParagraphStyle(
        'Footer',
        fontName=FONT_NAME,
        fontSize=9,
        textColor=colors.HexColor('#9CA3AF'),
        alignment=TA_CENTER,
        leading=13
    )
    
    story.append(Paragraph('このレポートがあなたのYouTube成功への第一歩となることを願っています。', footer))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('© 2025 強み発見ナビ All Rights Reserved', footer))
    
    # PDF生成
    doc.build(story)
    buffer.seek(0)
    return buffer
