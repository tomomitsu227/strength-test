# backend/app.py - デバッグ捜査モード
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os
# 一時的にコメントアウトして、インポートエラーの可能性を排除します
# from models_mbti import save_response, get_all_responses
# from pdf_generator_mbti_improved import generate_pdf_report

app = Flask(__name__)
CORS(app)

# --- ファイルパスの定義 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'data'))

QUESTIONS_PATH = os.path.join(DATA_DIR, 'questions.json')
TYPE_LOGIC_PATH = os.path.join(DATA_DIR, 'type_logic.json')
TYPE_DETAILS_PATH = os.path.join(DATA_DIR, 'type_details.json')

# --- デバッグ用読み込み関数 ---
def debug_load_json(path, file_name):
    print(f"【デバッグ】読み込み開始: {file_name}")
    print(f"【デバッグ】絶対パス: {path}")
    
    # 1. ファイルが存在するか確認
    if not os.path.exists(path):
        print(f"【エラー】ファイルが存在しません: {file_name}")
        return None

    # 2. ファイルサイズを確認
    size = os.path.getsize(path)
    print(f"【デバッグ】ファイルサイズ: {size} バイト")
    if size == 0:
         print(f"【致命的エラー】ファイルの中身が空っぽです: {file_name}")
         return None

    # 3. JSONとして読み込み試行
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"【成功】読み込み完了: {file_name}")
        return data
    except json.JSONDecodeError as e:
        print(f"【JSONエラー】{file_name} の形式が不正です: {e}")
        # 中身を少しだけ表示してみる（デバッグ用）
        try:
            with open(path, 'r', encoding='utf-8') as f:
                print(f"【参考】ファイル冒頭の内容: {f.read(50)}...")
        except:
            pass
        return None
    except Exception as e:
         print(f"【予期せぬエラー】{file_name} でエラー発生: {e}")
         return None

print("--- サーバー起動プロセス開始 ---")
print(f"【デバッグ】現在のディレクトリ: {os.getcwd()}")
print(f"【デバッグ】データフォルダ: {DATA_DIR}")

# データを順番に読み込む
QUESTIONS_DATA = debug_load_json(QUESTIONS_PATH, "questions.json")
TYPE_LOGIC = debug_load_json(TYPE_LOGIC_PATH, "type_logic.json")
TYPE_DETAILS = debug_load_json(TYPE_DETAILS_PATH, "type_details.json")

# 読み込みに失敗したら強制終了させる（ログを残すため）
if not all([QUESTIONS_DATA, TYPE_LOGIC, TYPE_DETAILS]):
    print("--- サーバー起動失敗：データの読み込みに失敗しました ---")
    # Renderにエラーを認識させるためわざと例外を起こす
    raise Exception("データの読み込みに失敗したため起動を中止します。上のログを確認してください。")

print("--- 全データの読み込みに成功しました。Flaskアプリを起動します ---")

# --- 以下、ダミーのAPIエンドポイント（起動確認用） ---
# ※ 本来のロジックは一時的に無効化しています
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'mode': 'debug'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)