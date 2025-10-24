# backend/pdf_generator_final.py - 文字化け完全解決＆シンプル化版

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ===== 日本語フォントの登録（ipaexg.ttf強制指定） =====
FONT_PATH = "ipaexg.ttf"
pdfmetrics.registerFont(TTFont('IPAexGothic', FONT_PATH))
FONT_NAME = 'IPAexGothic'

# カラー定義
PRIMARY_COLOR = colors.HexColor('#EF4444')
SECONDARY_COLOR = colors.HexColor('#10B981')
TEXT_COLOR = colors.HexColor('#1F2937')
BORDER_COLOR = colors.HexColor('#E5E7EB')


def create_radar_chart(scores, filename='/tmp/radar_chart.png'):
    """
    レーダーチャートを生成（7次元）
    """
    # 日本語ラベル
    labels = ['独創性', '計画性', '社交性', '共感力', '精神的安定性', '創作スタイル', '協働適性']
    
    # スコアの取得
    values = [
        scores.get('独創性', 5),
        scores.get('計画性', 5),
        scores.get('社交性', 5),
        scores.get('共感力', 5),
        scores.get('精神的安定性', 5),
        scores.get('創作スタイル', 5),
        scores.get('協働適性', 5)
    ]
    
    # 角度の計算
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    # グラフの作成
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # データのプロット
    ax.plot(angles, values, 'o-', linewidth=2, color='#EF4444', label='あなたのスコア')
    ax.fill(angles, values, alpha=0.25, color='#EF4444')
    
    # 軸の設定
    ax.set_xticks(angles[:-1])
    
    # 日本語フォントの設定
    font_prop = fm.FontProperties(fname=FONT_PATH)
    ax.set_xticklabels(labels, fontproperties=font_prop, size=11)
    
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], size=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # 背景色
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')
    
    # 保存
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return filename


def generate_pdf_report_final(user_name, data):
    """
    診断結果のPDFレポートを生成
    """
    buffer = BytesIO()
    
    # ドキュメントの作成
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    # スタイルの定義（すべてIPAexGothicを使用）
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        alignment=TA_CENTER,
        leading=30
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=16,
        textColor=TEXT_COLOR,
        spaceBefore=20,
        spaceAfter=10,
        leading=22
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading3'],
        fontName=FONT_NAME,
        fontSize=14,
        textColor=PRIMARY_COLOR,
        spaceBefore=15,
        spaceAfter=8,
        leading=18
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=FONT_NAME,
        fontSize=11,
        textColor=TEXT_COLOR,
        leading=18,
        spaceAfter=10
    )
    
    box_style = ParagraphStyle(
        'BoxText',
        parent=styles['BodyText'],
        fontName=FONT_NAME,
        fontSize=10,
        textColor=TEXT_COLOR,
        leading=16,
        leftIndent=10,
        rightIndent=10
    )
    
    # コンテンツの構築
    story = []
    
    # ===== タイトルページ =====
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("動画クリエイター特性診断", title_style))
    story.append(Spacer(1, 10*mm))
    
    # メインコア名
    main_core = data.get('main_core_name', 'クリエイター')
    story.append(Paragraph(f"あなたのコア: <b>{main_core}</b>", subtitle_style))
    
    # サブコアタイトル
    sub_core = data.get('sub_core_title', '')
    if sub_core:
        story.append(Paragraph(f"サブタイプ: {sub_core}", body_style))
    
    story.append(Spacer(1, 20*mm))
    
    # ===== レーダーチャート =====
    story.append(Paragraph("あなたの特性プロファイル", heading_style))
    
    radar_scores = data.get('radar_scores', {})
    if radar_scores:
        radar_file = create_radar_chart(radar_scores)
        img = RLImage(radar_file, width=140*mm, height=140*mm)
        story.append(img)
        story.append(Spacer(1, 10*mm))
    
    story.append(PageBreak())
    
    # ===== 向いていること =====
    suited_for = data.get('suited_for', '')
    if suited_for:
        story.append(Paragraph("あなたに向いていること", heading_style))
        
        suited_table = Table(
            [[Paragraph(suited_for, box_style)]],
            colWidths=[170*mm]
        )
        suited_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFDF5')),
            ('BOX', (0, 0), (-1, -1), 3, SECONDARY_COLOR),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(suited_table)
        story.append(Spacer(1, 10*mm))
    
    # ===== 意識すると良い点 =====
    not_suited_for = data.get('not_suited_for', '')
    if not_suited_for:
        story.append(Paragraph("意識すると良い点", heading_style))
        
        not_suited_table = Table(
            [[Paragraph(not_suited_for, box_style)]],
            colWidths=[170*mm]
        )
        not_suited_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF2F2')),
            ('BOX', (0, 0), (-1, -1), 3, PRIMARY_COLOR),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(not_suited_table)
        story.append(Spacer(1, 10*mm))
    
    # ===== 分析結果まとめ =====
    synthesis = data.get('synthesis', '')
    if synthesis:
        story.append(Paragraph("総合分析", heading_style))
        story.append(Paragraph(synthesis, body_style))
        story.append(Spacer(1, 10*mm))
    
    # ===== フッター =====
    story.append(Spacer(1, 20*mm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("動画クリエイター特性診断 - あなたの「核」を発見する", footer_style))
    
    # PDFの生成
    doc.build(story)
    buffer.seek(0)
    
    return buffer


if __name__ == '__main__':
    # テスト用
    test_data = {
        'main_core_name': '孤高のアーティスト',
        'sub_core_title': '緻密な世界観の構築者',
        'suited_for': 'テスト向いていること',
        'not_suited_for': 'テスト意識すると良い点',
        'synthesis': 'テスト総合分析',
        'radar_scores': {
            '独創性': 8.5,
            '計画性': 7.0,
            '社交性': 2.5,
            '共感力': 5.0,
            '精神的安定性': 5.5,
            '創作スタイル': 8.0,
            '協働適性': 3.5
        }
    }
    
    pdf_buffer = generate_pdf_report_final('テスト', test_data)
    with open('test_report.pdf', 'wb') as f:
        f.write(pdf_buffer.getvalue())
    print("テストPDF生成完了")
