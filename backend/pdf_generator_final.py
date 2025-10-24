# backend/pdf_generator_final.py - さらに堅牢性を高めた改善版

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os # osモジュールをインポート

# ===== 日本語フォントの登録（ipaexg.ttf強制指定） =====
# スクリプトの場所を基準に絶対パスを生成
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "ipaexg.ttf")

pdfmetrics.registerFont(TTFont('IPAexGothic', FONT_PATH))
FONT_NAME = 'IPAexGothic'

# カラー定義
PRIMARY_COLOR = colors.HexColor('#EF4444')
SECONDARY_COLOR = colors.HexColor('#10B981')
TEXT_COLOR = colors.HexColor('#1F2937')


def create_radar_chart_buffer(scores):
    """
    レーダーチャートを生成し、ファイルではなくBytesIOバッファを返す
    """
    labels = ['独創性', '計画性', '社交性', '共感力', '精神的安定性', '創作スタイル', '協働適性']
    values = [scores.get(label, 5) for label in labels]
    
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    
    ax.plot(angles, values, 'o-', linewidth=2, color='#EF4444')
    ax.fill(angles, values, alpha=0.25, color='#EF4444')
    
    ax.set_xticks(angles[:-1])
    
    font_prop = fm.FontProperties(fname=FONT_PATH, size=12)
    ax.set_xticklabels(labels, fontproperties=font_prop)
    
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], size=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # メモリ上のバッファを作成
    img_buffer = BytesIO()
    plt.tight_layout()
    # ファイルではなくバッファに保存
    plt.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
    plt.close(fig) # メモリリークを防ぐために明示的に閉じる
    
    img_buffer.seek(0)
    return img_buffer


def generate_pdf_report_final(user_name, data):
    """
    診断結果のPDFレポートを生成
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    
    # スタイルの定義
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontName=FONT_NAME, fontSize=24, textColor=PRIMARY_COLOR, spaceAfter=12, alignment=TA_CENTER, leading=30)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontName=FONT_NAME, fontSize=16, textColor=TEXT_COLOR, spaceBefore=20, spaceAfter=10, leading=22)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading3'], fontName=FONT_NAME, fontSize=14, textColor=PRIMARY_COLOR, spaceBefore=15, spaceAfter=8, leading=18)
    body_style = ParagraphStyle('CustomBody', parent=styles['BodyText'], fontName=FONT_NAME, fontSize=11, textColor=TEXT_COLOR, leading=18, spaceAfter=10, spaceBefore=10)
    box_style = ParagraphStyle('BoxText', parent=styles['BodyText'], fontName=FONT_NAME, fontSize=10, textColor=TEXT_COLOR, leading=16)

    story = []
    
    # ===== タイトルページ =====
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("動画クリエイター特性診断レポート", title_style))
    story.append(Spacer(1, 10*mm))
    main_core = data.get('main_core_name', 'クリエイター')
    story.append(Paragraph(f"あなたのタイプ: <b>{main_core}</b>", subtitle_style))
    sub_core = data.get('sub_core_title', '')
    if sub_core:
        story.append(Paragraph(sub_core, body_style))
    
    story.append(Spacer(1, 15*mm))
    
    # ===== レーダーチャート =====
    story.append(Paragraph("あなたの特性プロファイル", heading_style))
    
    radar_scores = data.get('radar_scores', {})
    if radar_scores:
        # バッファから直接画像を読み込む
        radar_buffer = create_radar_chart_buffer(radar_scores)
        img = RLImage(radar_buffer, width=150*mm, height=150*mm)
        story.append(img)
    
    story.append(PageBreak())
    
    # ===== 詳細分析 =====
    story.append(Paragraph("詳細分析", title_style))
    story.append(Spacer(1, 5*mm))

    # 向いていること
    suited_for = data.get('suited_for', '')
    if suited_for:
        story.append(Paragraph("あなたに向いていること", heading_style))
        story.append(Paragraph(suited_for.replace('\n', '<br/>'), body_style))
    
    # 意識すると良い点
    not_suited_for = data.get('not_suited_for', '')
    if not_suited_for:
        story.append(Paragraph("意識すると良い点", heading_style))
        story.append(Paragraph(not_suited_for.replace('\n', '<br/>'), body_style))
    
    # 総合分析
    synthesis = data.get('synthesis', '')
    if synthesis:
        story.append(Paragraph("分析結果のまとめ", heading_style))
        story.append(Paragraph(synthesis.replace('\n', '<br/>'), body_style))
    
    # フッター
    story.append(Spacer(1, 20*mm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontName=FONT_NAME, fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Paragraph("本レポートは、回答に基づいた傾向を示すものであり、能力を断定するものではありません。", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer

if __name__ == '__main__':
    test_data = {
        'main_core_name': '孤高のアーティスト',
        'sub_core_title': '緻密な世界観の構築者',
        'suited_for': 'テストです。\n改行もテストします。',
        'not_suited_for': 'テストです。',
        'synthesis': 'テストです。長文のテストをここで行います。回り込みやレイアウトが崩れないかを確認するためのテキストです。',
        'radar_scores': {
            '独創性': 8.5, '計画性': 7.0, '社交性': 2.5, '共感力': 5.0,
            '精神的安定性': 5.5, '創作スタイル': 8.0, '協働適性': 3.5
        }
    }
    
    pdf_buffer = generate_pdf_report_final('テスト', test_data)
    with open('test_report_improved.pdf', 'wb') as f:
        f.write(pdf_buffer.getvalue())
    print("改善版のテストPDFを生成しました: test_report_improved.pdf")