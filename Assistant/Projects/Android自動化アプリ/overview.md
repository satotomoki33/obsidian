# Android自動化アプリ

#programming #memo

## 概要

GUIとJSONファイルの両方から編集できる、Android向けの端末自動化アプリを開発する。

iPhoneの「ショートカット」のように、トリガー・条件・アクションを組み合わせて処理を作れるようにする。ただし、GUIだけで複雑なフローを組む面倒さを避けるため、JSONを正式な保存形式とし、GUIはJSONを視覚的に編集するビューとして扱う。

仮称候補:

- FlowDeck
- Automate JSON
- TriggerBox

## 目的

- GUIで簡単に自動化を作れる
- JSONを直接編集して素早く細かい設定ができる
- GUI編集と外部エディタによるJSON編集を相互に反映できる
- 通知、時刻、ウィジェットなどを起点にアプリやURLを開ける
- 実行内容と失敗理由を確認できる

## 基本モデル

1つの自動化を次の3要素で表す。

```text
WHEN  何が起きたら
IF    どの条件を満たしたら
DO    何を実行するか
```

例:

```text
WHEN Discordから「ロボコン」を含む通知が来る
IF   18:00〜翌1:00
DO   確認通知を表示し、押したらDiscordを開く
```

## 重要な設計方針

```text
JSON = 唯一の正式なデータ
GUI  = JSONを視覚的に操作するビュー
```

GUI専用の内部形式を持たず、GUIとJSONエディタは同じWorkflowモデルを編集する。

JSONには `schema_version` を持たせ、将来の形式変更に対応する。未知のフィールドをGUI保存時に消さない仕組みも必要。

## JSON例

```json
{
  "schema_version": 1,
  "id": "robocon-discord",
  "name": "ロボコン通知からDiscordを開く",
  "enabled": true,
  "trigger": {
    "type": "notification.posted",
    "package": "com.discord",
    "match": {
      "title_contains": "ロボコン"
    }
  },
  "conditions": [
    {
      "type": "time.in_range",
      "start": "18:00",
      "end": "01:00",
      "timezone": "Asia/Tokyo"
    }
  ],
  "actions": [
    {
      "type": "notification.show",
      "title": "ロボコン関連の通知",
      "body": "Discordを開きますか？",
      "on_tap": {
        "type": "app.open",
        "package": "com.discord"
      }
    }
  ]
}
```

## 想定機能

### トリガー

- 手動実行
- ホーム画面ウィジェットのタップ
- 指定時刻・曜日
- 他アプリからの通知受信
- 将来的には端末起動、充電状態、Wi-Fi接続なども検討

### 条件

- 時間帯
- 曜日
- 通知元アプリ
- 通知タイトル・本文の文字列一致
- 複数条件のAND・OR

### アクション

- アプリを開く
- URL・ディープリンクを開く
- 通知を表示する
- 通知タップ時に別アクションを実行する
- 一定時間待つ
- 複数アクションを順番に実行する

## Androidでの制約

Androidでは通知監視に `NotificationListenerService` を利用できるが、ユーザーによる通知アクセス権限の許可が必要。

バックグラウンドから突然別アプリを前面表示する動作はOSに制限される。そのため、指定時刻になったら直接アプリを開くのではなく、基本は次の流れにする。

```text
指定時刻になる
→ 自作通知を表示
→ ユーザーが通知を押す
→ 指定アプリを開く
```

他アプリの元の通知が押された瞬間を横取りすることも基本的にはできない。通知受信を検知した後、自作通知を出して、その通知タップを起点に処理する。

## 推奨技術構成

| 項目 | 技術候補 |
|---|---|
| 言語 | Kotlin |
| UI | Jetpack Compose |
| ウィジェット | Jetpack Glance |
| JSON | kotlinx.serialization |
| 非同期処理 | Kotlin Coroutines / Flow |
| 定期処理 | WorkManager |
| 時刻トリガー | AlarmManager |
| 通知監視 | NotificationListenerService |
| アプリ起動 | Intent / PackageManager |
| 設定保存 | DataStore |
| 実行履歴 | Room |

FlutterやReact Nativeでは通知監視、ウィジェット、AlarmManager、Intent周辺でネイティブ実装が多くなるため、Kotlinネイティブを優先する。

## 内部構成案

```text
GUIエディタ / JSONエディタ
            ↓
       Workflow JSON
            ↓
      Parser / Validator
            ↓
      Automation Engine
       ↙            ↘
Trigger Adapters   Action Executors
```

```text
app/
├── core/
│   ├── model/
│   ├── engine/
│   └── validation/
├── platform/android/
│   ├── notification/
│   ├── alarm/
│   ├── widget/
│   └── intent/
├── data/
│   ├── workspace/
│   ├── history/
│   └── settings/
└── ui/
    ├── workflow_list/
    ├── visual_editor/
    ├── json_editor/
    └── execution_log/
```

## ファイル管理案

Storage Access Frameworkでユーザーがワークスペースフォルダを選択する。

```text
AutomationWorkspace/
├── workflows/
│   ├── robocon-discord.json
│   ├── morning-mode.json
│   └── coding-widget.json
├── backups/
├── logs/
└── workspace.json
```

外部編集との競合対策:

- 読み込み時のファイルハッシュを保持
- 保存前に外部変更を確認
- 競合時にGUI版とファイル版の差分を表示
- 保存前にバックアップを作成
- JSON構文エラー時は前回の正常版で動作
- 壊れたJSONを自動で上書きしない

## MVP

### トリガー

- 手動実行
- ウィジェットタップ
- 指定時刻
- 他アプリの通知受信

### 条件

- 時間帯
- 曜日
- 通知元アプリ
- 通知タイトル・本文の文字列一致

### アクション

- アプリを開く
- URLを開く
- 通知を表示する
- 待機する
- 複数処理を順番に実行する

### 画面

- 自動化一覧
- GUI編集
- JSON編集
- 実行履歴
- 権限設定

MVPの完成条件:

> JSONまたはGUIで「ウィジェットを押すとアプリを開く」「指定時間に通知し、押すとアプリを開く」「特定アプリの通知を検知して別の通知を出す」を作成できる。

## 安全機構

- 通知内容は端末内だけで処理する
- ネット送信は標準で無効にする
- 監視対象アプリを許可リスト式にする
- JSONインポート時に必要権限と実行内容を表示する
- 自分の通知を再検知する無限ループを防ぐ
- 短時間の連続実行を抑えるクールダウンを設ける
- 実行履歴と失敗理由を保存する
- 全自動化を止める緊急停止スイッチを用意する
- 危険なURLスキームを拒否する

## iOS対応方針

iOSでは他アプリの通知監視や自由なバックグラウンド実行が難しいため、最初はAndroid専用とする。

将来的にiOS版を作る場合は、以下に機能を限定する。

- 自分のアプリのローカル通知
- 自分の通知タップ処理
- ウィジェット操作
- App Intents
- Shortcutsアプリからの呼び出し
- 自アプリ内のJSONワークフロー実行

## 関連タスク

現時点では日付付きタスクとして登録せず、開発開始時にMVPをIssueまたはタスクへ分解する。

## 未決定事項

- 正式なアプリ名
- JSON Schemaの詳細
- GUIをカード式・ノード式のどちらにするか
- 条件分岐、変数、ループを初期版に含めるか
- ワークフロー間呼び出しを許可するか
- 配布をGoogle Play前提にするか、APK配布を優先するか
- ファイル変更監視と競合解決の具体方式

## 関連ノート

- [[Android自動化アプリ/logs]]
