同じtoggleでも、一定時間以上経っていて、違うcommandがかなり安定しているなら再同期として採用

# 速度設定

> [!NOTE]- 速度設定
> 30Hzで最速を狙うなら、まずこのくらいが現実的。
> 
> ```
> const MOTOR_DEGREES_PER_SECOND = 180;const PULSE_HOLD_MS = 150;const COMMAND_END_HOLD_MS = 500;
> ```
> 
> このとき45°の回転時間は、
> 
> ```
> 45° / 180°/s = 0.25秒
> ```
> 
> 30Hzなら約7〜8フレーム。
> 
> これならまだ読める可能性がある。
> 
> さらに安定優先なら、
> 
> ```
> const MOTOR_DEGREES_PER_SECOND = 120;const PULSE_HOLD_MS = 150;const COMMAND_END_HOLD_MS = 600;
> ```
> 
> 45°に0.375秒、約11フレーム。  
> 最初の検証はこっちの方が安心。