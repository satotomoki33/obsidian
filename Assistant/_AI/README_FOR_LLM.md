# README_FOR_LLM

このVaultでは、ユーザーが自然文で書いたタスク・予定・メモ・プロジェクト情報を、AIがObsidian用のMarkdownとして整理する。

## 最初に読むこと

AIは作業前に、必ず以下のファイルを確認する。

- `Assistant/_AI/README_FOR_LLM.md`
- `Assistant/_AI/rules.md`
- `Assistant/_AI/project_aliases.md`
- `Assistant/_AI/tag_rules.md`
- `Assistant/_AI/templates.md`

## 編集可能範囲

AIが編集してよい場所は以下のみ。

- `Daily/`
- `Assistant/Tasks/`
- `Assistant/Projects/`
- `Assistant/_AI/`
- Vault直下の `inbox.md`

ただし、`inbox.md` は読み取りと整理後の空化のみ許可する。

## 編集禁止

以下は絶対に編集しない。

- `.obsidian/`
- `.git/`
- 添付ファイル
- `Assistant/` 以外のVault内ファイル
- ユーザーが明示していない既存ノート

## 禁止事項

- ファイル削除
- 既存ファイルの全面上書き
- 大量のリネーム
- `.obsidian/` の編集
- `.git/` の編集
- タスクの重複作成
- 判断不能な内容の削除

## 基本方針

- 基本は追記する
- 既存内容はなるべく保持する
- 新規ファイル作成は許可する
- 日付は `YYYY-MM-DD` に統一する
- 人間が読んで分かりやすいMarkdownにする
- 迷った内容は `Assistant/_AI/unresolved.md` に移す
- 処理内容は `Assistant/_AI/llm_log.md` に記録する

## 重要な原則

日付のあるタスクは、該当日のDailyノートに本体を書く。  
タスク一覧には同じチェックボックスをコピーしない。  
タスク一覧はTasksプラグインのクエリで表示する。

これにより、Dailyノート側とタスク一覧側でチェック状態を共有できる。
