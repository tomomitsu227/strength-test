# backend/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.spider import SpiderChart
import io
import matplotlib.pyplot as plt
import numpy as np

# 日本語フォント設定（ipaexg.ttfを使用）
try:
    pdfmetrics.registerFont(TTFont('Japanese', 'ipaexg.ttf'))
    FONT_NAME = 'Japanese'
except:
    FONT_NAME = 'Helvetica'  # フォールバック

def create_radar_chart(category_scores, filename='radar.png'):
    """レーダーチャートを生成"""
    categories = list(category_scores.keys())
    values = list(category_scores.values())
    
    # データ数に合わせて角度を計算
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]  # 閉じるために最初の値を追加
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values, 'o-', linewidth=2, color='#4A90E2')
    ax.fill(angles, values, alpha=0.25, color='#4A90E2')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.grid(True)
    
    # 画像として保存
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

def create_domain_bar_chart(domain_scores):
    """ドメイン別スコアの棒グラフを生成"""
    domains = [v['name'] for v in domain_scores.values()]
    raw_scores = [v['raw_score'] for v in domain_scores.values()]
    weighted_scores = [v['weighted_score'] for v in domain_scores.values()]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(domains))
    width = 0.35
    
    ax.bar(x - width/2, raw_scores, width, label='生スコア', color='#95C8F0')
    ax.bar(x + width/2, weighted_scores, width, label='重み付けスコア', color='#4A90E2')
    
    ax.set_xlabel('ドメイン')
    ax.set_ylabel('スコア')
    ax.set_title('ドメイン別スコア比較')
    ax.set_xticks(x)
    ax.set_xticklabels(domains, rotation=15, ha='right')
    ax.legend()
    ax.set_ylim(0, 5)
    ax.grid(axis='y', alpha=0.3)
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

def generate_pdf_report(user_id, scores, questions_data):
    """PDF診断レポートを生成"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # スタイル設定
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=16
    )
    
    # タイトル
    story.append(Paragraph('強み診断レポート', title_style))
    story.append(Paragraph(f'診断ID: {user_id[:8]}', normal_style))
    story.append(Spacer(1, 20))
    
    # ドメイン別スコア
    story.append(Paragraph('1. ドメイン別総合スコア', heading_style))
    
    domain_scores = scores['domain_scores']
    table_data = [['ドメイン', '生スコア', '重み付けスコア', 'エビデンス強度']]
    
    for domain, data in domain_scores.items():
        table_data.append([
            data['name'],
            str(data['raw_score']),
            str(data['weighted_score']),
            f"{int(data['evidence_weight'] * 100)}%"
        ])
    
    table = Table(table_data, colWidths=[4*cm, 3*cm, 4*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # 棒グラフ
    bar_chart = create_domain_bar_chart(domain_scores)
    img = Image(bar_chart, width=14*cm, height=8*cm)
    story.append(img)
    story.append(Spacer(1, 20))
    
    # レーダーチャート
    story.append(Paragraph('2. カテゴリ別詳細分析', heading_style))
    category_scores = scores['category_scores']
    radar_chart = create_radar_chart(category_scores)
    img_radar = Image(radar_chart, width=12*cm, height=12*cm)
    story.append(img_radar)
    story.append(Spacer(1, 20))
    
    # 診断結果の解説
    story.append(Paragraph('3. 診断結果の解説', heading_style))
    
    # 最も高いドメインを特定
    top_domain = max(domain_scores.items(), key=lambda x: x[1]['weighted_score'])
    story.append(Paragraph(
        f"あなたの最も強いドメインは「{top_domain[1]['name']}」です。",
        normal_style
    ))
    story.append(Paragraph(
        f"スコア: {top_domain[1]['weighted_score']} / エビデンス強度: {int(top_domain[1]['evidence_weight']*100)}%",
        normal_style
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        top_domain[1]['description'],
        normal_style
    ))
    
    # PDF生成
    doc.build(story)
    buffer.seek(0)
    return buffer
