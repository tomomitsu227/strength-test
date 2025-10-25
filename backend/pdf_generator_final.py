from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "ipaexg.ttf")

pdfmetrics.registerFont(TTFont('IPAexGothic', FONT_PATH))
FONT_NAME = 'IPAexGothic'

PRIMARY_COLOR_HEX = '#EF4444'
TEXT_COLOR_HEX = '#1F2937'
BORDER_COLOR = colors.lightgrey

def create_radar_chart_buffer(scores):
    labels = ['独創性', '計画性', '社交性', '共感力', '精神的安定性', '創作スタイル', '協働適性']
    values = [scores.get(label, 0) for label in labels] # デフォルトを0に変更
    
    # 描画する最小値は0だが、エラー対策で内部的に微小な値を加えることも考慮
    # ただし、ylim(0, 10)で十分な場合が多い
    
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values_to_plot = np.concatenate((values, [values[0]]))
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    
    ax.plot(angles, values_to_plot, 'o-', linewidth=2, color=PRIMARY_COLOR_HEX)
    ax.fill(angles, values_to_plot, alpha=0.25, color=PRIMARY_COLOR_HEX)
    
    ax.set_xticks(angles[:-1])
    
    font_prop = fm.FontProperties(fname=FONT_PATH, size=12)
    ax.set_xticklabels(labels, fontproperties=font_prop)
    
    ax.set_ylim(0, 10) # 最小値を0に設定
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], size=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    img_buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    img_buffer.seek(0)
    return img_buffer

def generate_pdf_report_final(user_name, data):
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontName=FONT_NAME, fontSize=24, textColor=colors.HexColor(PRIMARY_COLOR_HEX), spaceAfter=12, alignment=TA_CENTER, leading=30)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontName=FONT_NAME, fontSize=16, textColor=colors.HexColor(TEXT_COLOR_HEX), spaceBefore=20, spaceAfter=10, alignment=TA_CENTER, leading=22)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading3'], fontName=FONT_NAME, fontSize=14, textColor=colors.HexColor(PRIMARY_COLOR_HEX), spaceBefore=10, spaceAfter=8, leading=18, alignment=TA_LEFT)
    body_style = ParagraphStyle('CustomBody', parent=styles['BodyText'], fontName=FONT_NAME, fontSize=11, textColor=colors.HexColor(TEXT_COLOR_HEX), leading=18, alignment=TA_LEFT)
    
    story = []
    
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("動画クリエイター特性診断レポート", title_style))
    story.append(Spacer(1, 10*mm))
    main_core = data.get('main_core_name', 'クリエイター')
    story.append(Paragraph(f"あなたのタイプ: <b>{main_core}</b>", subtitle_style))
    sub_core = data.get('sub_core_title', '')
    if sub_core:
        body_style_center = body_style.clone('BodyCenter')
        body_style_center.alignment = TA_CENTER
        story.append(Paragraph(sub_core, body_style_center))
    
    story.append(Spacer(1, 15*mm))
    
    heading_style_center = heading_style.clone('HeadingCenter')
    heading_style_center.alignment = TA_CENTER
    story.append(Paragraph("あなたの特性プロファイル", heading_style_center))
    
    radar_scores = data.get('radar_scores', {})
    if radar_scores:
        radar_buffer = create_radar_chart_buffer(radar_scores)
        img = RLImage(radar_buffer, width=120*mm, height=120*mm)
        story.append(img)
    
    story.append(PageBreak())
    
    story.append(Paragraph("詳細分析", title_style))
    story.append(Spacer(1, 8*mm))

    box_padding = 5 * mm
    box_style = TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('LEFTPADDING', (0, 0), (-1, -1), box_padding),
        ('RIGHTPADDING', (0, 0), (-1, -1), box_padding),
        ('TOPPADDING', (0, 0), (-1, -1), box_padding),
        ('BOTTOMPADDING', (0, 0), (-1, -1), box_padding),
    ])

    def create_bullet_list(items, style):
        return [Paragraph(f"・{item}", style) for item in items]

    def build_card(title, items):
        if not items: return None
        content = [Paragraph(title, heading_style)] + create_bullet_list(items, body_style)
        tbl_content = [ [c] for c in content ]
        tbl = Table(tbl_content, colWidths=[doc.width - (box_padding * 2)], style=box_style, spaceAfter=6*mm)
        return tbl

    suited_card = build_card("向いていること", data.get('suited_for', []))
    if suited_card: story.append(suited_card)

    not_suited_card = build_card("向いていないこと", data.get('not_suited_for', []))
    if not_suited_card: story.append(not_suited_card)
    
    synthesis = data.get('synthesis', '')
    if synthesis:
        content = [Paragraph("分析結果のまとめ", heading_style), Paragraph(synthesis.replace('\n', '<br/>'), body_style)]
        tbl_content = [ [c] for c in content ]
        tbl = Table(tbl_content, colWidths=[doc.width - (box_padding * 2)], style=box_style)
        story.append(tbl)
    
    story.append(Spacer(1, 20*mm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontName=FONT_NAME, fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Paragraph("本レポートは、回答に基づいた傾向を示すものであり、能力を断定するものではありません。", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer