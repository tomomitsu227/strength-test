from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepInFrame
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

PRIMARY_COLOR = colors.HexColor('#EF4444')
TEXT_COLOR = colors.HexColor('#1F2937')
BORDER_COLOR = colors.lightgrey

def create_radar_chart_buffer(scores):
    labels = ['独創性', '計画性', '社交性', '共感力', '精神的安定性', '創作スタイル', '協働適性']
    values = [scores.get(label, 5) for label in labels]
    
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    
    ax.plot(angles, values, 'o-', linewidth=2, color=PRIMARY_COLOR)
    ax.fill(angles, values, alpha=0.25, color=PRIMARY_COLOR)
    
    ax.set_xticks(angles[:-1])
    
    font_prop = fm.FontProperties(fname=FONT_PATH, size=12)
    ax.set_xticklabels(labels, fontproperties=font_prop)
    
    # 最小値を2に設定
    ax.set_ylim(2, 10)
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
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontName=FONT_NAME, fontSize=24, textColor=PRIMARY_COLOR, spaceAfter=12, alignment=TA_CENTER, leading=30)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontName=FONT_NAME, fontSize=16, textColor=TEXT_COLOR, spaceBefore=20, spaceAfter=10, alignment=TA_CENTER, leading=22)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading3'], fontName=FONT_NAME, fontSize=14, textColor=PRIMARY_COLOR, spaceBefore=10, spaceAfter=8, leading=18, alignment=TA_LEFT)
    body_style = ParagraphStyle('CustomBody', parent=styles['BodyText'], fontName=FONT_NAME, fontSize=11, textColor=TEXT_COLOR, leading=18, alignment=TA_LEFT)
    
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
        # 正円を維持するためにwidthとheightを同じ値に設定
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

    # 箇条書きを整形するヘルパー関数
    def create_bullet_list(items, style):
        return [Paragraph(f"・{item}", style) for item in items]

    # 向いていること
    suited_for = data.get('suited_for', [])
    if suited_for:
        content = [Paragraph("向いていること", heading_style)] + create_bullet_list(suited_for, body_style)
        tbl = Table([content], colWidths=[doc.width], style=box_style, spaceAfter=6*mm)
        story.append(tbl)

    # 向いていないこと
    not_suited_for = data.get('not_suited_for', [])
    if not_suited_for:
        # 文言を修正
        content = [Paragraph("向いていないこと", heading_style)] + create_bullet_list(not_suited_for, body_style)
        tbl = Table([content], colWidths=[doc.width], style=box_style, spaceAfter=6*mm)
        story.append(tbl)
    
    # 総合分析
    synthesis = data.get('synthesis', '')
    if synthesis:
        content = [
            Paragraph("分析結果のまとめ", heading_style),
            Paragraph(synthesis.replace('\n', '<br/>'), body_style)
        ]
        tbl = Table([content], colWidths=[doc.width], style=box_style)
        story.append(tbl)
    
    story.append(Spacer(1, 20*mm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontName=FONT_NAME, fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Paragraph("本レポートは、回答に基づいた傾向を示すものであり、能力を断定するものではありません。", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer