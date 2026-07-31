---
title: Wio Buddy Arcade
status: 完成・実機動作確認済み
created: 2026-07-31
updated: 2026-08-01
tags:
  - project
  - embedded
  - Wio-Terminal
  - Arduino
  - game
  - Wi-Fi
aliases:
  - Wio Terminalゲーム機
  - Wio Buddy
---

# Wio Buddy Arcade

> [!summary] 一言で表すと
> Seeed Studio Wio Terminalを、表情豊かなペットロボット、3種類のゲーム、スマホリモコン、時計を備えた小型アーケード端末にするプロジェクト。2026-08-01時点で実機への書き込みと主要機能の動作確認まで完了している。

## プロジェクト概要

Wio Terminal D51Rの液晶、ボタン、5方向スイッチ、加速度センサー、光センサー、ブザー、Wi-Fiをまとめて活用するArduinoファームウェアを開発した。

起動すると4アプリのランチャーが表示され、次の機能を1台で切り替えて遊べる。

| アプリ | 内容 |
|---|---|
| Wio Buddy | 目と表情が動くペットロボット。撫でる、驚く、眠る、起きる、時計表示 |
| Tetris | ゴースト、NEXT、スコア、ライン、レベル、効果音付き |
| Space Invaders | 敵編隊、敵弾、防壁、残機、スコア、複数ウェーブ |
| Mini RPG | フィールド探索、NPC、宝箱、ターン制戦闘、成長、クリア目標 |

ソースコードは次の場所にある。

```text
/home/sato/dev/seeed/tetris
```

## 完成状態

- [x] 4アプリのランチャー
- [x] Wio Buddyの表情・まばたき・睡眠・感情・効果音
- [x] Tetris
- [x] Space Invaders
- [x] Mini RPG
- [x] ちらつきを抑えたフルスクリーンダブルバッファ描画
- [x] スマホ用Wi-Fiアクセスポイント
- [x] スマホ用Webリモコン
- [x] スマホからの現在時刻・タイムゾーン同期
- [x] Buddy画面のデジタル時計
- [x] RTL8720DN無線コアのeRPC対応ファームウェア更新
- [x] ビルド、Flash検証、実機診断

## すぐ使う

### 本体

1. Wio Terminalの電源を入れる
2. 5方向スイッチでアプリを選ぶ
3. スイッチ中央を押して起動する
4. どのアプリからでも上面中央の **B** でランチャーへ戻る

ショートカット:

| 入力 | 動作 |
|---|---|
| 上面A | Wio Buddyを開く |
| 上面C | Tetrisを開く |
| 5方向スイッチ中央 | 選択中のアプリを開く |

### スマホ連携と時計

1. スマホのWi-Fi設定で **`Wio-Buddy`** を選ぶ
2. パスワード **`buddy123`** を入力する
3. 自動表示されるページ、またはChromeで **`http://192.168.4.1`** を開く
4. ページを開いた時点でスマホの現在時刻とタイムゾーンが自動同期される
5. Buddy画面上部に時計が表示される

Web画面から「なでる」「びっくり」「ねむる」「おきる」を操作できる。別のゲームを表示中でも、Web操作を送るとBuddyへ切り替わる。

> [!note] インターネット未接続表示について
> `Wio-Buddy`はWio Terminalとスマホを直接つなぐローカルWi-Fiであり、インターネット回線は提供しない。スマホに「インターネット未接続」と表示されても正常。

> [!warning] 時計の保持
> Wio Terminalの電源を切ると時刻同期は失われる。再起動後にスマホで操作ページを開けば、すぐ再同期される。

## Buddyの動作

- 目が5方向スイッチと本体の傾きを追う
- 自動でまばたきする
- Aまたはスイッチ中央で撫でると喜ぶ
- Cまたは強いシェイクで驚く
- DOWNで眠り、UPで起きる
- 25秒ほど操作がなければ眠る
- 周囲の明るさによって背景色と瞳孔サイズが変わる
- 感情に合わせてブザーが鳴る
- スマホ同期後は顔の上部に時刻を表示する

## ゲーム操作

### Tetris

| 入力 | 動作 |
|---|---|
| LEFT / RIGHT | ミノ移動 |
| DOWN | ソフトドロップ |
| UP | ハードドロップ |
| スイッチ中央 / A | 回転 |
| ゲームオーバー時のC | リトライ |

### Space Invaders

| 入力 | 動作 |
|---|---|
| LEFT / RIGHT | 自機移動 |
| スイッチ中央 / A | ショット |
| ゲームオーバー時のC / スイッチ中央 | リトライ |

### Mini RPG

| 状態 | 入力 | 動作 |
|---|---|---|
| フィールド | 5方向スイッチ | 移動 |
| フィールド | スイッチ中央 / A | 会話・調べる |
| 戦闘 | スイッチ中央 / A | 攻撃 |
| 戦闘 | C | ポーション |
| 戦闘 | DOWN | 防御 |

南の宝箱からクリスタルを回収し、北東の神殿へ届けるとクリア。

## 使用したハードウェア機能

| Wio Terminal機能 | 用途 |
|---|---|
| 320×240 LCD | ランチャー、Buddy、ゲーム画面 |
| 5方向スイッチ | 選択、移動、ゲーム操作、視線操作 |
| 上面A/B/C | 決定、メニュー復帰、特殊操作 |
| LIS3DHTR加速度センサー | Buddyの視線、シェイク検出 |
| 光センサー | Buddyの背景と瞳孔の変化 |
| ブザー | 感情音とゲーム効果音 |
| USB Type-C | 電源、書き込み、シリアル診断 |
| RTL8720DN | ローカルWi-Fi AP、Webサーバー、DNS |

## システム構成

```text
スマホのChrome
  ├─ 現在時刻・タイムゾーンを送信
  └─ Buddy操作をHTTPで送信
              │
              │ Wi-Fi: Wio-Buddy / WPA2
              ▼
Wio Terminal RTL8720DN
  ├─ アクセスポイント 192.168.4.1
  ├─ DNSキャプティブポータル
  └─ HTTP Webサーバー
              │ eRPC
              ▼
ATSAMD51 メインアプリ
  ├─ 4アプリランチャー
  ├─ Buddy・時計
  ├─ Tetris
  ├─ Space Invaders
  └─ Mini RPG
              │
              ▼
LCD・ボタン・加速度・光・ブザー
```

家庭のWi-Fi、クラウド、外部サーバーは使わない。時刻はスマホのJavaScriptからUnix epochとタイムゾーンを受け取り、`millis()`との差分で進めている。

## ソース構成

| ファイル | 役割 |
|---|---|
| `src/main.cpp` | 起動、ランチャー、Buddy、Tetris、共通入力・センサー・描画 |
| `src/invaders.cpp` / `.h` | Space Invaders |
| `src/rpg.cpp` / `.h` | Mini RPG |
| `src/smart_link.cpp` / `.h` | Wi-Fi AP、DNS、Web UI、HTTP API、時計同期 |
| `src/app_shared.h` | アプリ間で共有する定義 |
| `platformio.ini` | Wio Terminal向けビルド設定と依存ライブラリ |
| `README.md` | 操作方法、ビルド、書き込み手順 |
| `LOG.md` | 実装・検証ログ |

## 開発環境と依存関係

- PlatformIO Core 6.1.19
- `atmelsam` / `seeed_wio_terminal`
- Arduino framework
- Seeed Arduino rpcWiFi 1.1.0
- Grove LIS3DHTR 1.2.4
- Wio Terminal用Seeed_Arduino_LCD 1.6.0

ビルドと書き込み:

```bash
cd /home/sato/dev/seeed/tetris
~/.platformio/penv/bin/platformio run
~/.platformio/penv/bin/platformio run --target upload --upload-port /dev/ttyACM0
```

シリアル診断:

```bash
~/.platformio/penv/bin/platformio device monitor --port /dev/ttyACM0 --baud 115200
```

2秒ごとに次のような診断が出る。

```text
mode=menu fb=8bit accel=ok xyz=... light=... wifi=ready clock=waiting
```

- `wifi=ready`: スマホ連携用APが起動済み
- `clock=waiting`: スマホページを開く前
- `clock=synced`: スマホから時刻同期済み

## メモリと最終書き込み結果

| 項目 | 使用量 | 割合 |
|---|---:|---:|
| 静的RAM | 61,136 / 196,608 bytes | 31.1% |
| Flash | 128,136 / 507,904 bytes | 25.2% |
| 実機へ書き込んだバイナリ | 129,168 bytes | Flash検証成功 |

Wi-Fiライブラリが静的RAMを使うため、裏画面は16bitから8bitへ変更した。320×240の8bitフルスクリーンスプライトを動的確保し、ダブルバッファによるちらつき防止を維持しながら約77KBを節約している。

## 解決したトラブル

### 1. 音は鳴るが画面が真っ暗

**原因:** PlatformIOがWio Terminal専用LCD実装ではなく、ピン設定のない汎用`TFT_eSPI`を選んでいた。

**対処:** 汎用依存を外し、Arduinoフレームワークに含まれるWio Terminal専用`Seeed_Arduino_LCD`を使うよう修正した。

### 2. 約3秒ごとの画面フリッカー

**原因:** 診断更新に合わせてランチャー全体を定期的に再描画していた。

**対処:** メニューは起動時と入力で選択が変わったときだけ描画するようにした。

### 3. キャラクターやゲームが1コマ動くたびにちらつく

**原因:** 描画途中の矩形や文字がLCDへ直接見えていた。

**対処:** RAM上で1フレームを完成させてからLCDへ一括転送するダブルバッファ方式へ変更した。Wi-Fi追加後は8bitバッファへ縮小した。

### 4. 内蔵加速度センサーを検出できない

**原因:** Grove向け`Wire`を使っており、内蔵センサーが接続されたI2Cバスと異なっていた。

**対処:** `Wire1`へ変更し、基板差に対応するため`0x19`と`0x18`の両アドレスを試すようにした。この実機では`Wire1 / 0x18`で応答した。

### 5. Wi-Fi初期化でアプリが停止する

**原因:** RTL8720DN側の無線ファームウェアがrpcWiFiのeRPC方式に未対応だった。

**対処:** Seeed公式`ambd_flash_tool` v0.6.0で無線コアを消去し、eRPC対応ファームウェアを書き込んだ。その後ATSAMD51へ本アプリを再書き込みした。

公式手順: [Wio Terminal Network Overview](https://wiki.seeedstudio.com/Wio-Terminal-Network-Overview/)

> [!important] 無線ファーム更新時
> 更新ツールはATSAMD51へ一時的なUSBシリアル中継プログラムを書き込む。無線コア更新後は、Wio Buddy Arcadeをもう一度uploadする必要がある。

## 実機で確認したこと

- USB ID: `2886:802d Seeed Wio Terminal`
- シリアルポート: `/dev/ttyACM0`
- LCD表示
- 4アプリのランチャー
- 加速度センサーの継続取得
- 光センサー値の取得
- ブザー
- Flash書き込みとVerify
- `wifi=ready`の継続出力
- `Wio-Buddy`がWPA2、電波強度100%で検出されること
- PCから`Wio-Buddy`へ接続できること

## Git履歴

主要コミット:

| Commit | 内容 |
|---|---|
| `b5893d7` | 初期Tetris試作を保存 |
| `ca19fd3` | BuddyとTetrisの統合ランチャー |
| `50ee12b` | 内蔵センサー検証と操作改善 |
| `f2a05cc` | Wio Terminal専用LCDドライバへ修正 |
| `393117e` | 周期的なメニュー再描画を停止 |
| `338dfce` | ダブルバッファ描画 |
| `f5e8d87` | Space Invaders追加 |
| `7dacf22` | 4アプリランチャーとMini RPG追加 |
| `0dc72c1` | 4アプリの実機検証を記録 |
| `33cd634` | スマホリモコンとBuddy時計 |
| `797545e` | 無線コア更新と最終検証を記録 |

詳細な時系列は [[Assistant/Projects/Wio Buddy Arcade/logs|作業ログ]] を参照。

## 現在の制約

- `Wio-Buddy`接続中は、そのWi-Fi経由でインターネットへは出られない
- 時計はRTCへ永続保存していないため、電源を切ると再同期が必要
- SSIDとパスワードはファームウェアへ固定で入っている
- スマホWeb UIはローカル接続専用で、HTTPSやユーザー認証は使わない
- ゲームのセーブデータやRPG進行状況は電源断後に保持しない

## 今後の拡張候補

- RTCまたはNTPによる電源再投入後の時計維持
- 家庭内Wi-Fiへ参加するSTAモードと、現在のAPモードの切り替え
- スマホ側にBuddyの現在の感情・センサー値をリアルタイム表示
- 明るさや傾きのグラフ表示
- Webからゲーム選択、スコア表示、難易度設定
- FlashへハイスコアとRPG進行を保存
- SSIDとパスワードの設定画面
