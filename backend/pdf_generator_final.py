# backend/pdf_generator_final.py - サーバー対応版
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.colors import black, green, orange
import matplotlib
# ★★★ 追加：matplotlibに画面を使わないモード(Agg)を指示 ★★★
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

# 日本語フォントのパス
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'ipaexg.ttf')
pdfmetrics.registerFont(TTFont('ipaexg', FONT_PATH))

def generate_pdf_report_final(user_id, result_data):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- レーダーチャート画像を生成 ---
    # ★★★ 修正：radar_scoresのキーを固定の10次元リストに変更 ★★★
    labels = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'StressTolerance', 'InformationStyle', 'DecisionMaking', 'MotivationSource', 'ValuePursuit', 'WorkStyle']
    jp_labels = ['開放性', '誠実性', '外向性', '協調性', 'ストレス耐性', '情報スタイル', '意思決定', 'モチベーション', '価値追求', '作業スタイル']
    
    # labelsの順番でスコアを取得
    stats = [result_data.get('radar_scores', {}).get(label, 0) for label in labels]
    
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats_closed = stats + [stats[0]]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles_closed, stats_closed, color='red', alpha=0.25)
    ax.plot(angles_closed, stats_closed, color='red', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles)
    ax.set_xticklabels(jp_labels, fontname='ipaexg', fontsize=12)
    ax.set_ylim(0, 10) # 0から10のスケールに固定

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0.1)
    img_buffer.seek(0)
    plt.close(fig)

    # --- PDFへの描画 ---
    p.setFont('ipaexg', 24)
    p.drawCentredString(width / 2, height - 70, "動画クリエイター特性診断レポート")
    p.setFont('ipaexg', 18)
    p.drawCentredString(width / 2, height - 120, f"あなたは「{result_data.get('type_name', '')}」タイプです")
    p.drawImage(img_buffer, width/2 - 150, height - 450, width=300, height=300, preserveAspectRatio=True)

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'ipaexg'
    styleN.fontSize = 11
    styleN.leading = 18

    p.setFillColor(green)
    p.rect(70, height - 520, 100, 25, stroke=0, fill=1)
    p.setFillColor(black)
    p.setFont('ipaexg', 14)
    p.drawString(80, height - 515, "注力すること")
    focus_p = Paragraph(result_data.get('focus_on', ''), styleN)
    focus_p.wrapOn(p, width - 140, 400)
    focus_p.drawOn(p, 70, height - 640)
    
    p.setFillColor(orange)
    p.rect(70, height - 680, 100, 25, stroke=0, fill=1)
    p.setFillColor(black)
    p.setFont('ipaexg', 14)
    p.drawString(80, height - 675, "手放すこと")
    let_go_p = Paragraph(result_data.get('let_go_of', ''), styleN)
    let_go_p.wrapOn(p, width - 140, 400)
    let_go_p.drawOn(p, 70, height - 800)

    p.showPage()
    p.setFont('ipaexg', 16)
    p.drawString(70, height - 70, "診断結果の統括 - あなたの本質")
    synthesis_p = Paragraph(result_data.get('synthesis', ''), styleN)
    synthesis_p.wrapOn(p, width - 140, 700)
    synthesis_p.drawOn(p, 70, height - 500)

    p.save()
    buffer.seek(0)
    return buffer