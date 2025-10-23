# backend/pdf_generator_final.py - 完全改善版

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
import os

# 日本語フォントの登録
try:
    # システムにインストールされている日本語フォントを使用
    font_path = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'  # macOS
    if not os.path.exists(font_path):
        font_path = '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf'  # Linux
    if not os.path.exists(font_path):
        font_path = 'C:\\Windows\\Fonts\\msgothic.ttc'  # Windows
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Japanese', font_path))
        FONT_NAME = 'Japanese'
    else:
        # フォールバック
        FONT_NAME = 'Helvetica'
except Exception as e:
    print(f"日本語フォントの登録に失敗しました: {e}")
    FONT_NAME = 'Helvetica'

# カラー定義 (Webページと同じ配色)
PRIMARY_COLOR = colors.HexColor('#EF4444')  # 赤
SECONDARY_COLOR = colors.HexColor('#10B981')  # 緑
BACKGROUND_LIGHT = colors.HexColor('#F9FAFB')  # 薄いグレー
TEXT_COLOR = colors.HexColor('#1F2937')  # ダークグレー
BORDER_COLOR = colors.HexColor('#E5E7EB')  # ボーダー用グレー


def create_radar_chart(scores, filename='radar_chart.png'):
    """
    レーダーチャートを生成してPNGファイルとして保存
    """
    # 日本語ラベル
    labels = ['開放性', '誠実性', '外向性', '協調性', 'ストレス耐性',
              '情報処理', '意思決定', '動機源泉', '価値追求', '作業スタイル']
    
    # スコアの取得 (0-10のスケール)
    values = [
        scores.get('Openness', 5),
        scores.get('Conscientiousness', 5),
        scores.get('Extraversion', 5),
        scores.get('Agreeableness', 5),
        scores.get('StressTolerance', 5),
        scores.get('InformationStyle', 5),
        scores.get('DecisionMaking', 5),
        scores.get('MotivationSource', 5),
        scores.get('ValuePursuit', 5),
        scores.get('WorkStyle', 5)
    ]
    
    # 角度の計算
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values += values[:1]  # 最初の値を最後に追加して円を閉じる
    angles += angles[:1]
    
    # グラフの作成
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # データのプロット
    ax.plot(angles, values, 'o-', linewidth=2, color='#EF4444', label='あなたのスコア')
    ax.fill(angles, values, alpha=0.25, color='#EF4444')
    
    # 軸の設定
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=10)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], size=8)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # 背景色
    ax.set_facecolor('#FAFAFA')
    fig.patch.set_facecolor('white')
    
    # 保存
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return filename


def create_progress_bar_image(score, label, filename='progress.png'):
    """
    プログレスバーの画像を生成
    """
    fig, ax = plt.subplots(figsize=(6, 0.8))
    
    # バーの描画
    ax.barh(0, 100, height=0.5, color='#E5E7EB', edgecolor='none')
    ax.barh(0, score, height=0.5, color='#EF4444', edgecolor='none')
    
    # テキスト
    ax.text(-5, 0, label, ha='right', va='center', fontsize=10, weight='bold')
    ax.text(score + 2, 0, f'{score}%', ha='left', va='center', fontsize=10)
    
    # 軸の設定
    ax.set_xlim(-20, 105)
    ax.set_ylim(-1, 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return filename


def generate_pdf_report_final(user_name, data):
    """
    診断結果のPDFレポートを生成
    
    Args:
        user_name: ユーザー名
        data: 診断結果データ(dict)
            - main_core_name: メインコア名
            - sub_core_title: サブコアタイトル
            - suited_for: 向いていること
            - not_suited_for: 向いていないこと
            - synthesis: 総合分析
            - radar_scores: レーダーチャート用のスコア
            - data_analysis: データ分析結果
    
    Returns:
        BytesIO: PDFのバイナリデータ
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
    
    # スタイルの定義
    styles = getSampleStyleSheet()
    
    # カスタムスタイル
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
    
    # メインタイトル
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
    
    # レーダーチャートの生成
    radar_scores = data.get('radar_scores', {})
    if radar_scores:
        radar_file = create_radar_chart(radar_scores, '/tmp/radar_chart.png')
        img = RLImage(radar_file, width=140*mm, height=140*mm)
        story.append(img)
        story.append(Spacer(1, 10*mm))
    
    story.append(PageBreak())
    
    # ===== あなたのユニークさ分析 =====
    data_analysis = data.get('data_analysis', {})
    if data_analysis:
        story.append(Paragraph("あなたのユニークさ分析", heading_style))
        story.append(Spacer(1, 5*mm))
        
        # 回答の明確さ
        extremeness_score = data_analysis.get('extremeness_score', 0)
        extremeness_comment = data_analysis.get('extremeness_comment', '')
        
        story.append(Paragraph(f"<b>回答の明確さ: {extremeness_score}%</b>", body_style))
        
        # プログレスバー(簡易版 - テーブルで表現)
        progress_table = Table(
            [[' ' * int(extremeness_score/2), ' ' * int((100-extremeness_score)/2)]],
            colWidths=[extremeness_score*1.5*mm, (100-extremeness_score)*1.5*mm]
        )
        progress_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), PRIMARY_COLOR),
            ('BACKGROUND', (1, 0), (1, 0), BORDER_COLOR),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR)
        ]))
        story.append(progress_table)
        story.append(Spacer(1, 3*mm))
        
        story.append(Paragraph(extremeness_comment, box_style))
        story.append(Spacer(1, 8*mm))
        
        # 最も特徴的な才能
        unique_trait = data_analysis.get('most_unique_trait', '')
        uniqueness_comment = data_analysis.get('uniqueness_comment', '')
        
        if unique_trait:
            story.append(Paragraph(f"<b>最も特徴的な才能: {unique_trait}</b>", body_style))
            story.append(Paragraph(uniqueness_comment, box_style))
            story.append(Spacer(1, 10*mm))
    
    # ===== 向いていること =====
    suited_for = data.get('suited_for', '')
    if suited_for:
        story.append(Paragraph("あなたに向いていること", heading_style))
        
        # ボックススタイルのテーブル
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
    
    # バッファの先頭に戻す
    buffer.seek(0)
    
    return buffer


# テスト用のコード
if __name__ == '__main__':
    # サンプルデータ
    test_data = {
        'main_core_name': '孤高のアーティスト',
        'sub_core_title': '緻密な世界観の構築者',
        'suited_for': 'あなたの回答からは、独創的なアイデアを具体的な計画に落とし込み、一人で着実に実行する能力が高いことが示唆されます。',
        'not_suited_for': '即興性が求められるライブ配信や、予測不能な状況への対応は、あなたの特性とは異なるかもしれません。',
        'synthesis': '内向的で独自の感性を持ちながら、計画性を重んじる傾向が見られます。',
        'radar_scores': {
            'Openness': 8.5,
            'Conscientiousness': 7.0,
            'Extraversion': 2.5,
            'Agreeableness': 5.0,
            'StressTolerance': 5.5,
            'InformationStyle': 4.0,
            'DecisionMaking': 6.5,
            'MotivationSource': 8.0,
            'ValuePursuit': 8.5,
            'WorkStyle': 9.0
        },
        'data_analysis': {
            'extremeness_score': 65,
            'extremeness_comment': 'あなたは多くの事柄に対して自分の意見をしっかり持っているタイプです。',
            'most_unique_trait': '外向性',
            'uniqueness_comment': 'あなたのビッグファイブ特性の中で、平均的な傾向から最も大きく離れているのは「外向性」です。'
        }
    }
    
    # PDF生成
    pdf_buffer = generate_pdf_report_final('テストユーザー', test_data)
    
    # ファイルとして保存
    with open('test_report.pdf', 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    print("テストPDFを生成しました: test_report.pdf")
