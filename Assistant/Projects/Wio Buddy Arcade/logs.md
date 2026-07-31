---
title: Wio Buddy Arcade Logs
created: 2026-07-31
updated: 2026-08-01
tags:
  - project-log
  - embedded
  - Wio-Terminal
---

# Wio Buddy Arcade Logs

親ノート: [[Assistant/Projects/Wio Buddy Arcade/overview|Wio Buddy Arcade]]

## 2026-07-31

- USBで接続された機器が`2886:802d Seeed Wio Terminal`、シリアルポートが`/dev/ttyACM0`であることを確認
- 既存のTetris試作をGitへ保存
- システム版PlatformIO 4.3.4ではなく、ユーザー版6.1.19を使用する方針を決定
- Wio BuddyとTetrisを選択できる統合ランチャーを実装
- LCD、5方向スイッチ、A/B/C、加速度、光センサー、ブザーを統合
- 起動状態を追える2秒間隔のUSBシリアル診断を追加
- 内蔵加速度センサーをGrove向け`Wire`から`Wire1`へ変更
- この実機のLIS3DHTRが`Wire1 / 0x18`で応答することを確認
- ペット起動直後の誤シェイク判定を修正
- Tetrisの短い回転・ハードドロップ入力を取りこぼさないよう改善
- 初期統合版を実機へ書き込み、Flash検証に成功

## 2026-08-01

### LCD復旧

- 音とセンサーは動くがLCDが真っ暗になる症状を確認
- 汎用`TFT_eSPI`が優先され、Wio Terminal用ピン設定が使われていないことを特定
- 汎用依存を除去し、Wio Terminal専用`Seeed_Arduino_LCD`へ修正
- LCD表示の復旧を確認

### フリッカー対策

- 約3秒ごとのフリッカーは、定期診断に合わせたメニュー全画面再描画が原因と判明
- ランチャー描画を起動時と選択変更時だけに限定
- キャラクターやゲームの描画途中が見える問題に対し、320×240のRAM裏画面を導入
- 完成したフレームだけをLCDへ一括転送する方式へ変更

### アプリ追加

- 起動メニューを2×2の4アプリ選択画面へ拡張
- Space Invadersを実装
  - 3段×6列の敵編隊
  - 自機弾と敵弾
  - 破壊可能な防壁
  - 残機、スコア、速度変化、複数ウェーブ
- Mini RPGを実装
  - 13×20フィールド
  - NPC、宝箱、5体の敵
  - ターン制戦闘、レベル、経験値、攻撃力、ゴールド
  - クリスタルを神殿へ届けるクリア目標
- 4アプリを1つのファームウェアへ同居できることを確認

### スマホ連携と時計

- Seeed Arduino rpcWiFi 1.1.0を追加
- `Wio-Buddy` WPA2アクセスポイントを実装
- `192.168.4.1`のスマホ用Web UIを実装
- DNSキャプティブポータルを実装
- WebからBuddyを撫でる、驚かせる、眠らせる、起こすAPIを追加
- スマホのJavaScriptからUnix epochとタイムゾーンを送る時刻同期を追加
- Buddyの顔上部へデジタル時計を追加
- Wi-Fi用RAMを確保するため、フルスクリーン裏画面を16bitから8bitへ変更
- ダブルバッファ方式を維持しつつ、動的RAMを約77KB節約

### 無線コア更新

- スマホ連携版を書き込むとWi-Fi初期化で止まり、起動後のシリアル出力が続かない症状を確認
- RTL8720DN側の古いファームウェアとrpcWiFiのeRPC方式の不一致と判断
- Seeed公式`ambd_flash_tool` v0.6.0を使用
- `erase`で無線コアを消去し、`All images are sent successfully`を確認
- `flash`でeRPC対応ファームウェアを書き込み、同じく成功を確認
- USB中継プログラムからWio Buddy Arcadeへ戻すため、ATSAMD51へアプリを再upload

### 最終検証

- 最終ビルド成功
  - 静的RAM: 61,136 / 196,608 bytes（31.1%）
  - Flash: 128,136 / 507,904 bytes（25.2%）
- 実機へ129,168 bytesを書き込み、Flash Verify成功
- シリアル診断へ`wifi=ready/offline`と`clock=synced/waiting`を追加
- `mode=menu ... accel=ok ... wifi=ready clock=waiting`が継続出力されることを確認
- `Wio-Buddy`がWPA2、電波強度100%で検出されることを確認
- PCからWio-Buddyへ接続可能なことを確認
- 接続テスト後、PCを元の`konpeito_5G`へ復帰
- テストで作成したPC側のWio-Buddy自動接続プロファイルを削除
- Git作業ツリーがクリーンであることを確認

## 最終コミット

- `33cd634 feat: add smartphone remote and Buddy clock`
- `797545e docs: record wireless core provisioning`
