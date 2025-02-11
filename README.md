# YouTube Sync Reader

YouTubeの動画から字幕を取得し、翻訳を行うアプリケーションです。

## 環境構築

1. 仮想環境の作成と有効化:
```bash
# 仮想環境の作成（初回のみ）
python -m venv venv

# 仮想環境の有効化
source venv/bin/activate
```

2. 依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

## サーバーの起動

1. 仮想環境が有効化されていることを確認
```bash
source venv/bin/activate
```

2. Flaskサーバーの起動
```bash
python app.py
```

サーバーは http://127.0.0.1:5000 で起動します。

## 使用方法

1. ブラウザで http://127.0.0.1:5000 にアクセス
2. YouTubeのURLを入力して字幕を取得
3. 必要に応じて翻訳を実行
