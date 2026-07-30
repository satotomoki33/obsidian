# neko1 ARカメラ確認

#robocon #memo

## 概要

neko1（lattepanda-r2）に接続されているAR通信用カメラと、KFSC用カメラのROS画像トピックを確認した記録。

- AR通信用カメラ: `See3CAM_37CUGM` × 2台
- KFSC用前方カメラ: `GMSL2-USB3.0 Conversion Kit`
- ROS 2ワークスペース: `tutrobo/abu2026-ros2-ws`
- 対象launch: `src/hardware/neko1/neko1_rtcl/launch/neko1.launch.py`

## カメラデバイスを見つける手順

### 1. カメラ名と `/dev/video*` の対応を確認

```bash
v4l2-ctl --list-devices
```

実機での確認結果:

```text
GMSL2-USB3.0 Conversion Kit (usb-0000:00:0d.0-1):
    /dev/video0
    /dev/video1
    /dev/media0

See3CAM_37CUGM (usb-0000:00:14.0-3.3):
    /dev/video2
    /dev/video3
    /dev/media1

See3CAM_37CUGM (usb-0000:00:14.0-3.4):
    /dev/video4
    /dev/video5
    /dev/media2
```

したがって、AR用See3CAMは次の2台。

| USBポート | 主に使うVideoデバイス | 別インターフェース |
|---|---|---|
| `3.3` | `/dev/video2` | `/dev/video3` |
| `3.4` | `/dev/video4` | `/dev/video5` |

通常は `video-index0` に対応する `/dev/video2` と `/dev/video4` を使う。

### 2. 再起動後も安定しやすいby-pathを確認

```bash
ls -l /dev/v4l/by-path/ | grep video
```

実機での対応:

```text
/dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-video-index0
  -> /dev/video2

/dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.4:1.0-video-index0
  -> /dev/video4
```

ARカメラの設定には、`/dev/video2` や `/dev/video4` よりも以下を使う方が安全。

```text
/dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-video-index0
/dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.4:1.0-video-index0
```

### 3. それぞれの映像を直接見る

```bash
ffplay -f v4l2 \
  -i /dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-video-index0
```

```bash
ffplay -f v4l2 \
  -i /dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.4:1.0-video-index0
```

片方ずつレンズを手で隠し、USB `3.3` と `3.4` のどちらが左・右か確認する。

映像が開けない場合は、対応フォーマットを確認する。

```bash
v4l2-ctl -d /dev/video2 --list-formats-ext
v4l2-ctl -d /dev/video4 --list-formats-ext
```

## neko1.launch.pyの現在の設定

`ar_comm_camera` は現在、次のデバイスパスを開く設定になっている。

```text
ar_comm_camera_1:
/dev/v4l/by-path/pci-0000:00:14.0-usb-0:6:1.0-video-index0

ar_comm_camera_2:
/dev/v4l/by-path/pci-0000:00:14.0-usb-0:9:1.0-video-index0
```

一方、現在のlattepanda-r2で実在するSee3CAMのパスは `0:3.3` と `0:3.4`。

そのため、現行launchの `0:6` / `0:9` と実機構成が一致していない。カメラノードが起動してもデバイスを開けず、画像トピックが流れない可能性がある。

## 左右の割り当て

`ar_receiver` 側では次の対応になっている。

```text
ar_comm_camera_1 = 右カメラ
ar_comm_camera_2 = 左カメラ
kfsc_detector    = 前方カメラ
```

したがって、実映像を確認してから以下のように割り当てる。

例: USB `3.3` が右、USB `3.4` が左の場合

```text
ar_comm_camera_1:
/dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-video-index0

ar_comm_camera_2:
/dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.4:1.0-video-index0
```

左右が逆なら `3.3` と `3.4` を入れ替える。

## ROS画像トピックの確認

### トピック一覧

```bash
ros2 topic list | grep -E 'ar_comm_camera|kfsc_detector|image'
```

ノードが起動しているか確認:

```bash
ros2 node list | grep ar_comm_camera
ros2 node info /r2/ar_comm_camera_1
ros2 node info /r2/ar_comm_camera_2
```

### rqt_image_viewで見る

```bash
ros2 run rqt_image_view rqt_image_view
```

ARカメラが画像をpublishしている場合、プルダウンから次のトピックを選ぶ。

```text
/r2/ar_comm_camera_1/image_raw
/r2/ar_comm_camera_2/image_raw
```

実際のトピック名は次で確認する。

```bash
ros2 topic list | grep ar_comm_camera
```

画像のpublish周期を確認:

```bash
ros2 topic hz /r2/ar_comm_camera_1/image_raw \
  --qos-reliability best_effort

ros2 topic hz /r2/ar_comm_camera_2/image_raw \
  --qos-reliability best_effort
```

ARカメラは設定上10 fpsの想定。

## KFSC用カメラの画像トピックの違い

### `preview_image/compressed`

```text
/r2/kfsc_detector/preview_image/compressed
```

- カメラから取得した映像を軽量化して表示する確認用画像
- YOLOの枠は描画されない
- カメラの接続、画角、向きの確認に使う
- 現在の設定は10 fps、0.5倍縮小、JPEG品質60

### `debug_image/compressed`

```text
/r2/kfsc_detector/debug_image/compressed
```

- クロップと歪み補正後にYOLO推論を実施
- 検出した物体の枠、Class ID、confidenceを描画
- KFSC認識結果の確認に使う
- Action版では`DetectKfsc`アクション実行時にYOLO処理が走るため、待機中は更新されない場合がある
- 現在は圧縮画像のみ有効、5 fps

### `aruco_filter_debug_image/compressed`

```text
/r2/kfsc_detector/aruco_filter_debug_image/compressed
```

- 前方カメラで検出したArUco候補のフィルタ結果を描画
- 緑: 採用
- 赤: 小さすぎて除外
- `id=<ID> side=<px> OK/SMALL` を表示
- 現在の最小辺しきい値は25 px
- マーカー候補があり、かつsubscriberがいる場合にpublishされる

## 確認用コマンドまとめ

```bash
# カメラ名とvideo番号
v4l2-ctl --list-devices

# USBポートごとの安定パス
ls -l /dev/v4l/by-path/ | grep video

# See3CAMの対応形式
v4l2-ctl -d /dev/video2 --list-formats-ext
v4l2-ctl -d /dev/video4 --list-formats-ext

# 直接映像確認
ffplay -f v4l2 -i \
  /dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-video-index0

ffplay -f v4l2 -i \
  /dev/v4l/by-path/pci-0000:00:14.0-usb-0:3.4:1.0-video-index0

# ROSノード・トピック確認
ros2 node list | grep ar_comm_camera
ros2 topic list | grep -E 'ar_comm_camera|image'

# ROS画像表示
ros2 run rqt_image_view rqt_image_view
```

## 決定事項

- AR通信用カメラは2台の`See3CAM_37CUGM`。
- 現在の実機ではUSB `3.3`が`/dev/video2`、USB `3.4`が`/dev/video4`の`video-index0`に対応する。
- launchでは`/dev/v4l/by-path/`を使う。
- `ar_comm_camera_1`は右、`ar_comm_camera_2`は左として割り当てる。
- カメラ自体の確認はまずV4L2/ffplay、ROS経由の確認は`rqt_image_view`を使う。

## 未解決事項

- USB `3.3`と`3.4`のどちらが物理的な左・右カメラかを映像で確定する。
- 左右確定後、`neko1.launch.py`の`device_id`を`0:3.3` / `0:3.4`へ修正する。
- 修正後に両`image_raw`がpublishされ、約10 Hzで流れることを確認する。
