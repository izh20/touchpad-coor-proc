# HP012 项目 HID IIC 数据上报格式（更新）

## 概述

本文档说明工程中实际使用的 HID IIC 手指包格式（与当前代码实现对齐）。每包固定为 47 字节（十进制），报文起始标识为 `0x2F`。

此格式用于解析并可视化触控板的手指/大面积触摸事件。

---

## 基本包结构

- 包长度: 47 字节
- 报告 ID: `0x2F`（第一字节用于快速同步包起始）
# 包长度: 47 字节
# 报文起始同步头: `0x2F, 0x00, 0x04`（其中第三字节 `0x04` 为实际的 report id）
# 注意：解析器同时对单字节 `0x2F` 同步保有向后兼容性，但样本中包头通常为三字节序列。
- 5 个手指槽位的起始偏移（0-based）：`[3, 11, 19, 27, 35]`

每个槽位包含状态/ID 字节和随后的坐标字段（详见下文）。另外，包尾的若干字节用于携带包级元数据（如 scantime、finger_count、key_state），当前实现约定使用固定偏移读取这些字段（见“包级元数据”部分）。

---

## 槽位内部定义

槽位起始字节（例如第一个槽位为 byte 3）包含状态/ID 信息：

- 字节含义（以槽位起始位置为基准）：
   - byte 0 (槽位起始): 高 4 bit = `finger_id`，低 4 bit = `status`
   - byte 1: pressure / 保留（可选）
   - byte 2: X 低 8 位
   - byte 3: X 高位（部分高位或按协议位扩展）
   - byte 4: Y 低 8 位
   - byte 5: Y 高位
   - byte 6..7: 保留

（注意：不同设备文档中有不同排列，本仓库代码以 47 字节包、槽位偏移 `[3,11,19,27,35]` 为准；具体坐标合并请参考“坐标拼接”段落。）

### 状态值（低 4 bit）

- 3: Finger Touch（手指按下） — 渲染为细线 + 空心圆
- 2: Large Area Touch（大面积按下） — 渲染为粗线 + 实心圆（并填充轨迹区域）
- 1: Finger Release（手指抬起） — 清除该 finger_id 的历史轨迹
- 0: Large Area Release（大面积抬起） — 清除该 finger_id 的历史轨迹

---

## 坐标拼接（小端）

坐标按小端合并，例如：

```
X = low_byte | (high_byte << 8)
Y = low_byte | (high_byte << 8)
```

代码中会把合并得到的 16-bit 值直接作为数据坐标用于渲染与统计。

---

## 包级元数据（scantime / finger_count / key_state）

在实际样本与工程实现中，我们约定在包的末尾固定位置读取包级元数据：

- byte[43] (0-based) : scantime low（u8）
- byte[44] (0-based) : scantime high（u8）
- byte[45] (0-based) : finger_count（u8）
- byte[46] (0-based) : key_state（u8，1 表示 Key DOWN）

scantime 解释为小端 16-bit 值：`scantime_u16 = low | (high << 8)`。UI 会同时展示 raw bytes（hex）与合并后的十进制 scantime 以便核对。

---

## 输入文件格式

- 本仓库示例和分析工具支持的输入为纯文本 CSV（或按行十六进制值）格式：每行包含多个 CSV 字段，第四个字段（index=3）为单字节数据值（十六进制或十进制），解析器会读取该列并将其看作按顺序的字节流，再按 47 字节切分为包。

示例（CSV 行示意）：

```
0.000,info,info,0x2F,..
0.008,info,info,0x00,..
...
```

此外也接受纯十六进制字节流（每行一个字节）形式，解析器会进行容错性的同步（查找 `0x2F` 作为包起始）。

---

## 使用示例（命令行）

推荐使用实时查看器：

```bash
python3 finger_trajectory_realtime.py --xmin 0 --xmax 3685 --ymin 0 --ymax 2640 2.txt
```

说明：
- 默认 `--frame-mode` 为 `packet`（按包回放并严格对应原始数据），可显式使用 `--frame-mode visible` 切换到基于可见点的连续可视化模式。
- 在 `packet` 模式下，左右箭头支持长按连续翻包，UI 会显示该包的原始十六进制字节、scantime（u8,u8 & u16）、finger_count 与 key_state，同时绘制属于该包的坐标点及历史轨迹（release 会清理历史）。

---

## 解析/代码对应

关键实现位于 `trajectory/parser.py` 和 `finger_trajectory_realtime.py`：

```python
PACKET_SIZE = 47
FINGER_REPORT_ID = 0x2F
FINGER_SLOTS = [3,11,19,27,35]

# 解析包尾 scantime/finger_count/key_state
low = pkt[43]
high = pkt[44]
finger_cnt = pkt[45]
key_state = pkt[46]
```

---

## 变更记录 / 注意事项

- 本文件已更新为与代码实现一致：使用 47 字节包与 0x2F 报文起始。若接入新设备或数据源，请先确认包长与起始标识，必要时调整 `trajectory/parser.py` 中的 `PACKET_SIZE` 和 `FINGER_REPORT_ID`。
- 仓库中已移除旧的静态绘图脚本（`finger_trajectory.py`、`finger_trajectory_gui.py`），请使用 `finger_trajectory_realtime.py` 进行交互式验证与回放。

---

如需我把本文件也同步到项目的其它 README 或生成变更日志，请告诉我要包含的摘要。 
