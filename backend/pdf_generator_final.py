# backend/pdf_generator_final.py - 最終レイアウト修正版
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.colors import black, green, orange, HexColor
from reportlab.lib.utils import ImageReader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import os

# 日本語フォントのパス
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'ipaexg.ttf')
pdfmetrics.registerFont(TTFont('ipaexg', FONT_PATH))
jp_font = FontProperties(fname=FONT_PATH)

def generate_pdf_report_final(user_id, result_data):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- スタイル定義 ---
    styles = getSampleStyleSheet()
    styleN = ParagraphStyle(name='Normal', fontName='ipaexg', fontSize=11, leading=18)
    
    # --- ヘッダー ---
    p.setFont('ipaexg', 18)
    p.drawCentredString(width / 2, height - 70, f"あなたは「{result_data.get('main_core_name', '')}」")
    p.setFont('ipaexg', 12)
    p.setFillColor(HexColor('#555555'))
    p.drawCentredString(width / 2, height - 95, result_data.get('sub_core_title', ''))

    # --- レーダーチャート ---
    radar_labels = ['開放性', '誠実性', '外向性', '協調性', 'ストレス耐性', '思考スタイル', '判断基準', 'モチベーション源泉', '創作スタンス', '作業環境']
    stats = [result_data.get('radar_scores', {}).get(label, 0) for label in radarLabels]
    
    angles = np.linspace(0, 2 * np.pi, len(radar_labels), endpoint=False).tolist()
    stats_closed = stats + [stats[0]]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles_closed, stats_closed, color='red', alpha=0.25)
    ax.plot(angles_closed, stats_closed, color='red', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles)
    ax.set_xticklabels(radar_labels, fontproperties=jp_font, fontsize=12)
    ax.set_ylim(0, 10)

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0.1)
    img_buffer.seek(0)
    plt.close(fig)
    
    p.drawImage(ImageReader(img_buffer), width/2 - 180, height - 480, width=360, height=360, preserveAspectRatio=True)
    p.setFont('ipaexg', 16)
    p.setFillColor(black)
    p.drawCentredString(width / 2, height - 480, "あなたの特性分析")

    # --- 2カラムセクション ---
    y_start = height - 520
    # 向いていること
    p.setFont('ipaexg', 14)
    p.setFillColor(green)
    p.drawString(70, y_start, "向いていること")
    suited_p = Paragraph(result_data.get('suited_for', ''), styleN)
    suited_p.wrapOn(p, width/2 - 100, 300)
    suited_p.drawOn(p, 70, y_start - suited_p.height - 10)
    
    # 向いていないこと
    p.setFont('ipaexg', 14)
    p.setFillColor(orange)
    p.drawString(width/2 + 20, y_start, "向いていないこと")
    not_suited_p = Paragraph(result_data.get('not_suited_for', ''), styleN)
    not_suited_p.wrapOn(p, width/2 - 100, 300)
    not_suited_p.drawOn(p, width/2 + 20, y_start - not_suited_p.height - 10)

    # --- 分析結果まとめ ---
    p.showPage() # 新しいページ
    p.setFont('ipaexg', 16)
    p.setFillColor(black)
    p.drawString(70, height - 70, "分析結果まとめ")
    synthesis_p = Paragraph(result_data.get('synthesis', ''), styleN)
    synthesis_p.wrapOn(p, width - 140, 700)
    synthesis_p.drawOn(p, 70, height - 100)
    
    p.save()
    buffer.seek(0)
    return buffer