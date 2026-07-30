# Action Deck設計

## 概要

Action Deckは、携帯エミュレーター機のコントローラーだけで、登録済みのLinux操作・スクリプト・SSHコマンドを選択して実行する専用ランチャー。

通常のLinuxデスクトップをゲームパッドで無理に操作するのではなく、小型画面向けの大きな項目とゲーム機らしい入力方式で定型操作を完結させる。

## 目標

- キーボードなしでよく使う操作を実行できる
- 小型画面でも読みやすい
- アクションを設定ファイルから追加できる
- 実行結果・失敗理由・終了コードを確認できる
- 危険な操作を誤って実行しにくい
- ゲーム中の入力と競合しない

## 基本UI

```text
┌────────────────────────────┐
│ Action Deck                │
├────────────────────────────┤
│ ▶ System                   │
│   Remote                   │
│   Development              │
│   Robot                    │
│   Favorites                │
└────────────────────────────┘

A: 決定  B: 戻る  X: 詳細  Y: お気に入り
```

カテゴリーを選ぶと、その中のアクション一覧を表示する。

```text
┌────────────────────────────┐
│ Remote                     │
├────────────────────────────┤
│ ▶ 自宅PCの状態確認         │
│   自宅PCへSSH              │
│   LattePandaへSSH          │
│   Tailscale状態確認        │
│   Moonlight起動            │
└────────────────────────────┘
```

## 入力割り当て案

| 入力 | 通常操作 |
|---|---|
| 十字キー上下 | 項目移動 |
| 十字キー左右 | ページ・値変更 |
| 左スティック | 項目移動の補助 |
| A | 決定・実行 |
| B | 戻る・キャンセル |
| X | 詳細、説明、ログ表示 |
| Y | お気に入り登録・解除 |
| L1 / R1 | カテゴリー切り替え |
| START | Action Deckホーム |
| SELECT長押し | Action Deckを呼び出す |
| L2 + R2 + START | システムメニュー |

ボタン割り当てはハードウェアごとに異なるため、論理ボタン名と実デバイスコードを設定ファイルで分離する。

## 想定画面

### ホーム

- カテゴリー一覧
- 接続状態
- バッテリー残量
- 現在時刻
- Wi-Fi状態

### アクション一覧

- アクション名
- 短い説明
- アイコン
- 危険度
- オンライン必須か
- 実行中か

### 実行中

```text
[実行中]
自宅PCへの接続確認

ping desktop.local

B: キャンセル
```

### 実行結果

```text
[成功]
自宅PCへの接続確認

応答時間: 12 ms
終了コード: 0
実行時間: 0.8秒

A: 再実行  X: 全ログ  B: 戻る
```

### エラー

```text
[失敗]
自宅PCへSSH

接続先へ到達できませんでした。

考えられる原因:
- Wi-Fi未接続
- PCの電源がOFF
- Tailscale未接続

A: 再試行  X: 詳細  B: 戻る
```

## システム構成

```text
/dev/input/event*
        ↓
Input Manager
        ↓
Action Deck UI
        ↓
Config Loader ── actions/*.yaml
        ↓
Action Executor
  ├─ ローカルコマンド
  ├─ Shell/Pythonスクリプト
  ├─ SSHコマンド
  └─ アプリ起動
        ↓
Result Viewer / Log Writer
```

## モジュール案

### `app.py`

- アプリ全体の起動
- 画面遷移
- メインループ
- 終了処理

### `input.py`

- `evdev`またはSDLからゲームパッド入力を取得
- 長押し・同時押し・連打を判定
- 実ボタンを論理ボタンへ変換

### `config.py`

- YAMLの読み込み
- スキーマ検証
- カテゴリーとアクションの生成
- 無効な設定を安全に拒否

### `executor.py`

- コマンド実行
- タイムアウト
- キャンセル
- 標準出力・標準エラー取得
- 終了コード取得
- SSH接続

### `ui.py`

- カテゴリー画面
- アクション一覧
- 確認ダイアログ
- 実行中画面
- 結果画面

### `logger.py`

- 実行日時
- アクション名
- 接続先
- 終了コード
- 実行時間
- 出力とエラー

## アクション設定案

```yaml
version: 1

categories:
  - id: remote
    name: Remote
    actions:
      - id: ping-desktop
        name: 自宅PCの状態確認
        description: desktop.localへpingを1回送信する
        icon: network
        command:
          program: ping
          args:
            - -c
            - "1"
            - desktop.local
        timeout_seconds: 5
        confirmation: none

      - id: ssh-desktop
        name: 自宅PCへSSH
        description: tmuxのmainセッションへ接続する
        icon: terminal
        command:
          program: ssh
          args:
            - -t
            - desktop
            - tmux attach-session -t main
        timeout_seconds: 0
        terminal: true
        confirmation: none

  - id: system
    name: System
    actions:
      - id: shutdown
        name: シャットダウン
        description: 端末の電源を安全に切る
        icon: power
        command:
          program: systemctl
          args:
            - poweroff
        timeout_seconds: 15
        confirmation: hold
        hold_seconds: 2
```

## 設定項目

各アクションは次の情報を持てるようにする。

| 項目 | 用途 |
|---|---|
| `id` | 内部識別子 |
| `name` | 画面表示名 |
| `description` | 詳細説明 |
| `icon` | アイコン名 |
| `program` | 実行プログラム |
| `args` | 引数配列 |
| `cwd` | 作業ディレクトリ |
| `env` | 必要な環境変数 |
| `timeout_seconds` | 実行上限 |
| `terminal` | 対話端末が必要か |
| `confirmation` | 確認方法 |
| `requires_network` | ネットワーク必須か |
| `requires_root` | 管理権限が必要か |
| `show_output` | 出力画面を表示するか |

## コマンド実行方針

### 採用する方式

Pythonの`subprocess`へプログラムと引数を配列で渡す。

```python
subprocess.run(
    ["ping", "-c", "1", "desktop.local"],
    capture_output=True,
    text=True,
    timeout=5,
    check=False,
)
```

### 原則避ける方式

```python
subprocess.run(user_defined_string, shell=True)
```

文字列全体をshellへ渡すと、引用符の扱い、特殊文字、コマンドインジェクションなどの問題が増えるため、通常アクションでは利用しない。

複雑な処理は、内容を確認した専用スクリプトとして保存し、そのスクリプトを引数なしまたは限定的な引数で呼び出す。

## アクション案

### System

| アクション | 実装例 | 確認 |
|---|---|---|
| IPアドレス表示 | `ip -brief address` | 不要 |
| バッテリー表示 | `/sys/class/power_supply`を読む | 不要 |
| CPU温度表示 | `/sys/class/thermal`を読む | 不要 |
| ストレージ表示 | `df -h` | 不要 |
| Wi-Fi再接続 | NetworkManager等 | Aで確認 |
| 再起動 | `systemctl reboot` | 長押し |
| シャットダウン | `systemctl poweroff` | 長押し |

### Remote

| アクション | 内容 |
|---|---|
| 自宅PCの状態確認 | pingまたはSSH接続試験 |
| 自宅PCへSSH | 通常のSSHセッション |
| 開発セッションへ接続 | SSH後にtmuxへattach |
| LattePandaへSSH | ロボットPCへ接続 |
| Tailscale確認 | 接続状態とIPを表示 |
| Moonlight起動 | GUIリモート画面を起動 |

### Development

| アクション | 内容 |
|---|---|
| Git status | 対象リポジトリの状態を表示 |
| Git pull | fast-forward可能時のみ更新 |
| Obsidian同期 | Gitまたは既存同期スクリプトを実行 |
| tmux一覧 | 遠隔PCのセッション一覧表示 |
| 開発環境確認 | ディスク、CPU、Docker等の状態表示 |

### Robot

初期段階では読み取り・状態確認系のみ実装する。

| アクション | 内容 |
|---|---|
| PC疎通確認 | ping、SSH接続確認 |
| ROS 2ノード一覧 | `ros2 node list` |
| ROS 2トピック一覧 | `ros2 topic list` |
| サービス状態 | `systemctl status` |
| ログ末尾表示 | `journalctl -n` |
| rosbag状態確認 | プロセスまたは保存先を確認 |

実機を動かすアクションは、通信・安全設計が固まるまで追加しない。

## 確認レベル

| レベル | 操作 | 対象例 |
|---|---|---|
| none | Aで即実行 | 状態表示、ping |
| confirm | 確認画面でA | Wi-Fi再接続、Git pull |
| hold | Aを一定時間長押し | 再起動、シャットダウン |
| sequence | 指定ボタンを順番に入力 | 危険な保守操作 |
| disabled | UIには表示するが実行不可 | 未実装、接続条件不足 |

## ゲームとの入力競合対策

- Action Deckは通常時にゲームパッド入力を占有しない
- SELECT単押しでは起動せず、長押しまたは安全な組み合わせを使う
- エミュレーター起動中はホットキーを無効化できる設定を用意する
- Action Deck起動時だけ入力デバイスをgrabする
- アプリ終了時は必ずgrabを解放する
- 強制終了しても入力が戻るようにsystemdで監視する

## systemd連携案

```ini
[Unit]
Description=Action Deck Controller Launcher
After=graphical-session.target network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/action-deck/app.py
Restart=on-failure
RestartSec=2
User=deck

[Install]
WantedBy=default.target
```

初期段階では自動起動せず、手動起動で安定性を確認してからサービス化する。

## ログ方針

保存候補:

```text
~/.local/state/action-deck/
├── action-deck.log
└── runs/
    └── 2026-07-30.jsonl
```

各実行で保存する項目:

- 実行日時
- アクションID
- 表示名
- 接続先
- 実行時間
- 終了コード
- 成功・失敗
- 標準出力
- 標準エラー

秘密鍵、パスワード、トークン、環境変数の機密値はログへ出さない。

## 段階的な実装順

### 試作1: PC上のUI

- pygameなどで全画面メニューを作る
- キーボード入力をゲームパッド入力の代用にする
- 固定された5アクションを実行する

### 試作2: 設定ファイル化

- YAML読み込み
- カテゴリー生成
- アクション生成
- 入力値検証

### 試作3: 実機入力

- `/dev/input/event*`を確認
- ボタンコードを記録
- 長押し・同時押しを実装

### 試作4: SSH統合

- 接続先一覧
- SSH鍵認証
- tmux attach
- タイムアウトとエラー表示

### 試作5: システム統合

- ゲームフロントエンドから起動
- systemdサービス化
- 安全なシャットダウン
- 実行ログ

## 初期完成条件

- コントローラーだけで起動・選択・実行・戻るができる
- YAMLへ項目を追加するとUIにも反映される
- 成功・失敗・タイムアウトを区別して表示できる
- 実行中の処理をキャンセルできる
- シャットダウンに長押し確認が入る
- ゲーム操作と競合しない

## 関連ノート

- [[overview]]
- [[機種選定]]
- [[logs]]
