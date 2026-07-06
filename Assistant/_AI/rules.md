# 整理ルール

## 全体方針

ユーザーの自然文メモを、以下に分類して整理する。

- タスク
- 予定
- メモ
- 作業ログ
- プロジェクト情報
- 未分類・判断不能

基本的に、情報を削除してはいけない。  
整理先が分からない場合は `Assistant/_AI/unresolved.md` に移す。

---

## inbox.md の処理

Vault直下の `inbox.md` に内容がある場合、以下の手順で処理する。

1. `inbox.md` の内容を読む
2. 内容をタスク、予定、メモ、プロジェクト情報に分解する
3. 日付があるタスクは `Daily/YYYY/MM/YYYY-MM-DD.md` に追加する
4. 日付がある予定は `Daily/YYYY/MM/YYYY-MM-DD.md` の `## Schedule` に追加する
5. 日付がないタスクは、内容から自然に決まるプロジェクトがあればそのプロジェクトのログか未整理欄に移す
6. 判断に迷う内容は `Assistant/_AI/unresolved.md` に移す
7. 処理が完了したら `inbox.md` を空にする
8. 何をしたかを `Assistant/_AI/llm_log.md` に記録する

判断不能な内容を消してはいけない。

---

## Dailyノート

Dailyノートは以下の場所に作る。

```text
Daily/YYYY/MM/YYYY-MM-DD.md
```

Dailyノートの基本構成:

```md
# YYYY-MM-DD

## Tasks

## Schedule

## Logs

## Notes
```

既にDailyノートがある場合は、既存内容を消さず、適切な見出しの下に追記する。  
見出しが存在しない場合は追加してよい。

---

## タスク

日付のあるタスクは、必ず該当日のDailyノートの `## Tasks` に追加する。

形式:

```md
- [ ] タスク名 📅 YYYY-MM-DD #task
  - project: [[プロジェクト名]]
  - memo: 補足
```

プロジェクト名が分からない場合:

```md
- [ ] タスク名 📅 YYYY-MM-DD #task
  - project:
  - memo: 補足
```

## チェックボックス共有の方針

同じタスクを複数ファイルにコピーしてはいけない。

タスク本体はDailyノートに1つだけ作る。  
タスク一覧はTasksプラグインのクエリでDailyノート上のタスクを表示する。

これにより、タスク一覧側でチェックしても元のDailyノートのタスクに反映される。

---

## Tasksフォルダ

`Assistant/Tasks/` には、タスク本体ではなくクエリ用ノートを置く。

作成するノート:

- `Assistant/Tasks/all-tasks.md`
- `Assistant/Tasks/upcoming.md`
- `Assistant/Tasks/overdue.md`

### all-tasks.md

````md
# All Tasks

```tasks
not done
sort by due
```
````

### upcoming.md

````md
# Upcoming Tasks

```tasks
not done
due after yesterday
sort by due
```
````

### overdue.md

````md
# Overdue Tasks

```tasks
not done
due before today
sort by due
```
````

---

## 予定

予定はDailyノートの `## Schedule` に追加する。

形式:

```md
- 時刻: 予定名 #schedule
  - location:
  - memo:
```

時刻が不明な場合:

```md
- 予定名 #schedule
  - time:
  - location:
  - memo:
```

---

## 作業ログ

作業ログはDailyノートの `## Logs` に追加する。

形式:

```md
- 作業内容
  - project: [[プロジェクト名]]
  - memo:
```

プロジェクトが明確な場合は、必要に応じて `Assistant/Projects/<プロジェクト名>/logs.md` にも要約を追記する。

---

## メモ

日付に関係するメモはDailyノートの `## Notes` に追加する。

プロジェクトに関係するメモは `Assistant/Projects/<プロジェクト名>/overview.md` または `logs.md` に追加する。

判断に迷った場合は `Assistant/_AI/unresolved.md` に移す。

---

## Projects

プロジェクトが明確な場合、以下のフォルダを作成する。

```text
Assistant/Projects/<プロジェクト名>/
├── overview.md
└── logs.md
```

`overview.md` の基本構成:

```md
# プロジェクト名

## 概要

## 関連タスク

## メモ
```

`logs.md` の基本構成:

```md
# プロジェクト名 Logs

## YYYY-MM-DD
```

ただし、タスク本体はProjectsに置かない。  
タスク本体は必ずDailyノートに置く。

---

## 未分類・判断不能

判断に迷う内容は `Assistant/_AI/unresolved.md` に移す。

形式:

```md
## YYYY-MM-DD

### 元の内容

> 元の文章

### 判断に迷った理由

- 理由を書く

### 仮分類

-
```

---

## LLM作業ログ

AIがファイルを変更したら、`Assistant/_AI/llm_log.md` に記録する。

形式:

```md
## YYYY-MM-DD

- `inbox.md` からN件整理
- `Daily/YYYY/MM/YYYY-MM-DD.md` にタスクを追加
- `Assistant/Projects/<プロジェクト名>/overview.md` を作成
- `inbox.md` を空にした
```
