# Weekly Notes

週間レビューを保存するディレクトリ。

## 保存形式

```text
Weekly/YYYY/MM/YYYY-Www.md
```

- 週は日本時間の月曜日から日曜日までとする。
- `YYYY-Www` はISO週番号を使用する。
- `MM` は対象週の月曜日が属する月を使用する。
- デイリーノート、`Twitterログ.md`、`tasks.md`、関連ノートを根拠として作成する。
- 単なるタスク一覧ではなく、出来事・感情・関心・生活状態のつながりを分析する。

## 基本構成

```md
---
type: weekly
week: YYYY-Www
period:
  start: YYYY-MM-DD
  end: YYYY-MM-DD
created: YYYY-MM-DD
---

# YYYY-Www（YYYY-MM-DD〜YYYY-MM-DD）

## 今週のテーマ

## 今週はどんな一週間だったか

## 記録とつぶやきから見えた自分らしさ

## 今週の成長

## 心身と生活の状態

## 持ち越したものが示していること

## 自分に問いかけたいこと

## 来週への小さな提案
```
