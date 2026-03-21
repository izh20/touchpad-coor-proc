# Finger Trajectory Analyzer

手指包数据轨迹可视化工具

## 功能概述

- 解析 HID IIC 手指包数据文件
- 实时以 130Hz 速度渲染手指轨迹
- 区分手指轨迹和大面积轨迹
- 支持轨迹回放控制

## 数据包格式

每包数据 **47字节 (0x2F)**，包含5个手指槽位：

| 字节位置 | 高4bit | 低4bit |
|---------|--------|--------|
| Byte 3 | 手指ID | 状态 |
| Byte 11 | 手指ID | 状态 |
| Byte 19 | 手指ID | 状态 |
| Byte 27 | 手指ID | 状态 |
| Byte 35 | 手指ID | 状态 |

**坐标格式**：每个槽位从 `slot+1` 开始：
- Byte slot+1, slot+2: X坐标 (小端)
- Byte slot+3, slot+4: Y坐标 (小端)

**状态定义**：

| 状态值 | 含义 | 显示样式 |
|--------|------|----------|
| 3 | 手指touch | 细线 + 小空心圆 |
| 2 | 大面积touch | 粗线 + 半透明填充 + 大实心圆 |
| 1 | 手指release | 清除该手指轨迹 |
| 0 | 大面积release | 清除该手指轨迹 |

## 使用方法

### 基本用法

```bash
# 运行实时轨迹查看器（自动计算坐标范围）
python3 finger_trajectory_realtime.py <数据文件.txt>

# 可选：显式指定坐标轴范围以设置 X/Y 分辨率
python3 finger_trajectory_realtime.py --xmin 0 --xmax 3685 --ymin 0 --ymax 2640 <数据文件.txt>

# 推荐（默认）
# 使用显式坐标范围以避免显示问题（推荐）
python3 finger_trajectory_realtime.py --xmin 0 --xmax 3685 --ymin 0 --ymax 2640 2.txt

# 快速自动模式（程序自动计算范围）
python3 finger_trajectory_realtime.py 2.txt
```

### 设置坐标轴分辨率

可以通过 `--xmin/--xmax/--ymin/--ymax` 四个可选参数显式指定数据坐标映射到显示区域时使用的坐标范围，从而手动控制 X、Y 轴的“分辨率”。当未指定时，程序会根据数据自动计算范围并在两端添加 10% 的边距。注意：若传入不合法的范围（如 `xmin >= xmax`），程序会忽略自定义值并回退到自动计算。

### 依赖安装

```bash
pip3 install pygame
```

## 操作说明

| 按键 | 功能 |
|------|------|
| `SPACE` | 播放 / 暂停 |
| `右箭头` | 逐帧前进 |
| `左箭头` | 逐帧后退 |
| `R` | 重置回第一帧 |
| `+` / `-` | 调整播放速度 (10-500 Hz) |
| `ESC` | 退出 |

### 新增：帧语义与按包显示

- 默认帧语义现为 `packet`（按包回放），程序会逐包显示：包的原始字节、scantime（u8,u8 与 u16）、finger_count、key_state，以及该包内的手指坐标。要按包回放请使用：

```bash
python3 finger_trajectory_realtime.py --frame-mode packet 2.txt
```

- 仍保留 `visible` 模式（以可见轨迹点为帧），用于连续运动可视化：

```bash
python3 finger_trajectory_realtime.py --frame-mode visible 2.txt
```

### Release 行为与轨迹清理

- 当检测到 `finger release`（状态=1）或 `large release`（状态=0）时，程序会清除该手指/大面积的历史轨迹，避免释放点影响后续轨迹的显示和判断。

### 键盘长按支持

- 对 `左右箭头` 已支持长按：按下后会先立即触发一次，短暂延迟后开始以较小间隔持续翻帧，便于快速浏览大量包数据。


## 界面元素

- **左上角**：当前帧 / 总帧数
- **右上角**：轨迹图例（显示每个手指/大面积的点数）
- **右下角**：状态颜色说明
  - 红色 = Finger Touch (状态3)
  - 蓝色 = Large Touch (状态2)
  - 绿色 = Finger Release (状态1)
  - 灰色 = Large Release (状态0)
- **左下角**：坐标范围和操作提示

## 显示样式

### 手指轨迹
- 细线 (2px)
- 小空心圆点 (8px)
- 标签显示 `F{id}`

### 大面积轨迹
- 粗线 (6px)
- 半透明填充区域
- 大实心圆点 (15px)
- 标签显示 `AREA{id}`

## 文件说明

| 文件 | 说明 |
|------|------|
| `finger_trajectory_realtime.py` | 实时轨迹查看器主程序 |
| `手指包数据.txt` | 示例数据文件 |
| `2.txt` | 示例数据文件 (多手指) |
| `3.txt` | 示例数据文件 (3手指轨迹) |
| `HP012项目数据上报格式.pdf` | 协议格式文档 |

## 常见问题

**Q: 为什么某些轨迹只显示一部分？**
A: 当检测到手指松键(status=1或status=0)时，该ID的轨迹会被清除，后续的点会作为新的触摸序列重新开始显示。

**Q: 如何区分手指和大面积？**
A: 根据状态判断。状态3=手指touch，状态2=大面积touch。

**Q: 播放速度太快/太慢？**
A: 使用 `+` 或 `-` 键调整速度，范围 10-500 Hz。

## 开发者说明（模块化）

项目已将解析器、模型与渲染器模块化到 `trajectory` 包中，位置：`trajectory/`。

- 解析器: `trajectory/parser.py`（类 `FingerDataParser`），可通过 `from trajectory import FingerDataParser` 导入。
- 模型: `trajectory/models.py`（包含 `FingerTrajectory`、`LargeTouchArea`）。
- 渲染器: `trajectory/renderer.py`（提供 `render_trajectories`、`render_legend` 辅助函数）。

示例：

```python
from trajectory import FingerDataParser, renderer

parser = FingerDataParser()
trajectories, packets = parser.process_csv_data('2.txt')
# 在 Pygame 环境中调用 renderer.render_trajectories(screen, trajectories, coord_to_screen)
```

原 `hid-iic-analyzer/hid-iic-analyzer/src` 下的旧实现已移至 `hid-iic-analyzer/hid-iic-analyzer/src_legacy/`，避免混淆。
