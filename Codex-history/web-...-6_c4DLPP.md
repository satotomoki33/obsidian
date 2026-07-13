---
tags: ["開発", "整理", "ミス", "path/home/sato/robocon/AR_rotate"]
workspace: "/home/sato/robocon/AR_rotate"
conversation_id: "6_c4DLPPf-cyUXrTzzWby"
updated: "2026-07-13T12:46:52.063Z"
---

# 回転をweb上ではなくモーターで回すとしたらどんな仕様だと思う？ まとめ...

Tags: #開発 #整理 #ミス #path/home/sato/robocon/AR_rotate

- Conversation ID: 6_c4DLPPf-cyUXrTzzWby
- Codex Session ID: 019f3d06-2821-7050-9984-8086b7331ad3
- Codex Session Workspace: /home/sato/robocon/AR_rotate
- Codex Session Version: workspace-c-v1
- Workspace: /home/sato/robocon/AR_rotate
- Updated: 2026-07-13T12:46:52.063Z

## Conversation

### user

回転をweb上ではなくモーターで回すとしたらどんな仕様だと思う？
まとめてほしい
速度制御で回して、角度がしきい値になったら0.5秒止めるみたいな感じかな

### assistant

まずリポジトリの構成を軽く確認して、今の「web上の回転」が何を指しているか把握します。その上で、モーター化する場合の仕様案としてまとめます。現状は HTML 側で角度を離散値に変換し、CSS の `transform: rotate(...)` でマーカーを回している構成です。モーター化するなら、この CSS 回転を「目標角度生成」と「実機の速度制御・停止制御」に置き換える仕様として整理するのが自然です。特に `aruco_rotate.html` は「コマンド値を相対角度にして回す」、`aruco_rotate_puls.html` は「45度パルスを複数回送る」設計になっています。実機モーターでは後者のパルス式のほうが、検出側が角度変化を読み取りやすく、停止タイミングも明確にできます。モーターで回すなら、仕様はこんな形が自然だと思います。

**基本方針**

Web上の `rotate()` を、実機では「速度制御で一定角速度回転 → 角度しきい値到達 → 一定時間停止」に置き換える。

今の実装に近いのは [aruco_rotate_puls.html](/home/sato/robocon/AR_rotate/aruco_rotate_puls.html) の方式です。  
45度ずつ回して、必要回数だけパルス的に送る設計。

**仕様案**

- 回転対象: ArUco / AprilTag を貼った円盤、またはマーカー板
- 駆動方式: DCモーター + エンコーダ、またはステッピングモーター
- 制御方式: 速度制御
- 基本角度単位: `45度`
- コマンド値: `0〜7`
- コマンド変換:
  - `1` → 45度
  - `2` → 90度
  - `3` → 135度
  - ...
  - `7` → 315度
  - `0` → 360度、つまり8パルス扱い
- 回転方向: コマンドごと、または送信周期ごとに時計回り / 反時計回りをトグル
- 回転速度: 例 `180 deg/s` または `360 deg/s`
- 停止時間:
  - 45度ごとのパルス停止: `0.15秒`
  - コマンド完了後の停止: `0.5秒`
- 角度到達判定:
  - 目標角度との差がしきい値以下になったら停止
  - しきい値例: `±3〜5度`
- 停止時動作:
  - モーター指令速度を `0`
  - 必要ならブレーキ制御または位置保持
  - `0.5秒` 静止してカメラ側が読み取りやすくする

**状態遷移**

```text
IDLE
  ↓ コマンド入力
ROTATING
  ↓ 角度しきい値到達
HOLDING 0.5秒
  ↓ 次パルスあり
ROTATING
  ↓ 全パルス完了
COMMAND_END_HOLD 0.5秒
  ↓
次コマンド or 繰り返し
```

**制御イメージ**

```text
目標角度 = 現在角度 + 45度

while 回転中:
    角度誤差 = 目標角度 - 現在角度

    if abs(角度誤差) <= しきい値:
        モーター速度 = 0
        0.5秒停止
        次の角度へ
    else:
        モーター速度 = 一定速度
```

個人的には、いきなり「任意角度まで連続回転」より、**45度ごとに止めるパルス式**が良いと思います。カメラが角度変化を読み取りやすく、機械誤差や認識遅延にも強いです。

<details>
<summary>Codex run log</summary>

- status: Codex CLI: codex --ask-for-approval never -C /home/sato/robocon/AR_rotate exec --sandbox workspace-write --skip-git-repo-check --color never --json "<prompt omitted, 77 chars>"
- status: Codex thread: 019f3d06-2821-7050-9984-8086b7331ad3
- status: Codex turn started
- command: /bin/bash -lc 'pwd && rg --files'
- stdout: /home/sato/robocon/AR_rotate
  aruco36_12_0000.png
  aruco36_12_0001.png
  tag36_11_00000_large.png
  aruco_rotate_puls.html
  AR_rotate.html
  AR_rotate_tgg.html
  tag36_11_00001_large.png
  tag36_11_00002_large.png
  AR_rotate_32.html
  aruco_rotate.html
  
- status: Command exited with code 0
- command: /bin/bash -lc 'rg -n "rotate|rotation|angle|theta|web|motor|servo|stepper|回転|角度|速度|threshold|しきい" .'
- stdout: ./aruco_rotate.html:113:    <p>ID:0を固定用Aruco、ID:1を一定角速度で相対角度だけ回転するArucoとして表示します。</p>
  ./aruco_rotate.html:125:            <div class="label marker-title">回転用Aruco / ID: 1</div>
  ./aruco_rotate.html:126:            <div class="aruco-marker" id="rotatingMarker" style="transform: rotate(0deg);">
  ./aruco_rotate.html:129:            <div class="label marker-status">状態: <span id="commandValue">IDLE</span> / 相対回転角: <span id="deltaValue" class="value">-</span></div>
  ./aruco_rotate.html:130:            <div class="label">トグル: <span id="toggleValue" class="value">-</span> / 向き: <span id="rotationDirection" class="value">時計回り</span></div>
  ./aruco_rotate.html:136:            <div class="aruco-marker" style="transform: rotate(0deg);">
  ./aruco_rotate.html:150:        const rotationDirection = document.getElementById('rotationDirection');
  ./aruco_rotate.html:223:            rotationDirection.textContent = directionText;
  ./aruco_rotate.html:229:            rotatingMarker.style.transform = `rotate(${currentAngle}deg)`;
  ./aruco_rotate_puls.html:111:    <p>ID:0を固定用Aruco、ID:1を45度回転パルス列でコマンド送信するArucoとして表示します。</p>
  ./aruco_rotate_puls.html:123:            <div class="label">回転用Aruco<br>ID: 1</div>
  ./aruco_rotate_puls.html:124:            <div class="aruco-marker" id="rotatingMarker" style="transform: rotate(0deg);">
  ./aruco_rotate_puls.html:128:            <div class="label">トグル: <span id="toggleValue" class="value">-</span> / 向き: <span id="rotationDirection" class="value">時計回り</span></div>
  ./aruco_rotate_puls.html:134:            <div class="aruco-marker" style="transform: rotate(0deg);">
  ./aruco_rotate_puls.html:148:        const rotationDirection = document.getElementById('rotationDirection');
  ./aruco_rotate_puls.html:221:            rotationDirection.textContent = directionText;
  ./aruco_rotate_puls.html:227:            rotatingMarker.style.transform = `rotate(${currentAngle}deg)`;
  ./AR_rotate_32.html:65:            /* ここで回転アニメーションを制御 */
  ./AR_rotate_32.html:70:        /* 回転の基準となる上方向の矢印 */
  ./AR_rotate_32.html:96:        .angle-value {
  ./AR_rotate_32.html:104:    <h1>ARマーカー角度通信 シミュレータ (32方向)</h1>
  ./AR_rotate_32.html:105:    <p>0〜1023の数値を入力すると、上位5bitと下位5bitに対応する角度に回転します。</p>
  ./AR_rotate_32.html:118:            <div class="april-tag" id="tagHigh" style="transform: rotate(0deg);">
  ./AR_rotate_32.html:121:            <div class="label">値: <span id="valHigh">0</span> / 角度: <span id="degHigh" class="angle-value">0°</span>
  ./AR_rotate_32.html:127:            <div class="april-tag" id="tagLow" style="transform: rotate(0deg);">
  ./AR_rotate_32.html:130:            <div class="label">値: <span id="valLow">0</span> / 角度: <span id="degLow" class="angle-value">0°</span></div>
  ./AR_rotate_32.html:135:            <div class="april-tag" style="transform: rotate(0deg);">
  ./AR_rotate_32.html:154:        // 1単位あたりの角度（360度 / 32分割）
  ./AR_rotate_32.html:175:            // 角度を計算
  ./AR_rotate_32.html:181:            // CSSのtransformを書き換えて回転させる
  ./AR_rotate_32.html:182:            tagHigh.style.transform = `rotate(${highAngle}deg)`;
  ./AR_rotate_32.html:183:            tagLow.style.transform = `rotate(${lowAngle}deg)`;
  ./AR_rotate_tgg.html:65:            /* ここで回転アニメーションを制御 */
  ./AR_rotate_tgg.html:70:        /* 回転の基準となる上方向の矢印 */
  ./AR_rotate_tgg.html:96:        .angle-value {
  ./AR_rotate_tgg.html:104:    <h1>ARマーカー角度通信 シミュレータ</h1>
  ./AR_rotate_tgg.html:105:    <p>0〜255の数値を入力すると、上位4bitと下位4bitに対応する角度に回転します。</p>
  ./AR_rotate_tgg.html:118:            <div class="april-tag" id="tagHigh" style="transform: rotate(0deg);">
  ./AR_rotate_tgg.html:121:            <div class="label">値: <span id="valHigh">0</span> / 角度: <span id="degHigh" class="angle-value">0°</span>
  ./AR_rotate_tgg.html:127:            <div class="april-tag" id="tagLow" style="transform: rotate(0deg);">
  ./AR_rotate_tgg.html:130:            <div class="label">値: <span id="valLow">0</span> / 角度: <span id="degLow" class="angle-value">0°</span></div>
  ./AR_rotate_tgg.html:135:            <div class="april-tag" style="transform: rotate(0deg);">
  ./AR_rotate_tgg.html:154:        // 1単位あたりの角度（360度 / 16分割）
  ./AR_rotate_tgg.html:157:        // 1秒間に何度回転するか（360度 / 秒）
  ./AR_rotate_tgg.html:163:                currentAngle: 0,      // 現在の実際の角度（連続）
  ./AR_rotate_tgg.html:164:                targetAngle: 0,       // 目標角度
  ./AR_rotate_tgg.html:196:            // 角度を計算
  ./AR_rotate_tgg.html:200:            // マーカーの目標角度を設定
  ./AR_rotate_tgg.html:217:        // マーカーの回転アニメーション更新
  ./AR_rotate_tgg.html:235:                // 目標角度に向かって移動中
  ./AR_rotate_tgg.html:245:                // 目標角度に到達したかチェック
  ./AR_rotate_tgg.html:246:                const angleDiff = Math.abs(state.currentAngle - state.targetAngle);
  ./AR_rotate_tgg.html:247:                const normalizedDiff = Math.min(angleDiff, 360 - angleDiff);
  ./AR_rotate_tgg.html:250:                    // 目標角度に到達した
  ./AR_rotate_tgg.html:256:                // 待機中：現在の方向で回転し続ける
  ./AR_rotate_tgg.html:268:            element.style.transform = `rotate(${state.currentAngle}deg)`;
  ./AR_rotate.html:57:            /* ここで回転アニメーションを制御 */
  ./AR_rotate.html:62:        /* 回転の基準となる上方向の矢印 */
  ./AR_rotate.html:87:        .angle-value {
  ./AR_rotate.html:94:    <h1>ARマーカー角度通信 シミュレータ</h1>
  ./AR_rotate.html:95:    <p>0〜255の数値を入力すると、上位4bitと下位4bitに対応する角度に回転します。</p>
  ./AR_rotate.html:107:            <div class="april-tag" id="tagHigh" style="transform: rotate(0deg);">
  ./AR_rotate.html:110:            <div class="label">値: <span id="valHigh">0</span> / 角度: <span id="degHigh" class="angle-value">0°</span></div>
  ./AR_rotate.html:115:            <div class="april-tag" id="tagLow" style="transform: rotate(0deg);">
  ./AR_rotate.html:118:            <div class="label">値: <span id="valLow">0</span> / 角度: <span id="degLow" class="angle-value">0°</span></div>
  ./AR_rotate.html:123:            <div class="april-tag" style="transform: rotate(0deg);">
  ./AR_rotate.html:142:        // 1単位あたりの角度（360度 / 16分割）
  ./AR_rotate.html:163:            // 角度を計算
  ./AR_rotate.html:169:            // CSSのtransformを書き換えて回転させる
  ./AR_rotate.html:170:            tagHigh.style.transform = `rotate(${highAngle}deg)`;
  ./AR_rotate.html:171:            tagLow.style.transform = `rotate(${lowAngle}deg)`;
  
- status: Command exited with code 0
- command: /bin/bash -lc "sed -n '140,280p' AR_rotate_tgg.html"
- stdout:     </div>
  
      <script>
          const inputField = document.getElementById('dataInput');
          const bitInfo = document.getElementById('bitInfo');
  
          const tagHigh = document.getElementById('tagHigh');
          const valHighDisplay = document.getElementById('valHigh');
          const degHighDisplay = document.getElementById('degHigh');
  
          const tagLow = document.getElementById('tagLow');
          const valLowDisplay = document.getElementById('valLow');
          const degLowDisplay = document.getElementById('degLow');
  
          // 1単位あたりの角度（360度 / 16分割）
          const ANGLE_STEP = 22.5;
  
          // 1秒間に何度回転するか（360度 / 秒）
          const ROTATION_SPEED = 200; // 度/秒
  
          // 各マーカーの状態管理
          const markerState = {
              high: {
                  currentAngle: 0,      // 現在の実際の角度（連続）
                  targetAngle: 0,       // 目標角度
                  direction: 1,         // 1 = CW (時計回り), -1 = CCW (反時計回り)
                  isMoving: false,      // 目標に向かって移動中か
                  lastTime: Date.now()
              },
              low: {
                  currentAngle: 0,
                  targetAngle: 0,
                  direction: 1,
                  isMoving: false,
                  lastTime: Date.now()
              }
          };
  
          function updateMarkers() {
              let value = parseInt(inputField.value);
  
              // 入力値のバリデーション（0-255の範囲に収める）
              if (isNaN(value)) value = 0;
              value = Math.max(0, Math.min(255, value));
              inputField.value = value; // UI上の数値を修正
  
              // 2進数表示の更新
              bitInfo.textContent = "Binary: " + value.toString(2).padStart(8, '0');
  
              // --- 計算の核心部分 ---
  
              // 上位4ビットを取り出す (右に4回シフト)
              const highNibble = (value >> 4) & 0x0F;
              // 下位4ビットを取り出す (マスクをかける)
              const lowNibble = value & 0x0F;
  
              // 角度を計算
              const highAngle = highNibble * ANGLE_STEP;
              const lowAngle = lowNibble * ANGLE_STEP;
  
              // マーカーの目標角度を設定
              markerState.high.targetAngle = highAngle;
              markerState.high.isMoving = true;
              markerState.high.lastTime = Date.now();
  
              markerState.low.targetAngle = lowAngle;
              markerState.low.isMoving = true;
              markerState.low.lastTime = Date.now();
  
              // 数値表示の更新
              valHighDisplay.textContent = highNibble;
              degHighDisplay.textContent = highAngle.toFixed(1) + "°";
  
              valLowDisplay.textContent = lowNibble;
              degLowDisplay.textContent = lowAngle.toFixed(1) + "°";
          }
  
          // マーカーの回転アニメーション更新
          function animateMarkers() {
              const now = Date.now();
  
              // 高ニブルマーカーの更新
              updateMarkerAnimation(markerState.high, tagHigh, now);
  
              // 低ニブルマーカーの更新
              updateMarkerAnimation(markerState.low, tagLow, now);
  
              requestAnimationFrame(animateMarkers);
          }
  
          function updateMarkerAnimation(state, element, now) {
              const deltaTime = (now - state.lastTime) / 1000; // ミリ秒を秒に変換
              state.lastTime = now;
  
              if (state.isMoving) {
                  // 目標角度に向かって移動中
                  const deltaRotation = ROTATION_SPEED * deltaTime * state.direction;
                  state.currentAngle += deltaRotation;
  
                  // 正規化（0-360の範囲に）
                  state.currentAngle = state.currentAngle % 360;
                  if (state.currentAngle < 0) {
                      state.currentAngle += 360;
                  }
  
                  // 目標角度に到達したかチェック
                  const angleDiff = Math.abs(state.currentAngle - state.targetAngle);
                  const normalizedDiff = Math.min(angleDiff, 360 - angleDiff);
  
                  if (normalizedDiff < 5) {
                      // 目標角度に到達した
                      state.currentAngle = state.targetAngle;
                      state.isMoving = false;
                      state.direction *= -1; // 方向を反転
                  }
              } else {
                  // 待機中：現在の方向で回転し続ける
                  const deltaRotation = ROTATION_SPEED * deltaTime * state.direction;
                  state.currentAngle += deltaRotation;
  
                  // 正規化（0-360の範囲に）
                  state.currentAngle = state.currentAngle % 360;
                  if (state.currentAngle < 0) {
                      state.currentAngle += 360;
                  }
              }
  
              // CSSのtransformを更新
              element.style.transform = `rotate(${state.currentAngle}deg)`;
          }
  
          // 入力が変更されたら実行
          inputField.addEventListener('input', updateMarkers);
  
          // ランダムボタンの処理
          const randomBtn = document.getElementById('randomBtn');
          randomBtn.addEventListener('click', function () {
              const randomValue = Math.floor(Math.random() * 256);
              inputField.value = randomValue;
              updateMarkers();
          });
  
- status: Command exited with code 0
- command: /bin/bash -lc "sed -n '150,260p' aruco_rotate.html"
- stdout:         const rotationDirection = document.getElementById('rotationDirection');
          const queueValue = document.getElementById('queueValue');
          const sendBtn = document.getElementById('sendBtn');
          const idleBtn = document.getElementById('idleBtn');
  
          const ANGLE_STEP = 45;
          const MOTOR_DEGREES_PER_SECOND = 360;
          const STOP_HOLD_MS = 400;
          const TOGGLE_CLOCKWISE = 0;
          const TOGGLE_COUNTER_CLOCKWISE = 1;
  
          const STATE_IDLE = 'IDLE';
          const STATE_ROTATING = 'ROTATING';
          const STATE_HOLDING = 'HOLDING';
  
          let state = STATE_IDLE;
          let currentCommand = null;
          let currentToggle = TOGGLE_CLOCKWISE;
          let currentAngle = 0;
          let motionStartAngle = 0;
          let motionTargetAngle = 0;
          let motionStartAt = 0;
          let motionDurationMs = 0;
          let holdStartAt = 0;
          let animationId = null;
          let lastFrameAt = null;
          let queuedCommand = null;
  
          function normalizeCommand(value) {
              let command = parseInt(value, 10);
  
              if (isNaN(command)) command = 0;
              return Math.max(0, Math.min(7, command));
          }
  
          function commandToStepCount(command) {
              return command === 0 ? 8 : command;
          }
  
          function commandToDeltaAngle(command) {
              return commandToStepCount(command) * ANGLE_STEP;
          }
  
          function getDeltaText() {
              if (currentCommand === null) return '-';
              return commandToDeltaAngle(currentCommand) + '°';
          }
  
          function getDirectionSign() {
              return currentToggle === TOGGLE_CLOCKWISE ? 1 : -1;
          }
  
          function flipToggle() {
              currentToggle =
                  currentToggle === TOGGLE_CLOCKWISE
                      ? TOGGLE_COUNTER_CLOCKWISE
                      : TOGGLE_CLOCKWISE;
          }
  
          function smoothStep(progress) {
              return progress * progress * (3 - 2 * progress);
          }
  
          function updateStatus() {
              const deltaText = getDeltaText();
              const directionText = currentToggle === TOGGLE_CLOCKWISE ? '時計回り' : '反時計回り';
              const queuedText = queuedCommand === null ? 'none' : queuedCommand;
              const activeText = currentCommand === null ? 'IDLE' : currentCommand;
              const toggleText = currentCommand === null ? '-' : currentToggle;
  
              commandValue.textContent = activeText;
              deltaValue.textContent = deltaText;
              toggleValue.textContent = toggleText;
              rotationDirection.textContent = directionText;
              queueValue.textContent = queuedCommand === null ? 'なし' : queuedCommand;
              commandInfo.textContent = `State: ${state} / Active: ${activeText} / Delta: ${deltaText} / Toggle: ${toggleText} / Queue: ${queuedText}`;
          }
  
          function renderMarker() {
              rotatingMarker.style.transform = `rotate(${currentAngle}deg)`;
          }
  
          function startAnimation() {
              if (animationId !== null) return;
              lastFrameAt = null;
              animationId = requestAnimationFrame(animationLoop);
          }
  
          function startCommandMotion(command, timestamp) {
              const deltaAngle = commandToDeltaAngle(command);
              const signedDeltaAngle = deltaAngle * getDirectionSign();
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle + signedDeltaAngle;
              motionStartAt = timestamp;
              motionDurationMs = (deltaAngle / MOTOR_DEGREES_PER_SECOND) * 1000;
              state = STATE_ROTATING;
  
              updateStatus();
              startAnimation();
          }
  
          function applyCommand(command, timestamp) {
              currentCommand = command;
              flipToggle();
              startCommandMotion(command, timestamp);
          }
  
          function updateRotating(timestamp) {
              const progress = Math.min((timestamp - motionStartAt) / motionDurationMs, 1);
              const easedProgress = smoothStep(progress);
  
- status: Command exited with code 0
- command: /bin/bash -lc "sed -n '150,260p' aruco_rotate_puls.html"
- stdout:         const sendBtn = document.getElementById('sendBtn');
          const idleBtn = document.getElementById('idleBtn');
  
          const ANGLE_STEP = 45;
          const MOTOR_DEGREES_PER_SECOND = 180;
          const PULSE_HOLD_MS = 150;
          const COMMAND_END_HOLD_MS = 500;
          const TOGGLE_CLOCKWISE = 0;
          const TOGGLE_COUNTER_CLOCKWISE = 1;
  
          const STATE_IDLE = 'IDLE';
          const STATE_ROTATING_PULSE = 'ROTATING_PULSE';
          const STATE_PULSE_HOLD = 'PULSE_HOLD';
          const STATE_COMMAND_END_HOLD = 'COMMAND_END_HOLD';
  
          let state = STATE_IDLE;
          let currentCommand = null;
          let currentToggle = TOGGLE_CLOCKWISE;
          let totalPulseCount = 0;
          let completedPulseCount = 0;
          let currentAngle = 0;
          let motionStartAngle = 0;
          let motionTargetAngle = 0;
          let motionStartAt = 0;
          let motionDurationMs = 0;
          let holdStartAt = 0;
          let animationId = null;
          let lastFrameAt = null;
          let queuedCommand = null;
  
          function normalizeCommand(value) {
              let command = parseInt(value, 10);
  
              if (isNaN(command)) command = 0;
              return Math.max(0, Math.min(7, command));
          }
  
          function commandToStepCount(command) {
              return command === 0 ? 8 : command;
          }
  
          function getPulseText() {
              if (currentCommand === null) return '-';
              return `${completedPulseCount}/${totalPulseCount}`;
          }
  
          function getDirectionSign() {
              return currentToggle === TOGGLE_CLOCKWISE ? 1 : -1;
          }
  
          function flipToggle() {
              currentToggle =
                  currentToggle === TOGGLE_CLOCKWISE
                      ? TOGGLE_COUNTER_CLOCKWISE
                      : TOGGLE_CLOCKWISE;
          }
  
          function smoothStep(progress) {
              return progress * progress * (3 - 2 * progress);
          }
  
          function updateStatus() {
              const pulseText = getPulseText();
              const directionText = currentToggle === TOGGLE_CLOCKWISE ? '時計回り' : '反時計回り';
              const queuedText = queuedCommand === null ? 'none' : queuedCommand;
              const activeText = currentCommand === null ? 'IDLE' : currentCommand;
              const toggleText = currentCommand === null ? '-' : currentToggle;
  
              commandValue.textContent = activeText;
              deltaValue.textContent = pulseText;
              toggleValue.textContent = toggleText;
              rotationDirection.textContent = directionText;
              queueValue.textContent = queuedCommand === null ? 'なし' : queuedCommand;
              commandInfo.textContent = `State: ${state} / Active: ${activeText} / Pulse: ${pulseText} / Toggle: ${toggleText} / Queue: ${queuedText}`;
          }
  
          function renderMarker() {
              rotatingMarker.style.transform = `rotate(${currentAngle}deg)`;
          }
  
          function startAnimation() {
              if (animationId !== null) return;
              lastFrameAt = null;
              animationId = requestAnimationFrame(animationLoop);
          }
  
          function startPulseMotion(timestamp) {
              const signedDeltaAngle = ANGLE_STEP * getDirectionSign();
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle + signedDeltaAngle;
              motionStartAt = timestamp;
              motionDurationMs = (ANGLE_STEP / MOTOR_DEGREES_PER_SECOND) * 1000;
              state = STATE_ROTATING_PULSE;
  
              updateStatus();
              startAnimation();
          }
  
          function applyCommand(command, timestamp) {
              currentCommand = command;
              totalPulseCount = commandToStepCount(command);
              completedPulseCount = 0;
              flipToggle();
              startPulseMotion(timestamp);
          }
  
          function updateRotating(timestamp) {
              const progress = Math.min((timestamp - motionStartAt) / motionDurationMs, 1);
              const easedProgress = smoothStep(progress);
  
  
- status: Command exited with code 0
- command: /bin/bash -lc "sed -n '260,380p' aruco_rotate.html"
- stdout:             const easedProgress = smoothStep(progress);
  
              currentAngle =
                  motionStartAngle +
                  (motionTargetAngle - motionStartAngle) * easedProgress;
  
              if (progress >= 1) {
                  currentAngle = motionTargetAngle;
                  state = STATE_HOLDING;
                  holdStartAt = timestamp;
                  updateStatus();
              }
          }
  
          function updateHolding(timestamp) {
              if (timestamp - holdStartAt < STOP_HOLD_MS) {
                  return;
              }
  
              if (queuedCommand !== null) {
                  const nextCommand = queuedCommand;
                  queuedCommand = null;
                  applyCommand(nextCommand, timestamp);
                  return;
              }
  
              if (currentCommand !== null) {
                  startCommandMotion(currentCommand, timestamp);
              }
          }
  
          function animationLoop(timestamp) {
              if (lastFrameAt === null) {
                  lastFrameAt = timestamp;
              }
  
              lastFrameAt = timestamp;
  
              if (state === STATE_ROTATING) {
                  updateRotating(timestamp);
              } else if (state === STATE_HOLDING) {
                  updateHolding(timestamp);
              }
  
              renderMarker();
  
              if (state !== STATE_IDLE || queuedCommand !== null) {
                  animationId = requestAnimationFrame(animationLoop);
              } else {
                  animationId = null;
                  lastFrameAt = null;
              }
          }
  
          function sendCommand() {
              const command = normalizeCommand(commandInput.value);
  
              if (state === STATE_IDLE) {
                  applyCommand(command, performance.now());
                  return;
              }
  
              queuedCommand = command;
              updateStatus();
          }
  
          function resetToIdle() {
              queuedCommand = null;
              currentCommand = null;
              state = STATE_IDLE;
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle;
              motionDurationMs = 0;
              holdStartAt = 0;
  
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
                  animationId = null;
              }
  
              lastFrameAt = null;
              updateStatus();
              renderMarker();
          }
  
          sendBtn.addEventListener('click', sendCommand);
          idleBtn.addEventListener('click', resetToIdle);
  
          window.addEventListener('beforeunload', function() {
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
              }
          });
  
          resetToIdle();
      </script>
  </body>
  </html>
  
- status: Command exited with code 0
- command: /bin/bash -lc "sed -n '260,400p' aruco_rotate_puls.html"
- stdout: 
              currentAngle =
                  motionStartAngle +
                  (motionTargetAngle - motionStartAngle) * easedProgress;
  
              if (progress >= 1) {
                  currentAngle = motionTargetAngle;
                  completedPulseCount += 1;
                  state =
                      completedPulseCount >= totalPulseCount
                          ? STATE_COMMAND_END_HOLD
                          : STATE_PULSE_HOLD;
                  holdStartAt = timestamp;
                  updateStatus();
              }
          }
  
          function updatePulseHold(timestamp) {
              if (timestamp - holdStartAt < PULSE_HOLD_MS) {
                  return;
              }
  
              startPulseMotion(timestamp);
          }
  
          function updateCommandEndHold(timestamp) {
              if (timestamp - holdStartAt < COMMAND_END_HOLD_MS) {
                  return;
              }
  
              if (queuedCommand !== null) {
                  const nextCommand = queuedCommand;
                  queuedCommand = null;
                  applyCommand(nextCommand, timestamp);
                  return;
              }
  
              if (currentCommand !== null) {
                  completedPulseCount = 0;
                  startPulseMotion(timestamp);
              }
          }
  
          function animationLoop(timestamp) {
              if (lastFrameAt === null) {
                  lastFrameAt = timestamp;
              }
  
              lastFrameAt = timestamp;
  
              if (state === STATE_ROTATING_PULSE) {
                  updateRotating(timestamp);
              } else if (state === STATE_PULSE_HOLD) {
                  updatePulseHold(timestamp);
              } else if (state === STATE_COMMAND_END_HOLD) {
                  updateCommandEndHold(timestamp);
              }
  
              renderMarker();
  
              if (state !== STATE_IDLE || queuedCommand !== null) {
                  animationId = requestAnimationFrame(animationLoop);
              } else {
                  animationId = null;
                  lastFrameAt = null;
              }
          }
  
          function sendCommand() {
              const command = normalizeCommand(commandInput.value);
  
              if (state === STATE_IDLE) {
                  applyCommand(command, performance.now());
                  return;
              }
  
              queuedCommand = command;
              updateStatus();
          }
  
          function resetToIdle() {
              queuedCommand = null;
              currentCommand = null;
              state = STATE_IDLE;
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle;
              motionDurationMs = 0;
              holdStartAt = 0;
              totalPulseCount = 0;
              completedPulseCount = 0;
  
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
                  animationId = null;
              }
  
              lastFrameAt = null;
              updateStatus();
              renderMarker();
          }
  
          sendBtn.addEventListener('click', sendCommand);
          idleBtn.addEventListener('click', resetToIdle);
  
          window.addEventListener('beforeunload', function() {
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
              }
          });
  
          resetToIdle();
      </script>
  </body>
  </html>
  
- status: Command exited with code 0
- status: tokens used: {"input_tokens":65821,"cached_input_tokens":54784,"output_tokens":1496,"reasoning_output_tokens":38}
- status: Codex exited with code 0
- status: History exported: /home/sato/obsidian/Codex-history/web-...-6_c4DLPP.md

</details>

### user

aruco_rotate.html の方式の仕様を出してほしい

### assistant

[aruco_rotate.html](/home/sato/robocon/AR_rotate/aruco_rotate.html) の方式をモーター実機仕様にすると、**コマンド値を相対回転角に変換して、同じ角度を周期的に回し続ける方式**です。

**方式概要**

- 固定マーカー: `ID:0`
- 回転マーカー: `ID:1`
- 入力コマンド: `0〜7`
- 回転単位: `45度`
- モーター制御: 速度制御
- 到達後停止: `0.4〜0.5秒`
- コマンド実行中は、同じ相対角度の回転を繰り返す
- 新しいコマンドが来た場合は、現在の回転と停止が終わった後に次コマンドへ切り替える

**コマンドと回転角**

```text
command = 0 → 360度回転
command = 1 → 45度回転
command = 2 → 90度回転
command = 3 → 135度回転
command = 4 → 180度回転
command = 5 → 225度回転
command = 6 → 270度回転
command = 7 → 315度回転
```

`0` は停止ではなく、`8ステップ = 360度` として扱う仕様です。

**動作シーケンス**

```text
IDLE
  ↓ コマンド入力
ROTATING
  ↓ 指定角度ぶん回転
HOLDING
  ↓ 0.4〜0.5秒停止
ROTATING
  ↓ 同じコマンド角度を再実行
HOLDING
  ↓
繰り返し
```

**モーター制御仕様**

- 回転開始時に現在角度を記録する
- コマンド値から相対回転角を計算する
- 目標角度を設定する

```text
目標角度 = 現在角度 + コマンド角度 × 回転方向
```

- モーターを一定角速度で回す
- 目標角度に到達したら停止する
- `0.5秒` 停止後、同じコマンドを再度実行する

**推奨パラメータ**

```text
角度ステップ: 45度
回転速度: 360 deg/s
停止時間: 0.5秒
角度到達しきい値: ±3〜5度
```

**方向トグル**

`aruco_rotate.html` では、コマンド適用時に回転方向を反転する設計です。

```text
1回目: 時計回り
2回目: 反時計回り
3回目: 時計回り
...
```

実機仕様としては、コマンド更新時に方向を反転させるか、常に同一方向にするかを選べます。今の HTML に合わせるなら **コマンドを受け取るたびに回転方向を反転**です。

**擬似コード**

```cpp
command = receiveCommand();  // 0〜7

stepCount = (command == 0) ? 8 : command;
deltaAngle = stepCount * 45.0;

targetAngle = currentAngle + direction * deltaAngle;

while (abs(targetAngle - currentAngle) > angleThreshold) {
    motor.setSpeed(direction * speed);
    currentAngle = encoder.getAngle();
}

motor.setSpeed(0);
delay(500);

repeat same command;
```

まとめると、`aruco_rotate.html` 方式は **「コマンド値 = 1回あたりの相対回転角」として扱い、指定角度だけ速度制御で回して、到達したら0.5秒止め、同じ動作を繰り返す」** 仕様です。

<details>
<summary>Codex run log</summary>

- status: Codex CLI: codex --ask-for-approval never -C /home/sato/robocon/AR_rotate exec --sandbox workspace-write resume --skip-git-repo-check --json 019f3d06-2821-7050-9984-8086b7331ad3 "<prompt omitted, 31 chars>"
- status: Codex thread: 019f3d06-2821-7050-9984-8086b7331ad3
- status: Codex turn started
- status: tokens used: {"input_tokens":86457,"cached_input_tokens":59776,"output_tokens":2428,"reasoning_output_tokens":66}
- status: Codex exited with code 0
- status: History exported: /home/sato/obsidian/Codex-history/web-...-6_c4DLPP.md

</details>

### user

aruco_rotate.html は今、0-7までしかできないけど360度以上回るようにすれば時間はかかるけど、無限にコマンド送れるよね

### assistant

そうです。回転量を360°以上に拡張すれば、**0〜7の8種類を時系列で送り続けられる**ので、理論上はコマンド列の長さに上限はありません。

ただし重要なのは、ArUcoマーカーの見た目は360°ごとに同じ向きへ戻ることです。受信側が停止後の角度だけを見る場合、例えば360°・720°・1080°を区別できません。したがって「何回転したか」ではなく、次のような時間プロトコルとして扱う必要があります。

- 回転開始を検出
- 回転中も連続追跡
- 45°ごとの通過回数、または累積回転角を数える
- 停止をコマンド確定として扱う
- 0.5秒停止中に値を読み取る
- 次の回転を次コマンドとして扱う

例えば回転量を次のように拡張できます。

| コマンド値 | 回転量 |
|---:|---:|
| 0 | 360° |
| 1 | 45° |
| 7 | 315° |
| 8 | 360° |
| 9 | 405° |
| 16 | 720° |
| N | `N × 45°` |

ただし現在の `0 → 360°` という特殊処理を残すと、`0`と`8`が同じ回転量になります。実機向けには、次のどちらかが分かりやすいです。

1. `回転量 = (コマンド + 1) × 45°`
2. `回転量 = コマンド × 45°`として、0は回転なし

実機仕様としては、

```text
受信 → 指定方向へ速度制御
     → 累積角度が目標値に到達
     → モーター停止
     → 0.5秒保持
     → 次のコマンドを実行
```

という形になります。

結論として、**送信できるコマンド列は実質無限にできる**一方、360°以上の回転数をカメラ側で判別するには、停止時のマーカー角度だけではなく、回転中の累積角度を途切れず追跡する必要があります。追跡を簡単かつ堅牢にするなら、1コマンドを315°以内にして、0.5秒の停止を区切りとして連続送信する方式の方が適しています。

<details>
<summary>Codex run log</summary>

- status: Codex CLI: codex --ask-for-approval never -C /home/sato/robocon/AR_rotate exec --sandbox danger-full-access resume --skip-git-repo-check --json 019f3d06-2821-7050-9984-8086b7331ad3 "<prompt omitted, 69 chars>"
- status: Codex thread: 019f3d06-2821-7050-9984-8086b7331ad3
- status: codex event: error
- status: Codex turn started
- status: tokens used: {"input_tokens":104864,"cached_input_tokens":69760,"output_tokens":3232,"reasoning_output_tokens":259}
- status: Codex exited with code 0
- status: History exported: /home/sato/obsidian/Codex-history/web-...-6_c4DLPP.md

</details>

### user

以下のHTMLファイルを、指定する新仕様に合わせて修正してください。

対象ファイルは、ArUcoマーカーを回転させて整数コマンドを表現するシミュレータです。

## 現在の構成

このHTMLには以下の機能があります。

* ID 1のArUcoマーカーを回転表示する
* ID 0のArUcoマーカーを固定表示する
* コマンド入力欄
* コマンド送信ボタン
* IDLEリセットボタン
* `IDLE`
* `ROTATING`
* `HOLDING`

の3状態による状態管理

現在の入力欄は`0〜7`に制限されています。

```html
<label for="commandInput">送信コマンド (0-7): </label>
<input type="number" id="commandInput" min="0" max="7" value="1">
```

また、現在はコマンド0を特別扱いし、8ステップ、つまり360°回転として扱っています。

```javascript
function commandToStepCount(command) {
    return command === 0 ? 8 : command;
}
```

この仕様を廃止し、以下の新仕様へ変更してください。

---

# 新仕様

## 1. コマンドの意味

コマンドは0以上の整数とします。

| コマンド | 動作            |
| ---: | ------------- |
|  `0` | 即時停止してIDLEへ移行 |
|  `1` | 45°回転         |
|  `2` | 90°回転         |
|  `7` | 315°回転        |
|  `8` | 360°回転        |
|  `9` | 405°回転        |
| `16` | 720°回転        |
|  `n` | `n × 45°`回転   |

回転角度は次の式で計算してください。

```javascript
deltaAngle = command * ANGLE_STEP;
```

`ANGLE_STEP`は現在と同じ45°を使用してください。

コマンド0を360°として扱う処理は完全に削除してください。

---

## 2. 入力欄

入力欄の`max="7"`を削除し、0以上の整数を入力できるようにしてください。

例：

```html
<label for="commandInput">
    送信コマンド（0: 停止、1以上: 45°刻み）
</label>

<input
    type="number"
    id="commandInput"
    min="0"
    step="1"
    value="1"
>
```

入力値を0〜7の範囲に丸める処理は行わないでください。

---

## 3. 入力値検証

以下の入力は無効としてください。

* 空文字
* 数値でない値
* 負の数
* 小数
* `Number.isSafeInteger()`を満たさない巨大な整数

無効な値の場合はコマンドを実行せず、画面上に次のようなエラーを表示してください。

```text
0以上の整数を入力してください
```

現在の`normalizeCommand()`のように、不正値を自動的に0へ変換したり、0〜7へクランプしたりしないでください。

検証関数は、例えば次のような責務にしてください。

```javascript
function parseCommand(value) {
    // 有効なら整数を返す
    // 無効ならnullを返す
}
```

---

## 4. コマンド0の動作

コマンド0を送信した場合、現在の状態にかかわらず即座に停止してください。

対象状態：

* `IDLE`
* `ROTATING`
* `HOLDING`

停止時には以下を実行してください。

1. 回転アニメーションを停止
2. 現在の表示角度を維持
3. `currentCommand`を`null`へ変更
4. `queuedCommand`を`null`へ変更
5. 状態を`STATE_IDLE`へ変更
6. 保持中のモーション情報をリセット
7. 画面表示を更新

停止時にマーカーを0°へ戻してはいけません。

現在角度のまま停止してください。

コマンド0では回転方向のトグルを変更しないでください。

既存の`resetToIdle()`を再利用または改良し、コマンド0でも同じ停止処理が使える設計にしてください。

---

## 5. 停止ボタン

現在の`IDLEリセット`ボタンは、ユーザーに分かりやすいように次の表示へ変更してください。

```text
停止
```

停止ボタンを押した場合は、コマンド0を送信した場合と同じ処理を実行してください。

停止ボタン専用の異なる挙動は作らず、停止処理を共通化してください。

例：

```javascript
function stopCommand() {
    // command 0と停止ボタンで共通利用
}
```

---

## 6. 非ゼロコマンドの実行

### IDLE中

`command >= 1`を送信した場合は、直ちにそのコマンドの回転を開始してください。

回転角度：

```javascript
command * 45
```

回転時間：

```javascript
motionDurationMs =
    (deltaAngle / MOTOR_DEGREES_PER_SECOND) * 1000;
```

現在の回転速度である毎秒360°は維持してください。

---

## 7. 実行中の新規コマンド

`ROTATING`または`HOLDING`中に、1以上の新しいコマンドが送信された場合は、現在と同じく予約コマンドとして保存してください。

予約できるコマンドは1件のみとします。

新しいコマンドが追加で送信された場合は、古い予約を新しい値で上書きしてください。

例：

```text
command 4を実行中
command 8を予約
さらにcommand 12を送信
→ 予約コマンドは12
```

コマンド0が送信された場合は予約ではなく、即座に停止してください。

---

## 8. コマンドの繰り返し

非ゼロコマンドは、現在の仕様と同じく繰り返し送信してください。

動作：

1. 指定角度を回転
2. 400ms停止
3. 予約コマンドがあれば予約コマンドを開始
4. 予約コマンドがなければ同じコマンドを再実行

例：

```text
command 9
→ 405°回転
→ 400ms停止
→ 405°回転
→ 400ms停止
→ 繰り返し
```

コマンド0または停止ボタンが押された場合は繰り返しを終了してください。

---

## 9. 回転方向

現在の回転方向トグルの仕組みを維持してください。

新しい非ゼロコマンドが開始されたときに回転方向を反転します。

ただし、同じコマンドを自動的に繰り返す場合は、回転方向を変更しないでください。

例：

```text
command 9を新規開始
→ 時計回り

command 9の自動再実行
→ 時計回りのまま

command 3を新規開始
→ 反時計回り
```

コマンド0または停止ボタンでは、トグルを反転しないでください。

現在のコードでは`applyCommand()`内で毎回`flipToggle()`を実行しているため、以下の2種類を区別できる構造へ整理してください。

* ユーザーが送信した新規コマンド
* 同じコマンドの自動再実行

例えば、次のように責務を分けても構いません。

```javascript
function applyNewCommand(command, timestamp) {
    currentCommand = command;
    flipToggle();
    startCommandMotion(command, timestamp);
}

function repeatCurrentCommand(timestamp) {
    startCommandMotion(currentCommand, timestamp);
}
```

関数名は適切な名前へ変更して構いません。

---

## 10. 表示内容

画面上の表示を新仕様に合わせて変更してください。

入力欄の説明：

```text
送信コマンド（0: 停止、1以上: 45°刻み）
```

実行中の非ゼロコマンドでは、次の情報を表示してください。

* 状態
* 実行中コマンド
* 相対回転角度
* トグル値
* 回転方向
* 予約コマンド

例：

```text
State: ROTATING / Active: 9 / Delta: 405° / Toggle: 1 / Queue: none
```

IDLE時は次のように表示してください。

```text
State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none
```

エラーメッセージを表示した後、正常なコマンドが送信されたらエラー表示を消してください。

---

## 11. 状態管理

次の状態は維持してください。

```javascript
const STATE_IDLE = 'IDLE';
const STATE_ROTATING = 'ROTATING';
const STATE_HOLDING = 'HOLDING';
```

状態遷移は次のようにしてください。

```text
IDLE
  └─ command >= 1 → ROTATING

ROTATING
  ├─ 回転完了 → HOLDING
  ├─ command >= 1 → 予約を更新
  └─ command 0 → IDLE

HOLDING
  ├─ 400ms経過・予約あり → 予約コマンドを開始
  ├─ 400ms経過・予約なし → 同じコマンドを再実行
  ├─ command >= 1 → 予約を更新
  └─ command 0 → IDLE
```

---

## 12. 変更時の注意事項

以下は維持してください。

* HTML、CSS、JavaScriptを1つのHTMLファイル内にまとめる
* 外部ライブラリは追加しない
* `requestAnimationFrame()`によるアニメーション
* `smoothStep()`による補間
* ID 0の固定ArUcoマーカー
* ID 1の回転ArUcoマーカー
* 現在角度を累積して保持する仕組み
* 回転速度360°/秒
* 停止保持時間400ms
* 予約コマンドは1件のみ
* 既存の画像ファイル名

画像ファイル名：

```text
aruco36_12_0000.png
aruco36_12_0001.png
```

不要なフレームワークや過剰なクラス設計は導入しないでください。

既存コードをできるだけ活用しながら、読みやすい関数構成へ整理してください。

---

## 13. 必須テストケース

修正後、以下の動作を確認してください。

### テスト1：command 0

1. command 5を実行
2. 回転中にcommand 0を送信
3. 即座に現在角度で停止
4. 状態がIDLEになる
5. 予約コマンドが削除される

### テスト2：command 8

1. command 8を送信
2. 360°回転する
3. 400ms停止する
4. 同じ方向へ360°回転を繰り返す

### テスト3：command 9

1. command 9を送信
2. 405°回転する
3. 表示上の相対回転角が405°になる

### テスト4：大きなコマンド

1. command 16を送信
2. 720°回転する
3. 2秒程度で回転が完了する

### テスト5：予約コマンド

1. command 4を実行
2. 回転中にcommand 10を送信
3. command 4完了後に400ms停止
4. 反対方向へcommand 10を開始

### テスト6：予約の上書き

1. command 4を実行
2. command 8を予約
3. command 12を送信
4. 予約表示が12になる
5. command 8は実行されない

### テスト7：停止による予約削除

1. command 4を実行
2. command 12を予約
3. command 0を送信
4. 即座に停止
5. command 12は実行されない

### テスト8：不正入力

以下を入力しても動作を開始しないこと。

```text
-1
1.5
空文字
abc
```

画面上に次を表示してください。

```text
0以上の整数を入力してください
```

---

## 14. 出力形式

修正後の完成したHTML全文を、1つのコードブロックで出力してください。

説明だけではなく、そのまま保存してブラウザで実行できる完全なHTMLを出してください。

コードブロックの後に、変更点を簡潔に箇条書きで説明してください。

元の機能を壊していないことを確認し、未実装部分や疑似コードを残さないでください。

### assistant

指定された状態遷移と入力検証に合わせて、既存HTMLの構造とマーカー表示を保ったまま修正します。まず現行コード全体を確認し、その後に停止処理・新規実行・自動再実行を分離してテストします。現行実装では、コマンド適用のたびに方向反転していたため、自動再実行でも方向が変わり得る構造でした。ここを「新規コマンド開始」と「同一コマンド再実行」に分け、コマンド0と停止ボタンは同じ即時停止関数へ集約します。修正を反映しました。次に、旧仕様の0〜7クランプやコマンド0の360°特例が残っていないことを確認し、JavaScriptの構文と指定された主要な状態遷移を自動検証します。主要テストは通過しました。`8 → 360°/1秒`、`16 → 720°/2秒`、400ms後の同方向反復、予約上書き、予約開始時の方向反転、回転途中の角度を保った即時停止、不正入力の拒否を確認できています。最後に実ブラウザで初期表示と画像参照を確認します。実ブラウザでも初期状態が正しく生成され、両方の既存マーカー画像も参照できています。初期HTML自体もIDLE表示と一致するよう、向きの初期表示だけ `-` に揃えて仕上げます。```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aruco36_12 コマンド送信シミュレータ</title>
    <style>
        body {
            font-family: sans-serif;
            text-align: center;
            background-color: white;
            padding: 20px;
        }

        h1 {
            color: #333;
        }

        .controls {
            margin: 30px auto;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 500px;
        }

        input[type="number"] {
            font-size: 24px;
            padding: 10px;
            width: 120px;
            text-align: center;
            border: 2px solid #ddd;
            border-radius: 5px;
        }

        button {
            margin-top: 15px;
            padding: 10px 20px;
            font-size: 16px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }

        button:hover {
            background-color: #0056b3;
        }

        .command-info {
            margin-top: 15px;
            font-family: monospace;
            color: #555;
        }

        .error-message {
            min-height: 1.5em;
            margin-top: 10px;
            color: #c62828;
            font-weight: bold;
        }

        .marker-container {
            display: flex;
            justify-content: center;
            gap: 120px;
            margin-top: 80px;
            flex-wrap: wrap;
            perspective: 1000px;
        }

        .marker-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }

        .aruco-marker {
            width: 220px;
            height: 220px;
            background-color: white;
            border: none;
            position: relative;
            box-shadow: none;
            padding: 10px;
        }

        .marker-image {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
            image-rendering: pixelated;
        }

        .label {
            margin-top: 40px;
            font-weight: bold;
            color: #666;
        }

        .marker-title {
            margin-bottom: 40px;
        }

        .marker-status {
            margin-top: 60px;
        }

        .value {
            color: #007bff;
        }
    </style>
</head>
<body>
    <h1>Aruco36_12 コマンド送信シミュレータ</h1>
    <p>ID:0を固定用Aruco、ID:1を一定角速度で相対角度だけ回転するArucoとして表示します。</p>

    <div class="controls">
        <label for="commandInput">送信コマンド（0: 停止、1以上: 45°刻み）</label><br>
        <input type="number" id="commandInput" min="0" step="1" value="1">
        <div class="error-message" id="errorMessage" role="alert"></div>
        <div class="command-info" id="commandInfo">State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none</div>
        <button id="sendBtn">コレを送れ</button>
        <button id="stopBtn">停止</button>
    </div>

    <div class="marker-container">
        <div class="marker-box">
            <div class="label marker-title">回転用Aruco / ID: 1</div>
            <div class="aruco-marker" id="rotatingMarker" style="transform: rotate(0deg);">
                <img src="aruco36_12_0001.png" class="marker-image" alt="Aruco36_12 ID 1">
            </div>
            <div class="label marker-status">状態: <span id="commandValue">IDLE</span> / 相対回転角: <span id="deltaValue" class="value">-</span></div>
            <div class="label">トグル: <span id="toggleValue" class="value">-</span> / 向き: <span id="rotationDirection" class="value">-</span></div>
            <div class="label">予約: <span id="queueValue" class="value">なし</span></div>
        </div>

        <div class="marker-box">
            <div class="label marker-title">座標固定用Aruco / ID: 0</div>
            <div class="aruco-marker" style="transform: rotate(0deg);">
                <img src="aruco36_12_0000.png" class="marker-image" alt="Aruco36_12 ID 0">
            </div>
            <div class="label marker-status">基準マーカー</div>
        </div>
    </div>

    <script>
        const commandInput = document.getElementById('commandInput');
        const errorMessage = document.getElementById('errorMessage');
        const commandInfo = document.getElementById('commandInfo');
        const rotatingMarker = document.getElementById('rotatingMarker');
        const commandValue = document.getElementById('commandValue');
        const deltaValue = document.getElementById('deltaValue');
        const toggleValue = document.getElementById('toggleValue');
        const rotationDirection = document.getElementById('rotationDirection');
        const queueValue = document.getElementById('queueValue');
        const sendBtn = document.getElementById('sendBtn');
        const stopBtn = document.getElementById('stopBtn');

        const ANGLE_STEP = 45;
        const MOTOR_DEGREES_PER_SECOND = 360;
        const STOP_HOLD_MS = 400;
        const TOGGLE_CLOCKWISE = 0;
        const TOGGLE_COUNTER_CLOCKWISE = 1;

        const STATE_IDLE = 'IDLE';
        const STATE_ROTATING = 'ROTATING';
        const STATE_HOLDING = 'HOLDING';

        let state = STATE_IDLE;
        let currentCommand = null;
        let currentToggle = TOGGLE_COUNTER_CLOCKWISE;
        let currentAngle = 0;
        let motionStartAngle = 0;
        let motionTargetAngle = 0;
        let motionStartAt = 0;
        let motionDurationMs = 0;
        let holdStartAt = 0;
        let animationId = null;
        let lastFrameAt = null;
        let queuedCommand = null;

        function parseCommand(value) {
            if (value.trim() === '') return null;

            const command = Number(value);
            if (!Number.isSafeInteger(command) || command < 0) return null;
            return command;
        }

        function commandToDeltaAngle(command) {
            return command * ANGLE_STEP;
        }

        function getDeltaText() {
            if (currentCommand === null) return '-';
            return commandToDeltaAngle(currentCommand) + '°';
        }

        function getDirectionSign() {
            return currentToggle === TOGGLE_CLOCKWISE ? 1 : -1;
        }

        function flipToggle() {
            currentToggle =
                currentToggle === TOGGLE_CLOCKWISE
                    ? TOGGLE_COUNTER_CLOCKWISE
                    : TOGGLE_CLOCKWISE;
        }

        function smoothStep(progress) {
            return progress * progress * (3 - 2 * progress);
        }

        function updateStatus() {
            const deltaText = getDeltaText();
            const queuedText = queuedCommand === null ? 'none' : queuedCommand;
            const activeText = currentCommand === null ? 'IDLE' : currentCommand;
            const toggleText = currentCommand === null ? '-' : currentToggle;
            const directionText =
                currentCommand === null
                    ? '-'
                    : currentToggle === TOGGLE_CLOCKWISE
                        ? '時計回り'
                        : '反時計回り';

            commandValue.textContent = activeText;
            deltaValue.textContent = deltaText;
            toggleValue.textContent = toggleText;
            rotationDirection.textContent = directionText;
            queueValue.textContent = queuedCommand === null ? 'なし' : queuedCommand;
            commandInfo.textContent = currentCommand === null
                ? 'State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none'
                : `State: ${state} / Active: ${activeText} / Delta: ${deltaText} / Toggle: ${toggleText} / Direction: ${directionText} / Queue: ${queuedText}`;
        }

        function renderMarker() {
            rotatingMarker.style.transform = `rotate(${currentAngle}deg)`;
        }

        function startAnimation() {
            if (animationId !== null) return;
            lastFrameAt = null;
            animationId = requestAnimationFrame(animationLoop);
        }

        function startCommandMotion(command, timestamp) {
            const deltaAngle = commandToDeltaAngle(command);
            const signedDeltaAngle = deltaAngle * getDirectionSign();

            motionStartAngle = currentAngle;
            motionTargetAngle = currentAngle + signedDeltaAngle;
            motionStartAt = timestamp;
            motionDurationMs = (deltaAngle / MOTOR_DEGREES_PER_SECOND) * 1000;
            state = STATE_ROTATING;

            updateStatus();
            startAnimation();
        }

        function applyNewCommand(command, timestamp) {
            currentCommand = command;
            flipToggle();
            startCommandMotion(command, timestamp);
        }

        function repeatCurrentCommand(timestamp) {
            if (currentCommand !== null) {
                startCommandMotion(currentCommand, timestamp);
            }
        }

        function updateRotating(timestamp) {
            const progress = Math.min((timestamp - motionStartAt) / motionDurationMs, 1);
            const easedProgress = smoothStep(progress);

            currentAngle =
                motionStartAngle +
                (motionTargetAngle - motionStartAngle) * easedProgress;

            if (progress >= 1) {
                currentAngle = motionTargetAngle;
                state = STATE_HOLDING;
                holdStartAt = timestamp;
                updateStatus();
            }
        }

        function updateHolding(timestamp) {
            if (timestamp - holdStartAt < STOP_HOLD_MS) {
                return;
            }

            if (queuedCommand !== null) {
                const nextCommand = queuedCommand;
                queuedCommand = null;
                applyNewCommand(nextCommand, timestamp);
                return;
            }

            repeatCurrentCommand(timestamp);
        }

        function animationLoop(timestamp) {
            if (lastFrameAt === null) {
                lastFrameAt = timestamp;
            }

            lastFrameAt = timestamp;

            if (state === STATE_ROTATING) {
                updateRotating(timestamp);
            } else if (state === STATE_HOLDING) {
                updateHolding(timestamp);
            }

            renderMarker();

            if (state !== STATE_IDLE || queuedCommand !== null) {
                animationId = requestAnimationFrame(animationLoop);
            } else {
                animationId = null;
                lastFrameAt = null;
            }
        }

        function sendCommand() {
            const command = parseCommand(commandInput.value);

            if (command === null) {
                errorMessage.textContent = '0以上の整数を入力してください';
                return;
            }

            errorMessage.textContent = '';

            if (command === 0) {
                stopCommand();
                return;
            }

            if (state === STATE_IDLE) {
                applyNewCommand(command, performance.now());
                return;
            }

            queuedCommand = command;
            updateStatus();
        }

        function stopCommand() {
            queuedCommand = null;
            currentCommand = null;
            state = STATE_IDLE;

            motionStartAngle = currentAngle;
            motionTargetAngle = currentAngle;
            motionStartAt = 0;
            motionDurationMs = 0;
            holdStartAt = 0;

            if (animationId !== null) {
                cancelAnimationFrame(animationId);
                animationId = null;
            }

            lastFrameAt = null;
            updateStatus();
            renderMarker();
        }

        sendBtn.addEventListener('click', sendCommand);
        stopBtn.addEventListener('click', stopCommand);
        commandInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                sendCommand();
            }
        });

        window.addEventListener('beforeunload', function() {
            if (animationId !== null) {
                cancelAnimationFrame(animationId);
            }
        });

        stopCommand();
    </script>
</body>
</html>
```

- [aruco_rotate.html](/home/sato/robocon/AR_rotate/aruco_rotate.html)を上記内容へ更新済みです。
- コマンドを`0以上の安全な整数`へ拡張し、回転角を`command × 45°`に変更しました。
- コマンド0と停止ボタンの処理を`stopCommand()`へ共通化しました。
- 新規コマンドだけ方向を反転し、自動反復では同じ方向を維持します。
- 1件の予約と上書き、400ms保持、360°/秒、累積角度を維持しています。
- JavaScript構文、指定された角度・時間・停止・予約・方向・入力検証をテストし、Chromeでの読み込みと画像参照も確認済みです。

<details>
<summary>Codex run log</summary>

- status: Codex CLI: codex --ask-for-approval never -C /home/sato/robocon/AR_rotate exec --sandbox danger-full-access resume --skip-git-repo-check --json 019f3d06-2821-7050-9984-8086b7331ad3 "<prompt omitted, 5801 chars>"
- status: Codex thread: 019f3d06-2821-7050-9984-8086b7331ad3
- status: Codex turn started
- command: /bin/bash -lc "sed -n '1,260p' aruco_rotate.html"
- stdout: <!DOCTYPE html>
  <html lang="ja">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Aruco36_12 コマンド送信シミュレータ</title>
      <style>
          body {
              font-family: sans-serif;
              text-align: center;
              background-color: white;
              padding: 20px;
          }
  
          h1 {
              color: #333;
          }
  
          .controls {
              margin: 30px auto;
              padding: 20px;
              background: white;
              border-radius: 10px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
              max-width: 500px;
          }
  
          input[type="number"] {
              font-size: 24px;
              padding: 10px;
              width: 120px;
              text-align: center;
              border: 2px solid #ddd;
              border-radius: 5px;
          }
  
          button {
              margin-top: 15px;
              padding: 10px 20px;
              font-size: 16px;
              background-color: #007bff;
              color: white;
              border: none;
              border-radius: 5px;
              cursor: pointer;
          }
  
          button:hover {
              background-color: #0056b3;
          }
  
          .command-info {
              margin-top: 15px;
              font-family: monospace;
              color: #555;
          }
  
          .marker-container {
              display: flex;
              justify-content: center;
              gap: 120px;
              margin-top: 80px;
              flex-wrap: wrap;
              perspective: 1000px;
          }
  
          .marker-box {
              display: flex;
              flex-direction: column;
              align-items: center;
              text-align: center;
          }
  
          .aruco-marker {
              width: 220px;
              height: 220px;
              background-color: white;
              border: none;
              position: relative;
              box-shadow: none;
              padding: 10px;
          }
  
          .marker-image {
              width: 100%;
              height: 100%;
              object-fit: contain;
              display: block;
              image-rendering: pixelated;
          }
  
          .label {
              margin-top: 40px;
              font-weight: bold;
              color: #666;
          }
  
          .marker-title {
              margin-bottom: 40px;
          }
  
          .marker-status {
              margin-top: 60px;
          }
  
          .value {
              color: #007bff;
          }
      </style>
  </head>
  <body>
      <h1>Aruco36_12 コマンド送信シミュレータ</h1>
      <p>ID:0を固定用Aruco、ID:1を一定角速度で相対角度だけ回転するArucoとして表示します。</p>
  
      <div class="controls">
          <label for="commandInput">送信コマンド (0-7): </label><br>
          <input type="number" id="commandInput" min="0" max="7" value="1">
          <div class="command-info" id="commandInfo">State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none</div>
          <button id="sendBtn">コレを送れ</button>
          <button id="idleBtn">IDLEリセット</button>
      </div>
  
      <div class="marker-container">
          <div class="marker-box">
              <div class="label marker-title">回転用Aruco / ID: 1</div>
              <div class="aruco-marker" id="rotatingMarker" style="transform: rotate(0deg);">
                  <img src="aruco36_12_0001.png" class="marker-image" alt="Aruco36_12 ID 1">
              </div>
              <div class="label marker-status">状態: <span id="commandValue">IDLE</span> / 相対回転角: <span id="deltaValue" class="value">-</span></div>
              <div class="label">トグル: <span id="toggleValue" class="value">-</span> / 向き: <span id="rotationDirection" class="value">時計回り</span></div>
              <div class="label">予約: <span id="queueValue" class="value">なし</span></div>
          </div>
  
          <div class="marker-box">
              <div class="label marker-title">座標固定用Aruco / ID: 0</div>
              <div class="aruco-marker" style="transform: rotate(0deg);">
                  <img src="aruco36_12_0000.png" class="marker-image" alt="Aruco36_12 ID 0">
              </div>
              <div class="label marker-status">基準マーカー</div>
          </div>
      </div>
  
      <script>
          const commandInput = document.getElementById('commandInput');
          const commandInfo = document.getElementById('commandInfo');
          const rotatingMarker = document.getElementById('rotatingMarker');
          const commandValue = document.getElementById('commandValue');
          const deltaValue = document.getElementById('deltaValue');
          const toggleValue = document.getElementById('toggleValue');
          const rotationDirection = document.getElementById('rotationDirection');
          const queueValue = document.getElementById('queueValue');
          const sendBtn = document.getElementById('sendBtn');
          const idleBtn = document.getElementById('idleBtn');
  
          const ANGLE_STEP = 45;
          const MOTOR_DEGREES_PER_SECOND = 360;
          const STOP_HOLD_MS = 400;
          const TOGGLE_CLOCKWISE = 0;
          const TOGGLE_COUNTER_CLOCKWISE = 1;
  
          const STATE_IDLE = 'IDLE';
          const STATE_ROTATING = 'ROTATING';
          const STATE_HOLDING = 'HOLDING';
  
          let state = STATE_IDLE;
          let currentCommand = null;
          let currentToggle = TOGGLE_CLOCKWISE;
          let currentAngle = 0;
          let motionStartAngle = 0;
          let motionTargetAngle = 0;
          let motionStartAt = 0;
          let motionDurationMs = 0;
          let holdStartAt = 0;
          let animationId = null;
          let lastFrameAt = null;
          let queuedCommand = null;
  
          function normalizeCommand(value) {
              let command = parseInt(value, 10);
  
              if (isNaN(command)) command = 0;
              return Math.max(0, Math.min(7, command));
          }
  
          function commandToStepCount(command) {
              return command === 0 ? 8 : command;
          }
  
          function commandToDeltaAngle(command) {
              return commandToStepCount(command) * ANGLE_STEP;
          }
  
          function getDeltaText() {
              if (currentCommand === null) return '-';
              return commandToDeltaAngle(currentCommand) + '°';
          }
  
          function getDirectionSign() {
              return currentToggle === TOGGLE_CLOCKWISE ? 1 : -1;
          }
  
          function flipToggle() {
              currentToggle =
                  currentToggle === TOGGLE_CLOCKWISE
                      ? TOGGLE_COUNTER_CLOCKWISE
                      : TOGGLE_CLOCKWISE;
          }
  
          function smoothStep(progress) {
              return progress * progress * (3 - 2 * progress);
          }
  
          function updateStatus() {
              const deltaText = getDeltaText();
              const directionText = currentToggle === TOGGLE_CLOCKWISE ? '時計回り' : '反時計回り';
              const queuedText = queuedCommand === null ? 'none' : queuedCommand;
              const activeText = currentCommand === null ? 'IDLE' : currentCommand;
              const toggleText = currentCommand === null ? '-' : currentToggle;
  
              commandValue.textContent = activeText;
              deltaValue.textContent = deltaText;
              toggleValue.textContent = toggleText;
              rotationDirection.textContent = directionText;
              queueValue.textContent = queuedCommand === null ? 'なし' : queuedCommand;
              commandInfo.textContent = `State: ${state} / Active: ${activeText} / Delta: ${deltaText} / Toggle: ${toggleText} / Queue: ${queuedText}`;
          }
  
          function renderMarker() {
              rotatingMarker.style.transform = `rotate(${currentAngle}deg)`;
          }
  
          function startAnimation() {
              if (animationId !== null) return;
              lastFrameAt = null;
              animationId = requestAnimationFrame(animationLoop);
          }
  
          function startCommandMotion(command, timestamp) {
              const deltaAngle = commandToDeltaAngle(command);
              const signedDeltaAngle = deltaAngle * getDirectionSign();
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle + signedDeltaAngle;
              motionStartAt = timestamp;
              motionDurationMs = (deltaAngle / MOTOR_DEGREES_PER_SECOND) * 1000;
              state = STATE_ROTATING;
  
              updateStatus();
              startAnimation();
          }
  
          function applyCommand(command, timestamp) {
              currentCommand = command;
              flipToggle();
              startCommandMotion(command, timestamp);
          }
  
          function updateRotating(timestamp) {
              const progress = Math.min((timestamp - motionStartAt) / motionDurationMs, 1);
              const easedProgress = smoothStep(progress);
  
- status: Command exited with code 0
- command: /bin/bash -lc "sed -n '261,520p' aruco_rotate.html"
- stdout: 
              currentAngle =
                  motionStartAngle +
                  (motionTargetAngle - motionStartAngle) * easedProgress;
  
              if (progress >= 1) {
                  currentAngle = motionTargetAngle;
                  state = STATE_HOLDING;
                  holdStartAt = timestamp;
                  updateStatus();
              }
          }
  
          function updateHolding(timestamp) {
              if (timestamp - holdStartAt < STOP_HOLD_MS) {
                  return;
              }
  
              if (queuedCommand !== null) {
                  const nextCommand = queuedCommand;
                  queuedCommand = null;
                  applyCommand(nextCommand, timestamp);
                  return;
              }
  
              if (currentCommand !== null) {
                  startCommandMotion(currentCommand, timestamp);
              }
          }
  
          function animationLoop(timestamp) {
              if (lastFrameAt === null) {
                  lastFrameAt = timestamp;
              }
  
              lastFrameAt = timestamp;
  
              if (state === STATE_ROTATING) {
                  updateRotating(timestamp);
              } else if (state === STATE_HOLDING) {
                  updateHolding(timestamp);
              }
  
              renderMarker();
  
              if (state !== STATE_IDLE || queuedCommand !== null) {
                  animationId = requestAnimationFrame(animationLoop);
              } else {
                  animationId = null;
                  lastFrameAt = null;
              }
          }
  
          function sendCommand() {
              const command = normalizeCommand(commandInput.value);
  
              if (state === STATE_IDLE) {
                  applyCommand(command, performance.now());
                  return;
              }
  
              queuedCommand = command;
              updateStatus();
          }
  
          function resetToIdle() {
              queuedCommand = null;
              currentCommand = null;
              state = STATE_IDLE;
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle;
              motionDurationMs = 0;
              holdStartAt = 0;
  
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
                  animationId = null;
              }
  
              lastFrameAt = null;
              updateStatus();
              renderMarker();
          }
  
          sendBtn.addEventListener('click', sendCommand);
          idleBtn.addEventListener('click', resetToIdle);
  
          window.addEventListener('beforeunload', function() {
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
              }
          });
  
          resetToIdle();
      </script>
  </body>
  </html>
  
- status: Command exited with code 0
- command: /bin/bash -lc "rg -n \"normalizeCommand|commandToStepCount|max=\\\"7\\\"|IDLEリセット|applyCommand|command === 0 \\? 8\" aruco_rotate.html"
- status: Command exited with code 1
- command: /bin/bash -lc 'rg -n "parseCommand|stopCommand|applyNewCommand|repeatCurrentCommand|commandToDeltaAngle|Direction" aruco_rotate.html'
- stdout: 138:            <div class="label">トグル: <span id="toggleValue" class="value">-</span> / 向き: <span id="rotationDirection" class="value">時計回り</span></div>
  159:        const rotationDirection = document.getElementById('rotationDirection');
  187:        function parseCommand(value) {
  195:        function commandToDeltaAngle(command) {
  201:            return commandToDeltaAngle(currentCommand) + '°';
  204:        function getDirectionSign() {
  234:            rotationDirection.textContent = directionText;
  238:                : `State: ${state} / Active: ${activeText} / Delta: ${deltaText} / Toggle: ${toggleText} / Direction: ${directionText} / Queue: ${queuedText}`;
  252:            const deltaAngle = commandToDeltaAngle(command);
  253:            const signedDeltaAngle = deltaAngle * getDirectionSign();
  265:        function applyNewCommand(command, timestamp) {
  271:        function repeatCurrentCommand(timestamp) {
  301:                applyNewCommand(nextCommand, timestamp);
  305:            repeatCurrentCommand(timestamp);
  332:            const command = parseCommand(commandInput.value);
  342:                stopCommand();
  347:                applyNewCommand(command, performance.now());
  355:        function stopCommand() {
  377:        stopBtn.addEventListener('click', stopCommand);
  390:        stopCommand();
  
- status: Command exited with code 0
- command: /bin/bash -lc "node -e \"const fs=require('fs'),vm=require('vm'); const h=fs.readFileSync('aruco_rotate.html','utf8'); const s=h.match(/<script>([\\\\s\\\\S]*?)<\\\\/script>/)[1]; new vm.Script(s); console.log('JavaScript syntax: OK');\""
- stdout: JavaScript syntax: OK
  
- status: Command exited with code 0
- command: /bin/bash -lc "rg --files -g 'package.json' -g 'playwright*' -g 'node_modules/playwright*/package.json' . .. | head -80"
- stdout: ../abu2026-ros2-ws/src/teleop/controller_webui/package.json
  ../dev_abu2026-ros2-ws/src/teleop/controller_webui/package.json
  
- status: Command exited with code 0
- command: /bin/bash -lc 'command -v chromium || command -v chromium-browser || command -v google-chrome || command -v firefox'
- stdout: /usr/bin/google-chrome
  
- status: Command exited with code 0
- command: /bin/bash -lc "node <<'NODE'
  const fs = require('fs');
  const vm = require('vm');
  const html = fs.readFileSync('aruco_rotate.html', 'utf8');
  const script = html.match(/<script>([\\s\\S]*?)<\\/script>/)[1];
  const elements = new Map();
  for (const id of ['commandInput','errorMessage','commandInfo','rotatingMarker','commandValue','deltaValue','toggleValue','rotationDirection','queueValue','sendBtn','stopBtn']) {
    elements.set(id, { value: '', textContent: '', style: {}, addEventListener() {} });
  }
  elements.get('commandInput').value = '1';
  let rafId = 0;
  const context = {
    document: { getElementById: id => elements.get(id) },
    window: { addEventListener() {} },
    performance: { now: () => 0 },
    requestAnimationFrame: () => ++rafId,
    cancelAnimationFrame() {},
    console
  };
  const tests = "'`
  function assert(condition, message) {
      if (!condition) throw new Error(message);
  }
  
  assert(parseCommand('"'') === null, 'empty must be invalid');
  assert(parseCommand('abc') === null, 'text must be invalid');
  assert(parseCommand('-1') === null, 'negative must be invalid');
  assert(parseCommand('1.5') === null, 'decimal must be invalid');
  assert(parseCommand('9007199254740992') === null, 'unsafe integer must be invalid');
  assert(parseCommand('0') === 0 && parseCommand('16') === 16, 'valid integers must parse');
  assert(commandToDeltaAngle(0) === 0, 'command 0 must be 0 degrees');
  assert(commandToDeltaAngle(9) === 405, 'command 9 must be 405 degrees');
  
  stopCommand();
  applyNewCommand(8, 0);
  assert(state === STATE_ROTATING, 'command 8 must rotate');
  assert(motionTargetAngle === 360, 'command 8 must target 360 degrees');
  assert(motionDurationMs === 1000, 'command 8 must take 1 second');
  const command8Toggle = currentToggle;
  updateRotating(1000);
  assert(state === STATE_HOLDING, 'completed motion must hold');
  updateHolding(1400);
  assert(state === STATE_ROTATING, 'command 8 must repeat after 400 ms');
  assert(motionTargetAngle === 720, 'command 8 repeat must add 360 degrees');
  assert(currentToggle === command8Toggle, 'automatic repeat must preserve direction');
  
  stopCommand();
  applyNewCommand(16, 0);
  assert(commandToDeltaAngle(16) === 720, 'command 16 must be 720 degrees');
  assert(motionDurationMs === 2000, 'command 16 must take 2 seconds');
  
  stopCommand();
  applyNewCommand(5, 0);
  updateRotating(300);
  const stoppedAngle = currentAngle;
  queuedCommand = 12;
  stopCommand();
  assert(state === STATE_IDLE, 'stop must enter IDLE');
  assert(currentCommand === null && queuedCommand === null, 'stop must clear active and queue');
  assert(currentAngle === stoppedAngle, 'stop must preserve current angle');
  
  currentAngle = 0;
  currentToggle = TOGGLE_COUNTER_CLOCKWISE;
  stopCommand();
  applyNewCommand(4, 0);
  assert(currentToggle === TOGGLE_CLOCKWISE, 'first new command must be clockwise');
  queuedCommand = 8;
  queuedCommand = 12;
  updateRotating(500);
  updateHolding(900);
  assert(currentCommand === 12, 'latest queued command must replace older queue');
  assert(queuedCommand === null, 'started queue must be consumed');
  assert(currentToggle === TOGGLE_COUNTER_CLOCKWISE, 'queued new command must reverse direction');
  assert(motionDurationMs === 1500, 'command 12 must take 1.5 seconds');
  
  stopCommand();
  commandInput.value = '1.5';
  sendCommand();
  assert(state === STATE_IDLE, 'invalid input must not start motion');
  assert(errorMessage.textContent === '0以上の整数を入力してください', 'invalid input must show error');
  commandInput.value = '9';
  sendCommand();
  assert(errorMessage.textContent === '', 'valid input must clear error');
  assert(currentCommand === 9 && commandToDeltaAngle(currentCommand) === 405, 'command 9 must start as 405 degrees');
  
  console.log('Behavior tests: OK');
  "'`;
  vm.runInNewContext(script + tests, context);
  NODE'
- stdout: Behavior tests: OK
  
- status: Command exited with code 0
- command: /bin/bash -lc "test -f aruco36_12_0000.png && test -f aruco36_12_0001.png && echo 'Marker images: OK'"
- stdout: Marker images: OK
  
- status: Command exited with code 0
- command: /bin/bash -lc 'git diff -- aruco_rotate.html'
- stdout: diff --git a/aruco_rotate.html b/aruco_rotate.html
  index 8a19e47..16b86f0 100644
  --- a/aruco_rotate.html
  +++ b/aruco_rotate.html
  @@ -55,6 +55,13 @@
               color: #555;
           }
   
  +        .error-message {
  +            min-height: 1.5em;
  +            margin-top: 10px;
  +            color: #c62828;
  +            font-weight: bold;
  +        }
  +
           .marker-container {
               display: flex;
               justify-content: center;
  @@ -113,11 +120,12 @@
       <p>ID:0を固定用Aruco、ID:1を一定角速度で相対角度だけ回転するArucoとして表示します。</p>
   
       <div class="controls">
  -        <label for="commandInput">送信コマンド (0-7): </label><br>
  -        <input type="number" id="commandInput" min="0" max="7" value="1">
  +        <label for="commandInput">送信コマンド（0: 停止、1以上: 45°刻み）</label><br>
  +        <input type="number" id="commandInput" min="0" step="1" value="1">
  +        <div class="error-message" id="errorMessage" role="alert"></div>
           <div class="command-info" id="commandInfo">State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none</div>
           <button id="sendBtn">コレを送れ</button>
  -        <button id="idleBtn">IDLEリセット</button>
  +        <button id="stopBtn">停止</button>
       </div>
   
       <div class="marker-container">
  @@ -142,6 +150,7 @@
   
       <script>
           const commandInput = document.getElementById('commandInput');
  +        const errorMessage = document.getElementById('errorMessage');
           const commandInfo = document.getElementById('commandInfo');
           const rotatingMarker = document.getElementById('rotatingMarker');
           const commandValue = document.getElementById('commandValue');
  @@ -150,7 +159,7 @@
           const rotationDirection = document.getElementById('rotationDirection');
           const queueValue = document.getElementById('queueValue');
           const sendBtn = document.getElementById('sendBtn');
  -        const idleBtn = document.getElementById('idleBtn');
  +        const stopBtn = document.getElementById('stopBtn');
   
           const ANGLE_STEP = 45;
           const MOTOR_DEGREES_PER_SECOND = 360;
  @@ -164,7 +173,7 @@
   
           let state = STATE_IDLE;
           let currentCommand = null;
  -        let currentToggle = TOGGLE_CLOCKWISE;
  +        let currentToggle = TOGGLE_COUNTER_CLOCKWISE;
           let currentAngle = 0;
           let motionStartAngle = 0;
           let motionTargetAngle = 0;
  @@ -175,19 +184,16 @@
           let lastFrameAt = null;
           let queuedCommand = null;
   
  -        function normalizeCommand(value) {
  -            let command = parseInt(value, 10);
  +        function parseCommand(value) {
  +            if (value.trim() === '') return null;
   
  -            if (isNaN(command)) command = 0;
  -            return Math.max(0, Math.min(7, command));
  -        }
  -
  -        function commandToStepCount(command) {
  -            return command === 0 ? 8 : command;
  +            const command = Number(value);
  +            if (!Number.isSafeInteger(command) || command < 0) return null;
  +            return command;
           }
   
           function commandToDeltaAngle(command) {
  -            return commandToStepCount(command) * ANGLE_STEP;
  +            return command * ANGLE_STEP;
           }
   
           function getDeltaText() {
  @@ -212,17 +218,24 @@
   
           function updateStatus() {
               const deltaText = getDeltaText();
  -            const directionText = currentToggle === TOGGLE_CLOCKWISE ? '時計回り' : '反時計回り';
               const queuedText = queuedCommand === null ? 'none' : queuedCommand;
               const activeText = currentCommand === null ? 'IDLE' : currentCommand;
               const toggleText = currentCommand === null ? '-' : currentToggle;
  +            const directionText =
  +                currentCommand === null
  +                    ? '-'
  +                    : currentToggle === TOGGLE_CLOCKWISE
  +                        ? '時計回り'
  +                        : '反時計回り';
   
               commandValue.textContent = activeText;
               deltaValue.textContent = deltaText;
               toggleValue.textContent = toggleText;
               rotationDirection.textContent = directionText;
               queueValue.textContent = queuedCommand === null ? 'なし' : queuedCommand;
  -            commandInfo.textContent = `State: ${state} / Active: ${activeText} / Delta: ${deltaText} / Toggle: ${toggleText} / Queue: ${queuedText}`;
  +            commandInfo.textContent = currentCommand === null
  +                ? 'State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none'
  +                : `State: ${state} / Active: ${activeText} / Delta: ${deltaText} / Toggle: ${toggleText} / Direction: ${directionText} / Queue: ${queuedText}`;
           }
   
           function renderMarker() {
  @@ -249,12 +262,18 @@
               startAnimation();
           }
   
  -        function applyCommand(command, timestamp) {
  +        function applyNewCommand(command, timestamp) {
               currentCommand = command;
               flipToggle();
               startCommandMotion(command, timestamp);
           }
   
  +        function repeatCurrentCommand(timestamp) {
  +            if (currentCommand !== null) {
  +                startCommandMotion(currentCommand, timestamp);
  +            }
  +        }
  +
           function updateRotating(timestamp) {
               const progress = Math.min((timestamp - motionStartAt) / motionDurationMs, 1);
               const easedProgress = smoothStep(progress);
  @@ -279,13 +298,11 @@
               if (queuedCommand !== null) {
                   const nextCommand = queuedCommand;
                   queuedCommand = null;
  -                applyCommand(nextCommand, timestamp);
  +                applyNewCommand(nextCommand, timestamp);
                   return;
               }
   
  -            if (currentCommand !== null) {
  -                startCommandMotion(currentCommand, timestamp);
  -            }
  +            repeatCurrentCommand(timestamp);
           }
   
           function animationLoop(timestamp) {
  @@ -312,10 +329,22 @@
           }
   
           function sendCommand() {
  -            const command = normalizeCommand(commandInput.value);
  +            const command = parseCommand(commandInput.value);
  +
  +            if (command === null) {
  +                errorMessage.textContent = '0以上の整数を入力してください';
  +                return;
  +            }
  +
  +            errorMessage.textContent = '';
  +
  +            if (command === 0) {
  +                stopCommand();
  +                return;
  +            }
   
               if (state === STATE_IDLE) {
  -                applyCommand(command, performance.now());
  +                applyNewCommand(command, performance.now());
                   return;
               }
   
  @@ -323,13 +352,14 @@
               updateStatus();
           }
   
  -        function resetToIdle() {
  +        function stopCommand() {
               queuedCommand = null;
               currentCommand = null;
               state = STATE_IDLE;
   
               motionStartAngle = currentAngle;
               motionTargetAngle = currentAngle;
  +            motionStartAt = 0;
               motionDurationMs = 0;
               holdStartAt = 0;
   
  @@ -344,7 +374,12 @@
           }
   
           sendBtn.addEventListener('click', sendCommand);
  -        idleBtn.addEventListener('click', resetToIdle);
  +        stopBtn.addEventListener('click', stopCommand);
  +        commandInput.addEventListener('keydown', function(event) {
  +            if (event.key === 'Enter') {
  +                sendCommand();
  +            }
  +        });
   
           window.addEventListener('beforeunload', function() {
               if (animationId !== null) {
  @@ -352,7 +387,7 @@
               }
           });
   
  -        resetToIdle();
  +        stopCommand();
       </script>
   </body>
   </html>
  
- status: Command exited with code 0
- command: /bin/bash -lc 'google-chrome --headless --no-sandbox --disable-gpu --dump-dom file:///home/sato/robocon/AR_rotate/aruco_rotate.html'
- stdout: <!DOCTYPE html>
  <html lang="ja"><head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Aruco36_12 コマンド送信シミュレータ</title>
      <style>
          body {
              font-family: sans-serif;
              text-align: center;
              background-color: white;
              padding: 20px;
          }
  
          h1 {
              color: #333;
          }
  
          .controls {
              margin: 30px auto;
              padding: 20px;
              background: white;
              border-radius: 10px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
              max-width: 500px;
          }
  
          input[type="number"] {
              font-size: 24px;
              padding: 10px;
              width: 120px;
              text-align: center;
              border: 2px solid #ddd;
              border-radius: 5px;
          }
  
          button {
              margin-top: 15px;
              padding: 10px 20px;
              font-size: 16px;
              background-color: #007bff;
              color: white;
              border: none;
              border-radius: 5px;
              cursor: pointer;
          }
  
          button:hover {
              background-color: #0056b3;
          }
  
          .command-info {
              margin-top: 15px;
              font-family: monospace;
              color: #555;
          }
  
          .error-message {
              min-height: 1.5em;
              margin-top: 10px;
              color: #c62828;
              font-weight: bold;
          }
  
          .marker-container {
              display: flex;
              justify-content: center;
              gap: 120px;
              margin-top: 80px;
              flex-wrap: wrap;
              perspective: 1000px;
          }
  
          .marker-box {
              display: flex;
              flex-direction: column;
              align-items: center;
              text-align: center;
          }
  
          .aruco-marker {
              width: 220px;
              height: 220px;
              background-color: white;
              border: none;
              position: relative;
              box-shadow: none;
              padding: 10px;
          }
  
          .marker-image {
              width: 100%;
              height: 100%;
              object-fit: contain;
              display: block;
              image-rendering: pixelated;
          }
  
          .label {
              margin-top: 40px;
              font-weight: bold;
              color: #666;
          }
  
          .marker-title {
              margin-bottom: 40px;
          }
  
          .marker-status {
              margin-top: 60px;
          }
  
          .value {
              color: #007bff;
          }
      </style>
  </head>
  <body>
      <h1>Aruco36_12 コマンド送信シミュレータ</h1>
      <p>ID:0を固定用Aruco、ID:1を一定角速度で相対角度だけ回転するArucoとして表示します。</p>
  
      <div class="controls">
          <label for="commandInput">送信コマンド（0: 停止、1以上: 45°刻み）</label><br>
          <input type="number" id="commandInput" min="0" step="1" value="1">
          <div class="error-message" id="errorMessage" role="alert"></div>
          <div class="command-info" id="commandInfo">State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none</div>
          <button id="sendBtn">コレを送れ</button>
          <button id="stopBtn">停止</button>
      </div>
  
      <div class="marker-container">
          <div class="marker-box">
              <div class="label marker-title">回転用Aruco / ID: 1</div>
              <div class="aruco-marker" id="rotatingMarker" style="transform: rotate(0deg);">
                  <img src="aruco36_12_0001.png" class="marker-image" alt="Aruco36_12 ID 1">
              </div>
              <div class="label marker-status">状態: <span id="commandValue">IDLE</span> / 相対回転角: <span id="deltaValue" class="value">-</span></div>
              <div class="label">トグル: <span id="toggleValue" class="value">-</span> / 向き: <span id="rotationDirection" class="value">-</span></div>
              <div class="label">予約: <span id="queueValue" class="value">なし</span></div>
          </div>
  
          <div class="marker-box">
              <div class="label marker-title">座標固定用Aruco / ID: 0</div>
              <div class="aruco-marker" style="transform: rotate(0deg);">
                  <img src="aruco36_12_0000.png" class="marker-image" alt="Aruco36_12 ID 0">
              </div>
              <div class="label marker-status">基準マーカー</div>
          </div>
      </div>
  
      <script>
          const commandInput = document.getElementById('commandInput');
          const errorMessage = document.getElementById('errorMessage');
          const commandInfo = document.getElementById('commandInfo');
          const rotatingMarker = document.getElementById('rotatingMarker');
          const commandValue = document.getElementById('commandValue');
          const deltaValue = document.getElementById('deltaValue');
          const toggleValue = document.getElementById('toggleValue');
          const rotationDirection = document.getElementById('rotationDirection');
          const queueValue = document.getElementById('queueValue');
          const sendBtn = document.getElementById('sendBtn');
          const stopBtn = document.getElementById('stopBtn');
  
          const ANGLE_STEP = 45;
          const MOTOR_DEGREES_PER_SECOND = 360;
          const STOP_HOLD_MS = 400;
          const TOGGLE_CLOCKWISE = 0;
          const TOGGLE_COUNTER_CLOCKWISE = 1;
  
          const STATE_IDLE = 'IDLE';
          const STATE_ROTATING = 'ROTATING';
          const STATE_HOLDING = 'HOLDING';
  
          let state = STATE_IDLE;
          let currentCommand = null;
          let currentToggle = TOGGLE_COUNTER_CLOCKWISE;
          let currentAngle = 0;
          let motionStartAngle = 0;
          let motionTargetAngle = 0;
          let motionStartAt = 0;
          let motionDurationMs = 0;
          let holdStartAt = 0;
          let animationId = null;
          let lastFrameAt = null;
          let queuedCommand = null;
  
          function parseCommand(value) {
              if (value.trim() === '') return null;
  
              const command = Number(value);
              if (!Number.isSafeInteger(command) || command < 0) return null;
              return command;
          }
  
          function commandToDeltaAngle(command) {
              return command * ANGLE_STEP;
          }
  
          function getDeltaText() {
              if (currentCommand === null) return '-';
              return commandToDeltaAngle(currentCommand) + '°';
          }
  
          function getDirectionSign() {
              return currentToggle === TOGGLE_CLOCKWISE ? 1 : -1;
          }
  
          function flipToggle() {
              currentToggle =
                  currentToggle === TOGGLE_CLOCKWISE
                      ? TOGGLE_COUNTER_CLOCKWISE
                      : TOGGLE_CLOCKWISE;
          }
  
          function smoothStep(progress) {
              return progress * progress * (3 - 2 * progress);
          }
  
          function updateStatus() {
              const deltaText = getDeltaText();
              const queuedText = queuedCommand === null ? 'none' : queuedCommand;
              const activeText = currentCommand === null ? 'IDLE' : currentCommand;
              const toggleText = currentCommand === null ? '-' : currentToggle;
              const directionText =
                  currentCommand === null
                      ? '-'
                      : currentToggle === TOGGLE_CLOCKWISE
                          ? '時計回り'
                          : '反時計回り';
  
              commandValue.textContent = activeText;
              deltaValue.textContent = deltaText;
              toggleValue.textContent = toggleText;
              rotationDirection.textContent = directionText;
              queueValue.textContent = queuedCommand === null ? 'なし' : queuedCommand;
              commandInfo.textContent = currentCommand === null
                  ? 'State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none'
                  : `State: ${state} / Active: ${activeText} / Delta: ${deltaText} / Toggle: ${toggleText} / Direction: ${directionText} / Queue: ${queuedText}`;
          }
  
          function renderMarker() {
              rotatingMarker.style.transform = `rotate(${currentAngle}deg)`;
          }
  
          function startAnimation() {
              if (animationId !== null) return;
              lastFrameAt = null;
              animationId = requestAnimationFrame(animationLoop);
          }
  
          function startCommandMotion(command, timestamp) {
              const deltaAngle = commandToDeltaAngle(command);
              const signedDeltaAngle = deltaAngle * getDirectionSign();
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle + signedDeltaAngle;
              motionStartAt = timestamp;
              motionDurationMs = (deltaAngle / MOTOR_DEGREES_PER_SECOND) * 1000;
              state = STATE_ROTATING;
  
              updateStatus();
              startAnimation();
          }
  
          function applyNewCommand(command, timestamp) {
              currentCommand = command;
              flipToggle();
              startCommandMotion(command, timestamp);
          }
  
          function repeatCurrentCommand(timestamp) {
              if (currentCommand !== null) {
                  startCommandMotion(currentCommand, timestamp);
              }
          }
  
          function updateRotating(timestamp) {
              const progress = Math.min((timestamp - motionStartAt) / motionDurationMs, 1);
              const easedProgress = smoothStep(progress);
  
              currentAngle =
                  motionStartAngle +
                  (motionTargetAngle - motionStartAngle) * easedProgress;
  
              if (progress >= 1) {
                  currentAngle = motionTargetAngle;
                  state = STATE_HOLDING;
                  holdStartAt = timestamp;
                  updateStatus();
              }
          }
  
          function updateHolding(timestamp) {
              if (timestamp - holdStartAt < STOP_HOLD_MS) {
                  return;
              }
  
              if (queuedCommand !== null) {
                  const nextCommand = queuedCommand;
                  queuedCommand = null;
                  applyNewCommand(nextCommand, timestamp);
                  return;
              }
  
              repeatCurrentCommand(timestamp);
          }
  
          function animationLoop(timestamp) {
              if (lastFrameAt === null) {
                  lastFrameAt = timestamp;
              }
  
              lastFrameAt = timestamp;
  
              if (state === STATE_ROTATING) {
                  updateRotating(timestamp);
              } else if (state === STATE_HOLDING) {
                  updateHolding(timestamp);
              }
  
              renderMarker();
  
              if (state !== STATE_IDLE || queuedCommand !== null) {
                  animationId = requestAnimationFrame(animationLoop);
              } else {
                  animationId = null;
                  lastFrameAt = null;
              }
          }
  
          function sendCommand() {
              const command = parseCommand(commandInput.value);
  
              if (command === null) {
                  errorMessage.textContent = '0以上の整数を入力してください';
                  return;
              }
  
              errorMessage.textContent = '';
  
              if (command === 0) {
                  stopCommand();
                  return;
              }
  
              if (state === STATE_IDLE) {
                  applyNewCommand(command, performance.now());
                  return;
              }
  
              queuedCommand = command;
              updateStatus();
          }
  
          function stopCommand() {
              queuedCommand = null;
              currentCommand = null;
              state = STATE_IDLE;
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle;
              motionStartAt = 0;
              motionDurationMs = 0;
              holdStartAt = 0;
  
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
                  animationId = null;
              }
  
              lastFrameAt = null;
              updateStatus();
              renderMarker();
          }
  
          sendBtn.addEventListener('click', sendCommand);
          stopBtn.addEventListener('click', stopCommand);
          commandInput.addEventListener('keydown', function(event) {
              if (event.key === 'Enter') {
                  sendCommand();
              }
          });
  
          window.addEventListener('beforeunload', function() {
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
              }
          });
  
          stopCommand();
      </script>
  
  
  </body></html>
  
- status: Command exited with code 0
- command: /bin/bash -lc "sed -n '1,430p' aruco_rotate.html"
- stdout: <!DOCTYPE html>
  <html lang="ja">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Aruco36_12 コマンド送信シミュレータ</title>
      <style>
          body {
              font-family: sans-serif;
              text-align: center;
              background-color: white;
              padding: 20px;
          }
  
          h1 {
              color: #333;
          }
  
          .controls {
              margin: 30px auto;
              padding: 20px;
              background: white;
              border-radius: 10px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
              max-width: 500px;
          }
  
          input[type="number"] {
              font-size: 24px;
              padding: 10px;
              width: 120px;
              text-align: center;
              border: 2px solid #ddd;
              border-radius: 5px;
          }
  
          button {
              margin-top: 15px;
              padding: 10px 20px;
              font-size: 16px;
              background-color: #007bff;
              color: white;
              border: none;
              border-radius: 5px;
              cursor: pointer;
          }
  
          button:hover {
              background-color: #0056b3;
          }
  
          .command-info {
              margin-top: 15px;
              font-family: monospace;
              color: #555;
          }
  
          .error-message {
              min-height: 1.5em;
              margin-top: 10px;
              color: #c62828;
              font-weight: bold;
          }
  
          .marker-container {
              display: flex;
              justify-content: center;
              gap: 120px;
              margin-top: 80px;
              flex-wrap: wrap;
              perspective: 1000px;
          }
  
          .marker-box {
              display: flex;
              flex-direction: column;
              align-items: center;
              text-align: center;
          }
  
          .aruco-marker {
              width: 220px;
              height: 220px;
              background-color: white;
              border: none;
              position: relative;
              box-shadow: none;
              padding: 10px;
          }
  
          .marker-image {
              width: 100%;
              height: 100%;
              object-fit: contain;
              display: block;
              image-rendering: pixelated;
          }
  
          .label {
              margin-top: 40px;
              font-weight: bold;
              color: #666;
          }
  
          .marker-title {
              margin-bottom: 40px;
          }
  
          .marker-status {
              margin-top: 60px;
          }
  
          .value {
              color: #007bff;
          }
      </style>
  </head>
  <body>
      <h1>Aruco36_12 コマンド送信シミュレータ</h1>
      <p>ID:0を固定用Aruco、ID:1を一定角速度で相対角度だけ回転するArucoとして表示します。</p>
  
      <div class="controls">
          <label for="commandInput">送信コマンド（0: 停止、1以上: 45°刻み）</label><br>
          <input type="number" id="commandInput" min="0" step="1" value="1">
          <div class="error-message" id="errorMessage" role="alert"></div>
          <div class="command-info" id="commandInfo">State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none</div>
          <button id="sendBtn">コレを送れ</button>
          <button id="stopBtn">停止</button>
      </div>
  
      <div class="marker-container">
          <div class="marker-box">
              <div class="label marker-title">回転用Aruco / ID: 1</div>
              <div class="aruco-marker" id="rotatingMarker" style="transform: rotate(0deg);">
                  <img src="aruco36_12_0001.png" class="marker-image" alt="Aruco36_12 ID 1">
              </div>
              <div class="label marker-status">状態: <span id="commandValue">IDLE</span> / 相対回転角: <span id="deltaValue" class="value">-</span></div>
              <div class="label">トグル: <span id="toggleValue" class="value">-</span> / 向き: <span id="rotationDirection" class="value">-</span></div>
              <div class="label">予約: <span id="queueValue" class="value">なし</span></div>
          </div>
  
          <div class="marker-box">
              <div class="label marker-title">座標固定用Aruco / ID: 0</div>
              <div class="aruco-marker" style="transform: rotate(0deg);">
                  <img src="aruco36_12_0000.png" class="marker-image" alt="Aruco36_12 ID 0">
              </div>
              <div class="label marker-status">基準マーカー</div>
          </div>
      </div>
  
      <script>
          const commandInput = document.getElementById('commandInput');
          const errorMessage = document.getElementById('errorMessage');
          const commandInfo = document.getElementById('commandInfo');
          const rotatingMarker = document.getElementById('rotatingMarker');
          const commandValue = document.getElementById('commandValue');
          const deltaValue = document.getElementById('deltaValue');
          const toggleValue = document.getElementById('toggleValue');
          const rotationDirection = document.getElementById('rotationDirection');
          const queueValue = document.getElementById('queueValue');
          const sendBtn = document.getElementById('sendBtn');
          const stopBtn = document.getElementById('stopBtn');
  
          const ANGLE_STEP = 45;
          const MOTOR_DEGREES_PER_SECOND = 360;
          const STOP_HOLD_MS = 400;
          const TOGGLE_CLOCKWISE = 0;
          const TOGGLE_COUNTER_CLOCKWISE = 1;
  
          const STATE_IDLE = 'IDLE';
          const STATE_ROTATING = 'ROTATING';
          const STATE_HOLDING = 'HOLDING';
  
          let state = STATE_IDLE;
          let currentCommand = null;
          let currentToggle = TOGGLE_COUNTER_CLOCKWISE;
          let currentAngle = 0;
          let motionStartAngle = 0;
          let motionTargetAngle = 0;
          let motionStartAt = 0;
          let motionDurationMs = 0;
          let holdStartAt = 0;
          let animationId = null;
          let lastFrameAt = null;
          let queuedCommand = null;
  
          function parseCommand(value) {
              if (value.trim() === '') return null;
  
              const command = Number(value);
              if (!Number.isSafeInteger(command) || command < 0) return null;
              return command;
          }
  
          function commandToDeltaAngle(command) {
              return command * ANGLE_STEP;
          }
  
          function getDeltaText() {
              if (currentCommand === null) return '-';
              return commandToDeltaAngle(currentCommand) + '°';
          }
  
          function getDirectionSign() {
              return currentToggle === TOGGLE_CLOCKWISE ? 1 : -1;
          }
  
          function flipToggle() {
              currentToggle =
                  currentToggle === TOGGLE_CLOCKWISE
                      ? TOGGLE_COUNTER_CLOCKWISE
                      : TOGGLE_CLOCKWISE;
          }
  
          function smoothStep(progress) {
              return progress * progress * (3 - 2 * progress);
          }
  
          function updateStatus() {
              const deltaText = getDeltaText();
              const queuedText = queuedCommand === null ? 'none' : queuedCommand;
              const activeText = currentCommand === null ? 'IDLE' : currentCommand;
              const toggleText = currentCommand === null ? '-' : currentToggle;
              const directionText =
                  currentCommand === null
                      ? '-'
                      : currentToggle === TOGGLE_CLOCKWISE
                          ? '時計回り'
                          : '反時計回り';
  
              commandValue.textContent = activeText;
              deltaValue.textContent = deltaText;
              toggleValue.textContent = toggleText;
              rotationDirection.textContent = directionText;
              queueValue.textContent = queuedCommand === null ? 'なし' : queuedCommand;
              commandInfo.textContent = currentCommand === null
                  ? 'State: IDLE / Active: IDLE / Delta: - / Toggle: - / Queue: none'
                  : `State: ${state} / Active: ${activeText} / Delta: ${deltaText} / Toggle: ${toggleText} / Direction: ${directionText} / Queue: ${queuedText}`;
          }
  
          function renderMarker() {
              rotatingMarker.style.transform = `rotate(${currentAngle}deg)`;
          }
  
          function startAnimation() {
              if (animationId !== null) return;
              lastFrameAt = null;
              animationId = requestAnimationFrame(animationLoop);
          }
  
          function startCommandMotion(command, timestamp) {
              const deltaAngle = commandToDeltaAngle(command);
              const signedDeltaAngle = deltaAngle * getDirectionSign();
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle + signedDeltaAngle;
              motionStartAt = timestamp;
              motionDurationMs = (deltaAngle / MOTOR_DEGREES_PER_SECOND) * 1000;
              state = STATE_ROTATING;
  
              updateStatus();
              startAnimation();
          }
  
          function applyNewCommand(command, timestamp) {
              currentCommand = command;
              flipToggle();
              startCommandMotion(command, timestamp);
          }
  
          function repeatCurrentCommand(timestamp) {
              if (currentCommand !== null) {
                  startCommandMotion(currentCommand, timestamp);
              }
          }
  
          function updateRotating(timestamp) {
              const progress = Math.min((timestamp - motionStartAt) / motionDurationMs, 1);
              const easedProgress = smoothStep(progress);
  
              currentAngle =
                  motionStartAngle +
                  (motionTargetAngle - motionStartAngle) * easedProgress;
  
              if (progress >= 1) {
                  currentAngle = motionTargetAngle;
                  state = STATE_HOLDING;
                  holdStartAt = timestamp;
                  updateStatus();
              }
          }
  
          function updateHolding(timestamp) {
              if (timestamp - holdStartAt < STOP_HOLD_MS) {
                  return;
              }
  
              if (queuedCommand !== null) {
                  const nextCommand = queuedCommand;
                  queuedCommand = null;
                  applyNewCommand(nextCommand, timestamp);
                  return;
              }
  
              repeatCurrentCommand(timestamp);
          }
  
          function animationLoop(timestamp) {
              if (lastFrameAt === null) {
                  lastFrameAt = timestamp;
              }
  
              lastFrameAt = timestamp;
  
              if (state === STATE_ROTATING) {
                  updateRotating(timestamp);
              } else if (state === STATE_HOLDING) {
                  updateHolding(timestamp);
              }
  
              renderMarker();
  
              if (state !== STATE_IDLE || queuedCommand !== null) {
                  animationId = requestAnimationFrame(animationLoop);
              } else {
                  animationId = null;
                  lastFrameAt = null;
              }
          }
  
          function sendCommand() {
              const command = parseCommand(commandInput.value);
  
              if (command === null) {
                  errorMessage.textContent = '0以上の整数を入力してください';
                  return;
              }
  
              errorMessage.textContent = '';
  
              if (command === 0) {
                  stopCommand();
                  return;
              }
  
              if (state === STATE_IDLE) {
                  applyNewCommand(command, performance.now());
                  return;
              }
  
              queuedCommand = command;
              updateStatus();
          }
  
          function stopCommand() {
              queuedCommand = null;
              currentCommand = null;
              state = STATE_IDLE;
  
              motionStartAngle = currentAngle;
              motionTargetAngle = currentAngle;
              motionStartAt = 0;
              motionDurationMs = 0;
              holdStartAt = 0;
  
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
                  animationId = null;
              }
  
              lastFrameAt = null;
              updateStatus();
              renderMarker();
          }
  
          sendBtn.addEventListener('click', sendCommand);
          stopBtn.addEventListener('click', stopCommand);
          commandInput.addEventListener('keydown', function(event) {
              if (event.key === 'Enter') {
                  sendCommand();
              }
          });
  
          window.addEventListener('beforeunload', function() {
              if (animationId !== null) {
                  cancelAnimationFrame(animationId);
              }
          });
  
          stopCommand();
      </script>
  </body>
  </html>
  
- status: Command exited with code 0
- status: tokens used: {"input_tokens":429681,"cached_input_tokens":341376,"output_tokens":11862,"reasoning_output_tokens":1809}
- status: Codex exited with code 0
- file_change: update: aruco_rotate.html

</details>
