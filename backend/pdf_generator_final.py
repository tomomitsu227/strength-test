# backend/pdf_generator_final.py
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.colors import black, green, orange, HexColor
import matplotlib.pyplot as plt
import numpy as np
import os

# 日本語フォントのパス（app.pyと同じ階層にあることを想定）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'ipaexg.ttf')
pdfmetrics.registerFont(TTFont('ipaexg', FONT_PATH))

def generate_pdf_report_final(user_id, result_data):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- レーダーチャート画像を生成 ---
    labels = list(result_data['radar_scores'].keys())
    # 日本語ラベルに変換
    jp_labels = ['開放性', '誠実性', '外向性', '協調性', 'ストレス耐性', '情報スタイル', '意思決定', 'モチベーション', '価値追求', '作業スタイル']
    stats = list(result_data['radar_scores'].values())
    
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats = np.concatenate((stats,[stats[0]]))
    angles += angles[:1]
    jp_labels += jp_labels[:1] # 表示用

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, stats, color='red', alpha=0.25)
    ax.plot(angles, stats, color='red', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(jp_labels[:-1], fontname='ipaexg', fontsize=12)
    
    # Matplotlibの画像をメモリに保存
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    plt.close(fig)

    # --- PDFへの描画 ---
    p.setFont('ipaexg', 24)
    p.drawCentredString(width / 2, height - 70, "動画クリエイター特性診断レポート")

    p.setFont('ipaexg', 18)
    p.drawCentredString(width / 2, height - 120, f"あなたは「{result_data.get('type_name', '')}」タイプです")

    # レーダーチャートを中央に配置
    p.drawImage(img_buffer, width/2 - 150, height - 450, width=300, height=300, preserveAspectRatio=True)

    # テキスト描画
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontName = 'ipaexg'
    styleN.fontSize = 11
    styleN.leading = 18

    # 注力すること
    p.setFillColor(green)
    p.rect(70, height - 520, 200, 25, stroke=0, fill=1)
    p.setFillColor(black)
    p.setFont('ipaexg', 14)
    p.drawString(80, height - 515, "注力すること")
    focus_p = Paragraph(result_data.get('focus_on', ''), styleN)
    focus_p.wrapOn(p, width - 140, 400)
    focus_p.drawOn(p, 70, height - 640)
    
    # 手放すこと
    p.setFillColor(orange)
    p.rect(70, height - 680, 200, 25, stroke=0, fill=1)
    p.setFillColor(black)
    p.setFont('ipaexg', 14)
    p.drawString(80, height - 675, "手放すこと")
    let_go_p = Paragraph(result_data.get('let_go_of', ''), styleN)
    let_go_p.wrapOn(p, width - 140, 400)
    let_go_p.drawOn(p, 70, height - 800)

    # 新しいページ
    p.showPage()

    p.setFont('ipaexg', 16)
    p.drawString(70, height - 70, "診断結果の統括 - あなたの本質")
    synthesis_p = Paragraph(result_data.get('synthesis', ''), styleN)
    synthesis_p.wrapOn(p, width - 140, 700)
    synthesis_p.drawOn(p, 70, height - 500)

    p.save()
    buffer.seek(0)
    return buffer