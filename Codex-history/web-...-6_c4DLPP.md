# 回転をweb上ではなくモーターで回すとしたらどんな仕様だと思う？ まとめ...

- Conversation ID: 6_c4DLPPf-cyUXrTzzWby
- Codex Session ID: 019f3d06-2821-7050-9984-8086b7331ad3
- Codex Session Workspace: /home/sato/robocon/AR_rotate
- Codex Session Version: workspace-c-v1
- Workspace: /home/sato/robocon/AR_rotate
- Updated: 2026-07-07T14:44:06.646Z

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

</details>
