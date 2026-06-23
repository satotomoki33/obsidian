
rotatorの角度
デフォ -0.25
組み立て -0.5


シーケンス並行移動
自動配置ちょいずれてるzumi
もうちょい手前にしたいzumi
L2(減速)押してると左ハンドうごかない？済
* [ ] シーケンス並行移動
* [ ] ARにキーコンを対応
* [x] KFSの配置のとき引いて出すのにラグがある
* [ ] R1の再合体
* [ ] 道場リトライからのバク即復帰
* [ ] リトライのときは閉じた状態からスタートかも
* [ ] 上位シーケンスが呼び出すもの
	* [ ] 槍回収



```
その悩みはもっともで、結論だけ言うと、単に make 系に寄せるだけでは同時送信にはならないです。make は「メッセージを組み立てるだけ」なので、2つ以上の値を同時に反映したいなら、組み立て前にまとめて反映するか、1回で publish する専用の入口が必要です。

命名の方針としては、私は次のどれかが筋がいいと思います。

1. make 系に寄せるなら、戻り値で完全なメッセージを作る
   つまり、個別の set を増やすのではなく、呼び出し側が必要な項目を全部埋めたあとに 1 回だけ publsrc/hardware/dog3/dog3_rtcl/config/params/dog3_kfs_place.yamlish する形です。  
   これは今の実装方針に近くて、名前も長くなりにくいです。

2. set ではなく update / apply / compose を使う
   set は「その値だけ確定させる」感じが強いので、複数項目の同時反映には少し弱いです。  
   例えばこういう語感が合います。
   - compose_kfs_target_command
   - update_kfs_target_command
   - apply_kfs_target_changes
   - merge_kfs_target_command

3. 同時反映専用の短いドメイン名を切る
   たとえば今回の用途が「開きながら deploy」なら、一般化しすぎずに
   - set_kfs_open_and_deploy_command
   - set_kfs_hand_deploy_command
   - set_kfs_opening_command
   みたいに、意味をそのまま短くした方が読みやすいことも多いです。

私なら、汎用化したいなら update / compose、用途固定なら open_and_deploy のような専用名にします。  
逆に make_staff_roller_target_command みたいな pure helper と set_* の二段構えは、責務が分かれていて悪くないです。なので「make が長いから嫌」という悩みは、名前を短くするよりも、役割を純粋関数と副作用関数で分ける方が解決しやすいです。

必要なら次に、今のコードに合わせて「このパッケージならどの命名が一番自然か」を 3 案くらいに絞って出せます。
```

## Dog3
 - [x] キモい名前のaltanativeを変更、msg型に合わせる
 - [x] decleareparameterをどうにかする
 - [x] gemini戦
 - [ ] コントローラーサーバーこねこね
	 - [x] トリガーつける
	 - [x] MANUAL->AUTOにタイムアウトつける
 - [x] pitchとHANDopencloseの成功判定ってつけてたっけ
 - [x] use_weaponとkfs_placeのマジックナンバー探す
 - [x] use_weaponのwaitsettleいらない
 - [ ] コントローラーのAUTOとMANUAL切り替えたときの機構の動き

 - [ ] MANUALのキーコン
	 - [ ] step_dockingを作る
	 - [ ] KFS_collectシーケンスでさげるのが足りない
 - [ ] マトリクスワンチ
	 - [ ] executor 側は作ってあるから、required 側、ROS側の部分を書く
	       aruco_sender_block
 - [ ] コントローラーでマトリクス呼び出す
 - [ ] スタッフ回収

### 手動キーコン
槍昇降
* 配列で渡してその順番でうごくようにする 
	* 42-108
槍回転
* 配列で渡してその順番で動くようにする
槍押出
* 抜け落ちるまで押し出す。もとの位置まで戻る
KFS昇降
* 配列で渡してその順番でうごくようにする
KFS展開
* 01でいんじゃね


make_staff_roller_target_command_msg
publish_staff_roller_target_command
って分けないといけないん？

問題点
right_triggerで毎回ローラーが起動するようになってる
ローラーの目標値がどんどんたされていってる

調整ハンドはトグル関数
```
dog3_controller_server

process_manual_mode_inputに手動操縦を実装する

staff_liftはdpad_up_button 、dpad_down_buttonで上下させる。目標値は配列で渡したやつをボタンを押すたびに順番に遷移させていく。最大まで行けばそこで、それ以上は行かないし、最小まで行けばそれ以上は下がらない。

staff_rotatorはBで正の方向に回転。right_trigger押しながらBで負の方向に回転。目標値は同じように配列を渡す

staff_rollerはAである位置まで回転。right_triggerでもとの位置にもどる。なおこのある位置まで回転は、ボタンを押した時点の位置を０とした相対位置である。

それぞれの関数をどこに作るかは一旦相談したいので案を取り敢えず出してみてほしい
```



## Dog2KfsPlaceNode の実装を新しいシステムに揃えたい
#### 要件
* シーケンスのためのノードは作らない
* src/hardware/rtclを用いて実装する
* asl::util::StateMachineを使う
* src/hardware/dog2/dog2/include/dog2の直下にkfs_place_sequenceとuse_weapon_sequenceの2つのディレクトリを作って実装する。
* placeとuse_weaponは分ける
* neko1_rtclの実装を参考にしたい

**rtclでの実装に関して**
まだ完全に理解しきってないから先輩にどんな感じで使えば良いのか聞いてみた
* read writeを使っていい感じにするらしい
* topic のpubsubとactionのクライアントだったりサーバーだったりをrtclだけでつくれるのか知りたい。できそうならこのまま実装を進める。できなそうなら相談


### 実装に必要なもの


シーケンサの実装をrtclでやるのって必須なん？
node依存自体を減らす方針
機構のシーケンスと足回りは分けたほうが良い？
機構のシーケンス自体はややこしくないから足とまとめても良いかも

### R1のシーケンスの実装方針
* スタッフ回収、組み立てのシーケンス
* KFS自動回収のシーケンス
* 槍使用のシーケンス
* KFS配置のシーケンス
これらのシーケンスを分けてそれぞれにノードを作って実装する

明日の朝までにやること
動作確認

### 修正点

weaponassembleやっぱり復帰出来ないのカス pose_holdが悪い説を提唱

##### 悪いのcreate_action_serverっぽい
PoseHold の書き方だけが悪いというより、RTCL の action wrapper が Canceled result を
goal_handle->canceled() に変換するときに、goal が CANCELING 状態か確認していないのが根本原因だと思います。
Approach / FollowTrajectory では cancel 完了までに自然な遅延があるため表面化していませんが、
PoseHold は cancel 後すぐに Canceled result を返すため、EXECUTING のまま canceled() を呼んでしまい、
invalid transition が発生しているように見えます。
https://chatgpt.com/c/6a0a8a4e-60bc-83a4-9644-f48fd8921a6a





キャリブレーションありでスタートするときと、なしでスタートするときが必要なのでは

-0.5

さっきやったこと
