#!/bin/bash

# /workspace ディレクトリ内の 'app.py' を探し、その絶対パスを取得
APP_PY_PATH=$(find /workspace -name "app.py" | head -n 1)

# 'app.py' が見つからなかった場合はエラーで終了
if [ -z "$APP_PY_PATH" ]; then
  echo "Error: app.py not found anywhere in /workspace"
  exit 1
fi

# 'app.py' があるディレクトリ（つまり backend ディレクトリの絶対パス）を取得
APP_DIR=$(dirname "$APP_PY_PATH")

# backend ディレクトリに移動
cd "$APP_DIR"

# 現在のディレクトリの内容をログに出力（デバッグ用）
echo "--- Running in directory: $(pwd) ---"
ls -la
echo "--- Found data directory: ---"
ls -la data/
echo "-------------------------------------"

# gunicorn を起動
gunicorn app:app --bind 0.0.0.0:8000