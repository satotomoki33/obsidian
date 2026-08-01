---
tags:
  - project
  - python
  - flask
  - youtube
  - audio
status: active
created: 2026-08-01
project_path: /home/sato/dev/youtube-walkman-converter
---

# YouTube Walkman Converter

YouTube動画の音声をMP3へ変換し、ウォークマン向けにメタデータとジャケット画像を整理するローカルWebアプリ。

> [!warning] 利用上の注意
> 権利を所有している、またはダウンロード・変換が許可されているコンテンツだけを対象にする。

## 現在の状態

- 初期バージョン実装済み
- Flaskサーバーは `127.0.0.1:5000` のみで待ち受け
- FFmpeg 7.0.2-staticをユーザー領域へ導入済み
- yt-dlp 2026.07.04を仮想環境へ導入済み
- 自動テストは9件すべて成功
- URL入力欄は貼り付けとドラッグ＆ドロップに対応

## プロジェクト情報

| 項目 | 内容 |
| --- | --- |
| パス | `/home/sato/dev/youtube-walkman-converter` |
| バックエンド | Python / Flask |
| 動画・音声取得 | yt-dlp |
| MP3変換 | FFmpeg |
| ID3タグ | Mutagen |
| 画像処理 | Pillow |
| フロントエンド | HTML / CSS / Vanilla JavaScript |
| 出力先 | `/home/sato/dev/youtube-walkman-converter/output` |
| ログ | `/home/sato/dev/youtube-walkman-converter/logs` |

## 起動方法

```bash
cd /home/sato/dev/youtube-walkman-converter
source .venv/bin/activate
python app.py
```

ブラウザで次を開く。

```text
http://127.0.0.1:5000
```

## 操作手順

1. 権利上利用可能なYouTube URLを入力欄へ貼り付けるか、ブラウザからドラッグ＆ドロップする。
2. 「動画情報を取得」を押す。
3. 曲名、アーティスト、アルバム、公開年、トラック番号、ジャンル、ファイル名を確認・編集する。
4. 必要に応じてジャケット画像と音質を変更する。
5. 「選択した曲をMP3に変換」を押す。
6. 完了後に個別MP3またはZIPを取得する。

## 主な機能

- 通常URL、短縮URL、Shorts URLの検証
- 複数URLの一括入力、重複除外、行番号付きエラー表示
- 動画タイトルとチャンネル名から曲名・アーティストを推定
- 楽曲メタデータの個別編集と一括編集
- 128 / 192 / 256 / 320 kbps変換
- YouTubeサムネイルまたは独自JPEG/PNGをジャケットとして使用
- 画像を600×600pxのJPEGへ変換
- ID3v2.3タグとAPICジャケットの埋め込み
- 1曲ずつの順次変換、進捗表示、キャンセル
- 失敗曲があっても残りの処理を継続
- 個別MP3とZIPのダウンロード
- ファイル名サニタイズと重複時の連番付与

## API

| メソッド | エンドポイント | 用途 |
| --- | --- | --- |
| POST | `/api/videos/info` | 動画情報取得 |
| POST | `/api/thumbnails` | 独自ジャケットのアップロード |
| POST | `/api/conversions` | 変換ジョブ作成 |
| GET | `/api/conversions/<job_id>` | 進捗取得 |
| POST | `/api/conversions/<job_id>/cancel` | キャンセル |
| GET | `/api/files/<file_id>` | 個別MP3取得 |
| GET | `/api/conversions/<job_id>/download` | ZIP取得 |

## テスト

```bash
cd /home/sato/dev/youtube-walkman-converter
source .venv/bin/activate
python -m pytest -q
node --check static/js/app.js
ffmpeg -version
python -m yt_dlp --version
```

実ファイルのタグ確認：

```bash
mutagen-inspect output/対象ファイル.mp3
```

## ディレクトリ構成

```text
youtube-walkman-converter/
├── app.py
├── config.py
├── models/track.py
├── services/
│   ├── youtube_service.py
│   ├── conversion_service.py
│   ├── metadata_service.py
│   └── file_service.py
├── templates/index.html
├── static/css/
├── static/js/app.js
├── tests/
├── temp/
├── output/
└── logs/
```

## コミット履歴

```text
b924930 URL入力欄のドラッグアンドドロップに対応
d929489 テストと利用手順を整備
f0d59fe メタデータ編集と進捗表示の画面を追加
6966d4b 変換処理とローカルAPIの基盤を実装
```

## 既知の制限

- ジョブ状態はメモリ上にあり、アプリ再起動後は復元されない。完成MP3は残る。
- 再生リスト、ログイン、Cookie、非公開動画、年齢・地域制限、DRM回避には非対応。
- メタデータ推定は完全ではないため、変換前に確認が必要。
- 進捗率は処理段階ベースの概算。
- outputフォルダをファイルマネージャーで開くボタンは未実装。
- ウォークマンの機種差があるため実機確認が必要。

## 今後の候補

- [ ] 実際に権利を持つ短い動画で一連の変換を確認する
- [ ] ウォークマン実機で曲名・アーティスト・ジャケット表示を確認する
- [ ] outputフォルダを開くボタンを追加する
- [ ] ジョブ履歴を永続化する
- [ ] 再生リスト対応を検討する

## 関連ファイル

- プロジェクトの詳細手順: `/home/sato/dev/youtube-walkman-converter/README.md`
- 設定: `/home/sato/dev/youtube-walkman-converter/config.py`
