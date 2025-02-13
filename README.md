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

## Herokuへのデプロイ

### 前提条件
- Heroku CLIがインストールされていること
- Herokuアカウントを持っていること

### デプロイ手順

1. Herokuにログイン
```bash
heroku login
```

2. Herokuアプリケーションの作成
```bash
heroku create youtube-sync-reader
```

3. 環境変数の設定
```bash
heroku config:set OPENAI_API_KEY="your-api-key"
heroku config:set YOUTUBE_API_KEY="your-api-key"
```

4. デプロイ
```bash
git push heroku main
```

5. プロセスの起動
```bash
# Webプロセスを起動
heroku ps:scale web=1

# Workerプロセスを起動
heroku ps:scale worker=1
```

### 運用コマンド

#### プロセスの状態確認
```bash
# 全プロセスの状態確認
heroku ps

# ログの確認（全プロセス）
heroku logs --tail

# Workerプロセスのログのみ確認
heroku logs --tail --ps worker
```

#### プロセスの停止
```bash
# Workerプロセスの停止
heroku ps:scale worker=0

# Webプロセスの停止
heroku ps:scale web=0
```

#### プロセスの再起動
```bash
# Webプロセスの再起動
heroku ps:scale web=0 && heroku ps:scale web=1

# Workerプロセスの再起動
heroku ps:scale worker=0 && heroku ps:scale worker=1
```

#### その他の便利なコマンド
```bash
# アプリケーションの情報確認
heroku info

# 環境変数の確認
heroku config

# データベースの情報確認
heroku pg:info
```

### トラブルシューティング

1. ログを確認して問題を特定
```bash
heroku logs --tail
```

2. プロセスが応答しない場合は再起動を試す
```bash
heroku ps:restart
```

3. デプロイに問題がある場合はビルドログを確認
```bash
heroku builds:info
```
