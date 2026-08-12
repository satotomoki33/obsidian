# Codex利用上限をGNOMEトップバーに表示

#memo #programming

## 概要

Ubuntu 24.04 / GNOME Shell 46のトップバーに、Codexの利用上限を常時表示するユーザー拡張を導入した。

表示例：

```text
[アイコン] 56%
```

トップバーの表示をクリックすると、次の情報を確認できる。

- 利用枠ごとの残量
- 利用枠のリセット日時
- ChatGPTプラン
- 利用可能なリセット券の枚数
- 最終取得時刻
- 手動更新ボタン
- Codex使用状況ダッシュボードへのリンク

## 導入状況

2026-08-12に導入済み。

| 項目 | 内容 |
| --- | --- |
| デスクトップ環境 | Ubuntu GNOME |
| GNOME Shell | 46.0 |
| Codex CLI | 0.144.1 |
| 拡張機能名 | Codex Limits |
| UUID | `codex-limits@sato` |
| 拡張バージョン | 3 |
| 自動更新 | 5分ごと |
| 保存場所 | `~/.local/share/gnome-shell/extensions/codex-limits@sato/` |

新規GNOME拡張をShellへ認識させるため、導入後に一度ログアウトしてログインし直す。

## 仕組み

ブラウザ画面のスクレイピングや認証トークンの直接読み取りは行わない。

Python製の補助スクリプトがローカルのCodex App Serverを起動し、JSON-RPCの `account/rateLimits/read` を呼び出す。返された `usedPercent` を残量へ変換し、GNOME拡張がトップバーへ表示する。

```text
GNOME拡張
  ↓ 5分ごとに起動
codex_limits.py
  ↓ JSON-RPC
codex app-server
  ↓
Codex利用上限情報
```

残量の計算：

```text
残り（%） = 100 - usedPercent
```

複数の利用枠が返された場合、トップバーには最も残量が少ない枠を表示し、各枠の詳細はクリックメニューに表示する。

## ファイル構成

```text
~/.local/share/gnome-shell/extensions/codex-limits@sato/
├── metadata.json
├── extension.js
└── codex_limits.py
```

- `metadata.json`: 拡張機能名、UUID、対応GNOMEバージョン
- `extension.js`: トップバー表示、メニュー、5分ごとの更新処理
- `codex_limits.py`: Codex App Serverから利用上限を取得

## 操作方法

### 詳細を見る

トップバーのCodexアイコンと `XX%` の表示をクリックする。トップバーの横幅を節約するため、バージョン3から `Codex 残り` の文字は表示しない。

### 手動更新する

表示をクリックし、`今すぐ更新` を選ぶ。

### Webの使用状況を開く

表示をクリックし、`Codex 使用状況を開く` を選ぶ。

URL：<https://chatgpt.com/codex/settings/usage>

## 確認用コマンド

利用上限の取得処理だけを確認する：

```bash
/usr/bin/python3 ~/.local/share/gnome-shell/extensions/codex-limits@sato/codex_limits.py
```

拡張が有効化対象へ登録されているか確認する：

```bash
gsettings get org.gnome.shell enabled-extensions
```

ログインし直した後、GNOMEが拡張を認識しているか確認する：

```bash
gnome-extensions info codex-limits@sato
```

GNOME Shellのエラーを確認する：

```bash
journalctl --user -b --no-pager | grep -i 'codex-limits\|Codex Limits\|JS ERROR'
```

## トラブルシューティング

### トップバーに表示されない

1. 一度ログアウトしてログインし直す。
2. 次のコマンドで拡張を有効にする。

```bash
gnome-extensions enable codex-limits@sato
```

3. `gnome-extensions info codex-limits@sato` で状態を確認する。

`状態: ERROR` かつログに `Tried to construct an object without a GType` と出る問題は、拡張バージョン2で修正済み。修正前のコードがGNOME Shellのメモリに残っている場合は、ログアウトしてログインし直す。

### `Codex --` と表示される

トップバー表示をクリックすると、取得エラーの内容が表示される。まず補助スクリプトを単独実行して確認する。

```bash
/usr/bin/python3 ~/.local/share/gnome-shell/extensions/codex-limits@sato/codex_limits.py
```

よくある確認項目：

- `codex --version` が成功するか
- Codex CLIへChatGPTアカウントでログイン済みか
- `codex app-server` が使用可能か
- ネットワークへ接続できるか

### 表示が古い

メニューの `今すぐ更新` を押す。通常は5分ごとに自動更新される。

## 無効化・再有効化

無効化：

```bash
gnome-extensions disable codex-limits@sato
```

再有効化：

```bash
gnome-extensions enable codex-limits@sato
```

## アンインストール

まず拡張を無効化する。

```bash
gnome-extensions disable codex-limits@sato
```

その後、拡張ディレクトリを削除し、ログアウトしてログインし直す。削除は元へ戻しにくいため、必要なら先にバックアップする。

```text
~/.local/share/gnome-shell/extensions/codex-limits@sato/
```

## 導入時点のスナップショット

2026-08-12の動作確認時点：

- ChatGPT Plus
- 週枠の残り：56%
- 次回リセット：2026-08-18 12:52 JST
- リセット券：1枚

この値は記録時点のものであり、トップバーの表示はCodexの利用に応じて変化する。

## 参考

- [Codex App Server](https://learn.chatgpt.com/docs/app-server.md)
- [Codex使用状況](https://chatgpt.com/codex/settings/usage)
