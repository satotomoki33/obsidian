# LattePandaのWi-Fi IPを192.168.11.11に固定する手順

#robocon #programming #memo

## 目的

新しいLattePandaがBUFFALOルーターから一時的なDHCPアドレスを受け取っている状態から、PCだけを使ってSSH経由で `192.168.11.11` に固定する。

- PC側のSSH設定は変更しない
- ラテパンへモニターやキーボードを直接つながない
- 再起動後も `192.168.11.11` を維持する

## 前提

```text
SSHユーザー: hinji
Wi-Fiインターフェース: wlo1
固定するIP: 192.168.11.11/24
ルーター: 192.168.11.1
SSHエイリアス: lattepanda-r1
```

PCの `~/.ssh/config`:

```sshconfig
Host lattepanda-r1
  HostName 192.168.11.11
  User hinji
```

> [!warning]
> 旧ラテパンや別の機器が `192.168.11.11` を使用していない状態で作業する。

## 手順

### 1. 新しいラテパンの仮IPを確認する

#### PC側で実行

ルーターの接続端末一覧を見るか、PCの近隣テーブルを確認する。

```bash
ip neigh
```

必要ならネットワークを走査する。

```bash
nmap -sn 192.168.11.0/24
```

例として、新しいラテパンの仮IPが `192.168.11.5` だった場合、次へ進む。

### 2. 仮IPへSSHする

#### PC側で実行

```bash
ssh hinji@192.168.11.5
```

以降、SSH内で実行するコマンドは、PCのキーボードから入力するが、実行先はラテパン側になる。

### 3. 使用中のWi-Fi接続UUIDを取得する

#### ラテパン側（SSH内）で実行

```bash
UUID=$(nmcli -g GENERAL.CON-UUID device show wlo1)
echo "$UUID"
```

現在使用中の接続も確認する。

```bash
nmcli -f NAME,UUID,DEVICE connection show --active
```

接続名が重複していても、以降はUUIDを使うため問題ない。

### 4. 固定IPを保存する

#### ラテパン側（SSH内）で実行

`ipv4.method manual` とアドレスは、必ず同じコマンド内で設定する。

```bash
sudo nmcli connection modify "$UUID" \
  ipv4.addresses "192.168.11.11/24" \
  ipv4.gateway "192.168.11.1" \
  ipv4.dns "192.168.11.1 1.1.1.1" \
  ipv4.method manual \
  connection.autoconnect yes \
  connection.autoconnect-priority 100
```

保存内容を確認する。

```bash
nmcli -g ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.dns,connection.autoconnect \
  connection show "$UUID"
```

期待する出力:

```text
manual
192.168.11.11/24
192.168.11.1
192.168.11.1,1.1.1.1
yes
```

この段階では設定が保存されただけで、現在のSSH接続はまだ仮IPを使用している。

### 5. SSH切断後も処理が続く形でWi-Fiを再接続する

#### ラテパン側（SSH内）で実行

```bash
sudo systemd-run \
  --unit=lattepanda-ip-switch \
  --on-active=5s \
  -- /bin/sh -c "nmcli connection down '$UUID'; sleep 2; nmcli connection up '$UUID'"
```

次のように表示されればタイマー登録成功。

```text
Running timer as unit: lattepanda-ip-switch.timer
```

約5秒後にWi-Fiが切り替わり、SSHが停止または切断される。これは正常。

SSH端末が固まった場合は、新しいPC側ターミナルを開く。必要なら、SSH端末でEnterを押してから次を入力して強制切断する。

```text
~.
```

### 6. PCのARPキャッシュを消す

#### PC側で実行

```bash
sudo ip neigh flush to 192.168.11.11
```

旧ラテパンのMACアドレス情報がPCに残っている場合に備えて実行する。

### 7. `192.168.11.11` へ接続する

#### PC側で実行

```bash
ping -c 3 192.168.11.11
```

疎通できたらSSHする。

```bash
ssh lattepanda-r1
```

直接指定する場合:

```bash
ssh hinji@192.168.11.11
```

### 8. 最終確認

#### ラテパン側（新しいSSH内）で実行

```bash
ip -4 -br addr show wlo1
ip route
nmcli -f NAME,UUID,DEVICE connection show --active
```

期待する状態:

```text
wlo1  UP  192.168.11.11/24
```

```text
default via 192.168.11.1 dev wlo1
```

保存設定を確認する。

```bash
UUID=$(nmcli -g GENERAL.CON-UUID device show wlo1)
nmcli -g connection.autoconnect,ipv4.method,ipv4.addresses connection show "$UUID"
```

期待する出力:

```text
yes
manual
192.168.11.11/24
```

この状態なら、ラテパン再起動後も通常は `192.168.11.11` で自動接続する。

## 新しいラテパンでSSHホスト鍵が変わった場合

PC側で次のエラーが出ることがある。

```text
REMOTE HOST IDENTIFICATION HAS CHANGED
```

#### PC側で実行

```bash
ssh-keygen -R 192.168.11.11
ssh-keygen -R lattepanda-r1
ssh lattepanda-r1
```

## 「シークレットが必要でしたが入力されていません」と出る場合

Wi-Fiパスワードが接続プロファイルに保存されていない可能性がある。

#### ラテパン側（SSH内）で実行

新しい接続プロファイルを作成し、Wi-Fiパスワードを端末から入力する。

```bash
sudo nmcli --ask device wifi connect "Buffalo-6G-DE80" \
  ifname wlo1 \
  name "Buffalo-6G-DE80-recovery"
```

パスワード入力中は文字が表示されなくても正常。その後は、新しく作成された接続のUUIDを取得し、上記の固定IP設定を行う。

```bash
UUID=$(nmcli -g GENERAL.CON-UUID device show wlo1)
echo "$UUID"
```

## 注意点

この設定はラテパン側では恒久的だが、ルーター側に旧ラテパンのMACアドレスと `192.168.11.11` の固定割り当てが残っている場合は、旧ラテパンを同じネットワークへ接続しない。

長期的には、BUFFALOルーターの固定割り当てを新ラテパンのMACアドレスへ更新し、ラテパン側をDHCP運用に戻す構成が最も安全。