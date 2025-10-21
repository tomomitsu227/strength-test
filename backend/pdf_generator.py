# backend/pdf_generator.py (日本語対応・改善版)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import matplotlib
matplotlib.use('Agg')  # GUIなし環境用
import matplotlib.pyplot as plt
import numpy as np

# 日本語フォント設定
try:
    pdfmetrics.registerFont(TTFont('Japanese', 'ipaexg.ttf'))
    FONT_NAME = 'Japanese'
except:
    try:
        # Windows標準の日本語フォントを試す
        pdfmetrics.registerFont(TTFont('Japanese', 'C:/Windows/Fonts/msgothic.ttc'))
        FONT_NAME = 'Japanese'
    except:
        FONT_NAME = 'Helvetica'  # フォールバック

# Matplotlibの日本語フォント設定
try:
    plt.rcParams['font.family'] = 'MS Gothic'
except:
    try:
        plt.rcParams['font.family'] = 'IPAexGothic'
    except:
        pass

def create_radar_chart(category_scores):
    """レーダーチャートを生成"""
    categories = list(category_scores.keys())
    values = list(category_scores.values())
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values_plot = values + values[:1]
    angles_plot = angles + angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    ax.plot(angles_plot, values_plot, 'o-', linewidth=2, color='#4A90E2')
    ax.fill(angles_plot, values_plot, alpha=0.25, color='#4A90E2')
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.grid(True)
    ax.set_title('カテゴリ別詳細スコア', pad=20, fontsize=14)
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

def create_domain_bar_chart(domain_scores):
    """ドメイン別スコアの棒グラフを生成"""
    domains = [v['name'] for v in domain_scores.values()]
    weighted_scores = [v['weighted_score'] for v in domain_scores.values()]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(domains, weighted_scores, color='#4A90E2')
    
    ax.set_xlabel('スコア', fontsize=12)
    ax.set_title('領域別総合スコア', fontsize=14, pad=15)
    ax.set_xlim(0, 5)
    ax.grid(axis='x', alpha=0.3)
    
    # 値ラベル追加
    for i, (bar, score) in enumerate(zip(bars, weighted_scores)):
        ax.text(score + 0.1, i, f'{score:.1f}', va='center', fontsize=11)
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

def generate_pdf_report(user_id, scores, questions_data):
    """PDF診断レポートを生成（日本語対応）"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    story = []
    
    # スタイル設定
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=18,
        alignment=TA_LEFT
    )
    
    # タイトル
    story.append(Paragraph('あなたの強み診断レポート', title_style))
    story.append(Paragraph(f'診断ID: {user_id[:8]}', normal_style))
    story.append(Spacer(1, 20))
    
    # 総合評価
    story.append(Paragraph('総合評価', heading_style))
    domain_scores = scores['domain_scores']
    
    # 最も高いドメインを特定
    top_domain = max(domain_scores.items(), key=lambda x: x[1]['weighted_score'])
    story.append(Paragraph(
        f"あなたの最も強い領域は「<b>{top_domain[1]['name']}</b>」です。",
        normal_style
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"スコア: {top_domain[1]['weighted_score']:.1f} / 5.0",
        normal_style
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        top_domain[1]['description'],
        normal_style
    ))
    story.append(Spacer(1, 25))
    
    # 棒グラフ
    story.append(Paragraph('1. 領域別スコア', heading_style))
    bar_chart = create_domain_bar_chart(domain_scores)
    img = Image(bar_chart, width=14*cm, height=8*cm)
    story.append(img)
    story.append(Spacer(1, 25))
    
    # スコア詳細表
    story.append(Paragraph('2. 詳細スコア', heading_style))
    table_data = [['領域', 'スコア', '説明']]
    
    for domain, data in domain_scores.items():
        # 説明文を短縮
        desc_short = data['description'][:50] + '...' if len(data['description']) > 50 else data['description']
        table_data.append([
            Paragraph(data['name'], normal_style),
            f"{data['weighted_score']:.1f}",
            Paragraph(desc_short, normal_style)
        ])
    
    table = Table(table_data, colWidths=[4*cm, 2*cm, 8*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table)
    story.append(Spacer(1, 25))
    
    # レーダーチャート
    story.append(Paragraph('3. カテゴリ別詳細分析', heading_style))
    category_scores = scores['category_scores']
    radar_chart = create_radar_chart(category_scores)
    img_radar = Image(radar_chart, width=12*cm, height=12*cm)
    story.append(img_radar)
    story.append(Spacer(1, 25))
    
    # まとめ
    story.append(Paragraph('4. まとめ', heading_style))
    story.append(Paragraph(
        'この診断は複数の心理学理論に基づき、あなたの強みと特性を多角的に分析しています。'
        '自分の強みを理解し、日々の生活や仕事に活かしていきましょう。',
        normal_style
    ))
    
    # PDF生成
    doc.build(story)
    buffer.seek(0)
    return buffer
