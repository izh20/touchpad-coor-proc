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
# 运行实时轨迹查看器
python3 finger_trajectory_realtime.py <数据文件.txt>

# 示例
python3 finger_trajectory_realtime.py 手指包数据.txt
python3 finger_trajectory_realtime.py 2.txt
python3 finger_trajectory_realtime.py 3.txt
```

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
