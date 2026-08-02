# DOG3 LiDAR IP設定・接続確認手順

#robocon #memo

## 概要

DOG3（lattepanda-r1）の2台のHOKUYO LiDARについて、接続確認、IP不一致の切り分け、WindowsのIP Discoveryを使ったIP変更、ROS 2での最終確認までをまとめる。

今回の原因は次の2点だった。

- 左LiDAR本体が旧IP `192.168.0.12` のままで、ROS設定の `192.168.1.12` と一致していなかった
- 右LiDAR `192.168.0.10` は一時的に応答しなくなったが、LiDAR本体の再起動で復旧した

## 最終的なネットワーク構成

| 接続 | LattePanda側 | LiDAR側 | ROSノード |
|---|---|---|---|
| 右LiDAR | `enp2s0`: `192.168.0.1/24` | `192.168.0.10` | `/r1/urg_node_0` |
| 左LiDAR | `enp1s0`: `192.168.1.1/24` | `192.168.1.12` | `/r1/urg_node_1` |

ROS側の設定ファイル:

```text
src/hardware/dog3/dog3_rtcl/config/params/sensors.yaml
```

想定設定:

```yaml
/r1/urg_node_0:
  ros__parameters:
    ip_address: "192.168.0.10"
    laser_frame_id: "r1_right_lidar"
    publish_multiecho: true

/r1/urg_node_1:
  ros__parameters:
    ip_address: "192.168.1.12"
    laser_frame_id: "r1_left_lidar"
    publish_multiecho: true
```

---

## 1. LattePanda側の基本確認

以下はすべて `lattepanda-r1` で実行する。

### ホスト名とNICを確認

```bash
hostname
ip -br link
ip -br addr
ip route
```

現在の正常例:

```text
lattepanda-r1

enp1s0 UP 192.168.1.1/24
enp2s0 UP 192.168.0.1/24
```

### 物理リンクを確認

```bash
for dev in enp1s0 enp2s0; do
  echo "=== $dev ==="
  cat /sys/class/net/$dev/carrier
 done
```

結果:

```text
1 = LANの電気的リンクあり
0 = ケーブル未接続、電源OFF、接触不良など
```

`carrier=1` や `LOWER_UP` は、LANの電気的リンクがあることだけを示す。LiDAR本体の制御部やIP通信が正常とは限らない。

---

## 2. LiDARへの接続確認

### 通常のping

```bash
# 右LiDAR
ping -c 3 -I enp2s0 192.168.0.10

# 左LiDAR
ping -c 3 -I enp1s0 192.168.1.12
```

正常時は `0% packet loss` になる。

### ARPで直接確認

pingが通らない場合は `arping` を使う。

```bash
sudo arping -I enp2s0 -c 3 192.168.0.10
sudo arping -I enp1s0 -c 3 192.168.1.12
```

旧IPの可能性も確認する。

```bash
sudo arping -I enp1s0 -c 3 192.168.0.12
```

今回、左LiDARは次の応答を返した。

```text
192.168.0.12 [00:1D:9B:1E:8E:E9]
```

これにより、左LiDAR本体が旧IP `192.168.0.12` のままだと確定した。

### 既知IPを総当たりする

```bash
for dev in enp1s0 enp2s0; do
  for ip in 192.168.0.10 192.168.0.12 192.168.1.12; do
    echo
    echo "=== $dev -> $ip ==="
    sudo arping -I "$dev" -c 2 -w 3 "$ip"
  done
done
```

これで、どのLiDARがどのNICに接続されているかを確認できる。

### `arping`だけ通る理由

`arping` はEthernet層で直接問い合わせるため、送信元と相手が別サブネットでも応答を見つけられることがある。

一方、通常のpingやROS通信では、次のように同じサブネットへそろえる必要がある。

```text
192.168.0.1 ↔ 192.168.0.10
192.168.1.1 ↔ 192.168.1.12
```

---

## 3. 右LiDARが突然見えなくなった場合

今回、右LiDARはLANケーブルを抜き差しした後、`carrier=1` のままARP応答がなくなった。

まずNICを再起動する。

```bash
sudo ip link set enp2s0 down
sleep 2
sudo ip link set enp2s0 up
sleep 5
sudo ip neigh flush dev enp2s0
sudo arping -I enp2s0 -c 5 192.168.0.10
```

それでも戻らなければ、LiDAR本体の電源をOFFにし、約10秒待ってからONにする。

今回の右LiDAR `192.168.0.10` は、本体再起動で復旧した。

---

## 4. Windows PCをLiDAR設定用に準備する

対象LiDARだけをWindows PCへ有線接続する。右LiDARと間違えないよう、左LiDARだけを接続する。

### `ncpa.cpl` を開く

1. `Win + R`
2. 次を入力してEnter

```text
ncpa.cpl
```

3. `イーサネット 2` を右クリック
4. `プロパティ`
5. `インターネット プロトコル バージョン4 (TCP/IPv4)`
6. `プロパティ`

### Windows側の固定IP

変更前の左LiDARが `192.168.0.12` なので、PCも同じ `192.168.0.x` にする。

```text
次のIPアドレスを使う

IPアドレス:          192.168.0.2
サブネットマスク:    255.255.255.0
デフォルトゲートウェイ: 空欄
DNS:                 空欄
```

設定後、PowerShellまたはコマンドプロンプトで確認する。

```powershell
ipconfig
```

正常例:

```text
イーサネット 2
IPv4アドレス: 192.168.0.2
サブネットマスク: 255.255.255.0
```

### `192.168.137.1` になっている場合

Windowsのモバイルホットスポットやインターネット接続共有によって、Ethernetが自動的に `192.168.137.1` になることがある。

以下を確認する。

```text
設定
→ ネットワークとインターネット
→ モバイル ホットスポット
→ オフ
```

または、`ncpa.cpl` でWi-Fiの共有設定を確認する。

```text
Wi-Fiを右クリック
→ プロパティ
→ 共有
→ 「ネットワークのほかのユーザーに…」のチェックを外す
```

その後、再び `イーサネット 2` を `192.168.0.2/24` に設定する。

---

## 5. IP DiscoveryでLiDARのIPを書き換える

### インターフェース選択

IP Discoveryを起動し、最初の画面では `Wi-Fi` ではなく `イーサネット 2` を選ぶ。

正しい表示:

```text
イーサネット 2
IPアドレス: 192.168.0.2
ネットワークマスク: 255.255.255.0
```

### 対象センサを確認

今回の左LiDAR:

```text
シリアル番号: H2308956
現在IP: 192.168.0.12
MACアドレス: 00:1D:9B:1E:8E:E9
```

LattePandaの `arping` で確認したMACと一致することを確認する。

### 書き込み内容

IPアドレス設定画面で次を入力する。

```text
IPアドレス:       192.168.1.12
ネットワークマスク: 255.255.255.0
ゲートウェイ:       192.168.1.1
書き込み対象:       チェックあり
```

その後、`書き込み` を押す。

注意:

- 右上の `出荷状態にリセット` は押さない
- `書き込み対象` のチェックを忘れない
- 画面下の `ベースアドレス` は変更しない
- 書き込み後、PCは `192.168.0.2`、LiDARは `192.168.1.12` になるため、一覧からLiDARが消える場合がある。これは正常

### 書き込み失敗の見分け方

書き込み後に再検出され、すぐ次の旧設定へ戻る場合は、書き込みできていない可能性が高い。

```text
IPアドレス: 192.168.0.12
ゲートウェイ: 192.168.0.1
```

その場合は、Windows側Ethernetが本当に `192.168.0.2/24` になっているか確認し、IP Discoveryを再起動して再度書き込む。

---

## 6. 書き込み後の確認

LiDARの電源を再起動し、DOG3へ戻して確認する。

```bash
sudo arping -I enp1s0 -c 3 192.168.1.12
sudo arping -I enp1s0 -c 3 192.168.0.12
```

成功状態:

```text
192.168.1.12 → 応答あり
192.168.0.12 → 応答なし
```

通常のpingも確認する。

```bash
ping -c 3 -I enp1s0 192.168.1.12
```

---

## 7. ROS 2での最終確認

DOG3を起動する。

```bash
ros2 launch dog3_rtcl dog3.launch.py
```

別ターミナルで、実際に読み込まれたIPを確認する。

```bash
ros2 param get /r1/urg_node_0 ip_address
ros2 param get /r1/urg_node_1 ip_address
```

期待値:

```text
/r1/urg_node_0: 192.168.0.10
/r1/urg_node_1: 192.168.1.12
```

LiDARトピックのpublish周期を確認する。

```bash
ros2 topic hz /r1/laser0/last
ros2 topic hz /r1/laser1/last
```

両方で継続的に周波数が表示されれば復旧完了。

---

## 8. 現在のNIC割り当てについて

現在のlattepanda-r1では次の割り当てになっている。

```text
enp1s0 = 192.168.1.1  左LiDAR用
enp2s0 = 192.168.0.1  右LiDAR用
```

GitHub上のNixOS設定では、NIC名とサブネットの割り当てが逆になっている時点があった。ただし、現在の配線とルーティングが上記でそろっていれば、今回の接続不良の直接原因ではない。

チームで物理ポートと左右LiDARの標準対応を確認するまでは、NixOS設定やケーブル配置を不用意に入れ替えない。

---

## 最短確認コマンド

```bash
# NICとIP
ip -br addr

# 右LiDAR
ping -c 3 -I enp2s0 192.168.0.10

# 左LiDAR
ping -c 3 -I enp1s0 192.168.1.12

# ARPで確認
sudo arping -I enp2s0 -c 3 192.168.0.10
sudo arping -I enp1s0 -c 3 192.168.1.12

# ROSトピック
ros2 topic hz /r1/laser0/last
ros2 topic hz /r1/laser1/last
```

## 決定事項

- 右LiDARは `192.168.0.10`
- 左LiDARは `192.168.1.12`
- 左LiDARの旧IP `192.168.0.12` は使用しない
- WindowsでIPを書き込む際は、最初にPC側EthernetをLiDARの現在IPと同じサブネットへ設定する
- `192.168.137.1` のままではなく、今回の設定時は `192.168.0.2/24` を使用する
- `carrier=1` でも通信不能なら、LiDAR本体の電源再起動を試す
