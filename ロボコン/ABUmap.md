[PR](https://github.com/tutrobo/abu2026-ros2-ws/pull/798)
feat/dog3-abu-field/sto

坂道に制限を入れる
確認したら入ってた
```
このブランチだと、ランプの姿勢制限はすでに abu2026_obstacle_map_r1.yaml に入っています。

abu2026_obstacle_map_r1.yaml (line 37) に:

yaml

`angle_constraints: # Ramp - bounds: min: [8.3, 4.525] max: [11.8, 6.025] centers: [0.0, 180.0] tolerance: 5.0`

があり、さらに Ramp の sampling_region (line 100) にも:

yaml

`theta_centers: [0.0, 180.0] theta_tolerance: 5.0`

があります。
```