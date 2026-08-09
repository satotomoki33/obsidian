# SSH切断後にROSを停止する

#memo #robocon

## 目的

SSH元のPCや端末が落ちて `Ctrl+C` を送れなくなり、R1側に `ros2 launch` やROSノードだけが残ったときに、再起動せず停止するための手順。

## 1. R1へSSHし直す

```bash
ssh ubuntu@<R1のIP>
```

## 2. 残っているROSプロセスを確認する

```bash
pgrep -af ros
```

DOG3周辺だけ見たい場合は、例えば次でもよい。

```bash
pgrep -af "dog3|ros2"
```

表示されたPIDとコマンドを確認し、止めたい `ros2 launch` を特定する。

## 3. Ctrl+C相当のSIGINTを送る

PIDを指定する場合:

```bash
kill -SIGINT <PID>
```

例:

```bash
kill -SIGINT 12345
```

起動コマンドを十分絞り込める場合は `pkill` でもよい。

```bash
pkill -SIGINT -f "ros2 launch dog3_rtcl dog3.launch.py"
```

`SIGINT` は通常の `Ctrl+C` とほぼ同じ扱いなので、まずこれを使う。`ros2 launch` の親プロセスに送れば、通常は配下のノードも終了処理に入る。

## 4. 止まらない場合

次の順で強くしていく。

```bash
kill -SIGINT <PID>
kill -SIGTERM <PID>
kill -SIGKILL <PID>
```

- `SIGINT`: Ctrl+C相当。最優先
- `SIGTERM`: 通常終了要求
- `SIGKILL`: 強制終了。最後の手段

ロボットでは、終了処理やモータ停止処理を飛ばす可能性があるため、いきなり `SIGKILL` は使わない。

## 5. 停止確認

```bash
pgrep -af "dog3|ros2"
```

必要ならROS側も確認する。

```bash
ros2 node list
```

## 注意

一般的なROS 2ノードには、すべてのノードを対象にした `ros2 node kill /node_name` のような汎用停止コマンドはない。基本的にはLinux側のプロセスへシグナルを送る。

次のような広すぎる指定は、ROS daemonや関係ないプロセスまで巻き込む可能性があるため避ける。

```bash
pkill -f ros
```

できるだけPID、launchファイル名、パッケージ名などで対象を絞る。

## 予防: tmuxでROSを起動する

長時間動かすROSは `tmux` 内で起動しておくと、SSHが切れても端末セッションがR1側に残る。

起動:

```bash
tmux new -s dog3
```

その中でROSを起動する。

```bash
ros2 launch ...
```

PCが落ちたりSSHが切れたあと、再接続して復帰する。

```bash
tmux attach -t dog3
```

元の端末画面に戻れるので、そのまま `Ctrl+C` で正常終了できる。

### tmuxセッション確認

```bash
tmux ls
```
