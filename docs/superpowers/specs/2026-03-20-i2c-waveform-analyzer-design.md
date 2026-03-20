# Logic2 I2C Waveform Analyzer 设计文档

## 概述

开发一个 Electron + React UI 软件，实时显示 Logic2 抓取的 I2C 波形、协议解析和手指轨迹数据。

## 技术栈

- **Electron** - 跨平台桌面框架
- **React 18** - UI 框架
- **Logic2 自动化 API** - 实时获取 I2C 数据

## 界面布局

### 整体布局
- 顶部水平标签栏，三个标签页等宽分布
- 标签页切换显示不同内容

### 标签页结构

| 标签 | 内容 |
|------|------|
| 波形 | I2C 波形（SCL + SDA）实时显示 |
| 协议 | I2C 事务层级树状解析 |
| 轨迹 | 手指轨迹独立播放 |

## 视觉风格

### 深色主题配色
- 背景色: `#1e1e1e`
- 前景色: `#d4d4d4`
- 次级背景: `#252526`
- 边框色: `#3c3c3c`

### 波形配色 (Logic2 风格)
- SCL: 蓝色 `#569cd6`
- SDA: 橙色 `#ce9178`
- ACK: 绿色 `#6a9955`
- NACK: 红色 `#f14c4c`
- 地址: 黄色 `#dcdcaa`
- 数据: 浅蓝色 `#9cdcfe`

## 功能模块

### 1. 数据采集模块 (Main Process)

**职责**：通过 Logic2 API 获取实时数据

```
Logic2 Automation API → Main Process → IPC Bridge → Renderer
```

**接口**：
- `connectToLogic2()` - 建立连接
- `onI2CData(callback)` - 实时 I2C 数据回调
- `onFingerData(callback)` - 实时手指轨迹回调

### 2. 波形显示组件 (WaveformTab)

**职责**：实时渲染 I2C 波形

**功能**：
- SCL/SDA 双通道波形绘制
- 缩放控制 (鼠标滚轮/按钮)
- 平移控制 (拖拽/进度条)
- 时间轴游标

**交互**：
- 点击波形区间 → 高亮对应协议事务
- 滚轮 → 缩放
- 拖拽 → 平移

### 3. 协议解析组件 (ProtocolTab)

**职责**：显示 I2C 事务层级树

**显示格式**：
```
▼ START
  ▼ 地址: 0x50 (写)
    ▼ 数据: [0x01, 0x02, 0x03]
    ACK
  ▼ 地址: 0x50 (读)
    数据: [0xAA, 0xBB]
    NACK
  STOP
```

**功能**：
- 层级树状展开/折叠
- 点击事务 → 定位到波形对应位置
- 搜索/过滤

### 4. 手指轨迹组件 (TrajectoryTab)

**职责**：独立播放手指轨迹

**功能**：
- Pygame-style 轨迹渲染 (130Hz)
- 播放/暂停控制
- 逐帧前进/后退
- 速度调节 (10-500 Hz)

**显示样式**：
- 手指轨迹: 细线 (2px) + 空心圆
- 大面积轨迹: 粗线 (6px) + 实心圆
- 多指区分颜色

### 5. 数据缓存

使用 Ring Buffer 存储历史数据：
- 波形数据: 最近 10000 采样点
- 协议事务: 最近 1000 条
- 手指轨迹: 最近 1000 帧

## IPC 通信协议

```typescript
// Main → Renderer
interface I2CDataEvent {
  type: 'i2c';
  timestamp: number;
  scl: boolean;
  sda: boolean;
}

interface FingerDataEvent {
  type: 'finger';
  timestamp: number;
  frame: number;
  fingers: FingerSlot[];
}

interface ProtocolDecodeEvent {
  type: 'protocol';
  timestamp: number;
  address: number;
  direction: 'read' | 'write';
  data: number[];
  ack: boolean;
}
```

## 项目结构

```
i2c-analyzer/
├── package.json
├── electron/
│   ├── main.ts           # Electron 主进程
│   ├── preload.ts        # 预加载脚本
│   └── logic2-bridge.ts  # Logic2 API 桥接
├── src/
│   ├── App.tsx           # 主应用
│   ├── components/
│   │   ├── WaveformTab/
│   │   ├── ProtocolTab/
│   │   └── TrajectoryTab/
│   ├── hooks/
│   │   ├── useI2CData.ts
│   │   └── useFingerData.ts
│   └── styles/
│       └── theme.ts
└── docs/
    └── specs/
```

## 依赖

```json
{
  "electron": "^28.0.0",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "electron-builder": "^24.0.0"
}
```

## 后续步骤

1. 搭建 Electron + React 项目脚手架
2. 实现 Logic2 API 桥接
3. 实现波形渲染组件
4. 实现协议解析组件
5. 集成手指轨迹显示
