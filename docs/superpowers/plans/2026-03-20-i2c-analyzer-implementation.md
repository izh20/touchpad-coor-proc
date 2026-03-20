# I2C Waveform Analyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an Electron + React desktop application that parses Logic2 .sal files and displays I2C waveforms, protocol decoding, and finger trajectory from HID finger packets embedded in I2C data.

**Architecture:** Electron app with main process handling .sal file parsing and IPC bridge to React renderer. Three tabbed views share a common data store. Finger packets are identified by header [0x2F, 0x00, 0x04] within I2C data payloads.

**Tech Stack:** Electron 28, React 18, Vite, TypeScript

---

## File Structure

```
i2c-analyzer/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── electron/
│   ├── main.ts              # Main process entry
│   ├── preload.ts           # Preload script (IPC bridge)
│   └── parser/
│       ├── sal-parser.ts    # .sal file parser
│       ├── i2c-decoder.ts  # I2C protocol decoder
│       └── finger-parser.ts # Finger packet parser (47 bytes)
├── src/
│   ├── main.tsx             # React entry
│   ├── App.tsx              # Main app with tabs
│   ├── components/
│   │   ├── TabBar.tsx
│   │   ├── WaveformTab/
│   │   │   ├── WaveformTab.tsx
│   │   │   ├── WaveformCanvas.tsx
│   │   │   └── WaveformControls.tsx
│   │   ├── ProtocolTab/
│   │   │   ├── ProtocolTab.tsx
│   │   │   └── ProtocolTree.tsx
│   │   └── TrajectoryTab/
│   │       ├── TrajectoryTab.tsx
│   │       └── TrajectoryCanvas.tsx
│   ├── hooks/
│   │   ├── useSalFile.ts    # Load .sal file via IPC
│   │   └── usePlayback.ts   # Playback controls
│   ├── store/
│   │   └── dataStore.ts     # Shared state (Zustand)
│   ├── styles/
│   │   └── theme.ts         # Dark theme constants
│   └── types/
│       └── index.ts         # TypeScript interfaces
└── tests/
    ├── finger-parser.test.ts
    └── i2c-decoder.test.ts
```

---

## Task 1: Project Scaffold

**Goal:** Set up Electron + React + Vite + TypeScript project

**Files:**
- Create: `package.json`
- Create: `vite.config.ts`
- Create: `tsconfig.json`
- Create: `index.html`
- Create: `electron/main.ts`
- Create: `electron/preload.ts`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "i2c-analyzer",
  "version": "1.0.0",
  "main": "dist-electron/main.js",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build && electron-builder",
    "preview": "vite preview"
  },
  "dependencies": {
    "electron": "^28.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.4.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "electron-builder": "^24.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vite-plugin-electron": "^0.28.0"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import electron from 'vite-plugin-electron'

export default defineConfig({
  plugins: [react(), electron()],
})
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
```

- [ ] **Step 3b: Create tsconfig.node.json for Vite/Electron build**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts", "electron/**/*.ts"]
}
```

- [ ] **Step 4: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>I2C Analyzer</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create electron/main.ts**

```typescript
import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import * as path from 'path'

let mainWindow: BrowserWindow | null = null

app.whenReady().then(() => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: { preload: path.join(__dirname, 'preload.js') }
  })

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }
})

ipcMain.handle('open-file-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    properties: ['openFile'],
    filters: [{ name: 'Saleae Files', extensions: ['sal'] }]
  })
  return result.filePaths[0] || null
})
```

- [ ] **Step 6: Create electron/preload.ts**

```typescript
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
  onFileData: (callback: (data: unknown) => void) => {
    ipcRenderer.on('file-data', (_, data) => callback(data))
  }
})
```

- [ ] **Step 7: Install dependencies**

Run: `npm install`

- [ ] **Step 8: Verify dev server starts**

Run: `npm run dev`
Expected: Vite dev server starts on port 5173

- [ ] **Step 9: Commit**

```bash
git add package.json vite.config.ts tsconfig.json index.html electron/
git commit -m "feat: scaffold Electron + React + Vite project"
```

---

## Task 2: Theme and Types

**Goal:** Define dark theme colors and TypeScript interfaces

**Files:**
- Create: `src/styles/theme.ts`
- Create: `src/types/index.ts`

- [ ] **Step 1: Create src/styles/theme.ts**

```typescript
export const theme = {
  colors: {
    background: '#1e1e1e',
    foreground: '#d4d4d4',
    secondaryBg: '#252526',
    border: '#3c3c3c',
    // Waveform colors (Logic2 style)
    scl: '#569cd6',
    sda: '#ce9178',
    ack: '#6a9955',
    nack: '#f14c4c',
    address: '#dcdcaa',
    data: '#9cdcfe',
  },
  spacing: { xs: 4, sm: 8, md: 16, lg: 24 },
} as const
```

- [ ] **Step 2: Create src/types/index.ts**

```typescript
export interface I2CWaveformSample {
  timestamp: number
  scl: boolean
  sda: boolean
}

export interface I2CTransaction {
  timestamp: number
  address: number
  direction: 'read' | 'write'
  data: number[]
  ack: boolean
  startTime: number
  endTime: number
}

export interface FingerSlot {
  fingerId: number
  status: number  // 0-3
  x: number
  y: number
  pressure: number
}

export interface FingerFrame {
  timestamp: number
  frameIndex: number
  slots: FingerSlot[]
}

export interface SalFileData {
  waveforms: I2CWaveformSample[]
  transactions: I2CTransaction[]
  fingerFrames: FingerFrame[]
}
```

- [ ] **Step 3: Commit**

```bash
git add src/styles/theme.ts src/types/index.ts
git commit -m "feat: add theme and TypeScript types"
```

---

## Task 3: Finger Packet Parser

**Goal:** Parse HID finger packets from I2C data payloads

**Files:**
- Create: `electron/parser/finger-parser.ts`
- Create: `tests/finger-parser.test.ts`

- [ ] **Step 1: Create tests/finger-parser.test.ts**

```typescript
import { parseFingerPacket, isFingerPacketHeader } from '../electron/parser/finger-parser'

describe('isFingerPacketHeader', () => {
  it('returns true for [0x2F, 0x00, 0x04]', () => {
    expect(isFingerPacketHeader([0x2F, 0x00, 0x04])).toBe(true)
  })

  it('returns false for other headers', () => {
    expect(isFingerPacketHeader([0x00, 0x00, 0x04])).toBe(false)
    expect(isFingerPacketHeader([0x2F, 0x01, 0x04])).toBe(false)
  })
})

describe('parseFingerPacket', () => {
  it('parses 47-byte finger packet correctly', () => {
    // Slot 0: fingerId=3, status=3, x=100, y=200, pressure=50
    const data = new Uint8Array([
      0x2F, 0x00, 0x04,  // Header
      0x33,              // Slot 0: fingerId=3, status=3
      0x64, 0x00,        // X = 100 (little endian)
      0xC8, 0x00,        // Y = 200 (little endian)
      0x00, 0x00,        // Reserved
      0x32,              // Pressure = 50
      // ... remaining slots zeros for simplicity
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // Slot 1
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // Slot 2
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // Slot 3
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  // Slot 4
    ])

    const slots = parseFingerPacket(data, 0)

    expect(slots[0].fingerId).toBe(3)
    expect(slots[0].status).toBe(3)
    expect(slots[0].x).toBe(100)
    expect(slots[0].y).toBe(200)
    expect(slots[0].pressure).toBe(50)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx jest tests/finger-parser.test.ts`
Expected: FAIL - "isFingerPacketHeader not defined"

- [ ] **Step 3: Create electron/parser/finger-parser.ts**

```typescript
import type { FingerSlot } from '../../src/types'

const FINGER_SLOT_OFFSETS = [3, 11, 19, 27, 35]

/**
 * Check if first 3 bytes indicate a finger packet header
 */
export function isFingerPacketHeader(data: Uint8Array): boolean {
  return data[0] === 0x2F && data[1] === 0x00 && data[2] === 0x04
}

/**
 * Parse a 47-byte finger packet starting at offset
 */
export function parseFingerPacket(data: Uint8Array, timestamp: number): FingerSlot[] {
  const slots: FingerSlot[] = []

  for (const offset of FINGER_SLOT_OFFSETS) {
    const statusByte = data[offset]
    const fingerId = (statusByte & 0xF0) >> 4
    const status = statusByte & 0x0F

    // Skip if no finger in this slot
    if (status === 0 || status === 1) {
      slots.push({ fingerId, status, x: 0, y: 0, pressure: 0 })
      continue
    }

    const x = data[offset + 1] | (data[offset + 2] << 8)
    const y = data[offset + 3] | (data[offset + 4] << 8)
    const pressure = data[offset + 7]

    slots.push({ fingerId, status, x, y, pressure })
  }

  return slots
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx jest tests/finger-parser.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add electron/parser/finger-parser.ts tests/finger-parser.test.ts
git commit -m "feat: add finger packet parser with header detection"
```

---

## Task 4: I2C Protocol Decoder

**Goal:** Decode I2C signal data into transactions

**Files:**
- Create: `electron/parser/i2c-decoder.ts`
- Create: `tests/i2c-decoder.test.ts`

- [ ] **Step 1: Create tests/i2c-decoder.test.ts**

```typescript
import { decodeI2CWaveforms } from '../electron/parser/i2c-decoder'
import type { I2CWaveformSample, I2CTransaction } from '../src/types'

describe('decodeI2CWaveforms', () => {
  it('detects START condition (SCL high, SDA falling)', () => {
    const samples: I2CWaveformSample[] = [
      { timestamp: 0, scl: true, sda: true },
      { timestamp: 1, scl: true, sda: false }, // START
      { timestamp: 2, scl: false, sda: false },
    ]

    const transactions = decodeI2CWaveforms(samples)
    expect(transactions.length).toBeGreaterThan(0)
    expect(transactions[0].startTime).toBe(1)
  })
})
```

- [ ] **Step 2: Create electron/parser/i2c-decoder.ts**

```typescript
import type { I2CWaveformSample, I2CTransaction } from '../../src/types'

/**
 * Decode I2C waveform samples into transactions
 *
 * I2C signaling:
 * - START: SDA falling while SCL is high
 * - STOP: SDA rising while SCL is high
 * - Data: Sampled on SCL rising edge (MSB first)
 */
export function decodeI2CWaveforms(samples: I2CWaveformSample[]): I2CTransaction[] {
  const transactions: I2CTransaction[] = []

  let inTransaction = false
  let currentAddress = 0
  let currentDirection: 'read' | 'write' = 'write'
  let currentData: number[] = []
  let startTime = 0
  let bitBuffer = 0
  let bitCount = 0
  let currentByte = 0

  for (let i = 1; i < samples.length; i++) {
    const prev = samples[i - 1]
    const curr = samples[i]

    // START: SDA falling edge while SCL is high
    if (prev.scl && curr.scl && prev.sda && !curr.sda) {
      if (inTransaction && currentData.length > 0) {
        transactions.push({
          timestamp: startTime,
          address: currentAddress,
          direction: currentDirection,
          data: [...currentData],
          ack: true,
          startTime,
          endTime: prev.timestamp
        })
      }
      inTransaction = true
      startTime = curr.timestamp
      currentData = []
      bitCount = 0
      bitBuffer = 0
      currentByte = 0
      continue
    }

    // STOP: SDA rising edge while SCL is high
    if (prev.scl && curr.scl && !prev.sda && curr.sda) {
      if (inTransaction && currentData.length > 0) {
        transactions.push({
          timestamp: startTime,
          address: currentAddress,
          direction: currentDirection,
          data: [...currentData],
          ack: true,
          startTime,
          endTime: curr.timestamp
        })
      }
      inTransaction = false
      currentData = []
      bitCount = 0
      continue
    }

    // Sample data bit on SCL rising edge
    if (!prev.scl && curr.scl && inTransaction) {
      bitBuffer = (bitBuffer << 1) | (curr.sda ? 1 : 0)
      bitCount++

      // Address phase: first 7 bits + R/W bit (8 bits total)
      if (bitCount <= 8) {
        currentByte = bitBuffer
        if (bitCount === 8) {
          currentAddress = currentByte >> 1
          currentDirection = (currentByte & 1) === 0 ? 'write' : 'read'
        }
      } else {
        // Data phase: 8 bits per byte
        if (bitCount % 8 === 0) {
          currentData.push(currentByte)
          currentByte = 0
          bitBuffer = 0
        } else {
          currentByte = (currentByte << 1) | (curr.sda ? 1 : 0)
        }
      }
    }
  }

  return transactions
}
```

- [ ] **Step 3: Run test to verify it passes**

Run: `npx jest tests/i2c-decoder.test.ts`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add electron/parser/i2c-decoder.ts tests/i2c-decoder.test.ts
git commit -m "feat: add I2C protocol decoder"
```

---

## Task 5: SAL File Parser

**Goal:** Parse Logic2 .sal files and extract I2C data

**Files:**
- Create: `electron/parser/sal-parser.ts`
- Modify: `electron/main.ts` (add IPC handler)
- Modify: `electron/preload.ts` (expose parse-sal-file)

**Note:** This task assumes .sal file format contains raw digital samples. The actual .sal format parsing may vary based on Logic2 version. The finger packet scanning approach below scans I2C data payloads for [0x2F, 0x00, 0x04] headers.

- [ ] **Step 1: Create electron/parser/sal-parser.ts**

```typescript
import * as fs from 'fs'
import type { SalFileData, I2CWaveformSample, I2CTransaction, FingerFrame } from '../../src/types'
import { isFingerPacketHeader, parseFingerPacket } from './finger-parser'
import { decodeI2CWaveforms } from './i2c-decoder'

/**
 * Parse .sal file and extract I2C waveforms, transactions, and finger frames
 *
 * .sal file format (simplified):
 * - Header with metadata
 * - Digital sample data as alternating bytes for different channels
 * - Each byte represents one sample (bit 0 = channel 0, bit 1 = channel 1, etc.)
 *
 * Finger packets are embedded in I2C transaction data payloads.
 * We first decode I2C transactions, then scan their payloads for finger packet headers.
 */
export function parseSalFile(filePath: string): SalFileData {
  const buffer = fs.readFileSync(filePath)
  const data = new Uint8Array(buffer)

  // Extract digital samples (simplified - assumes raw binary format)
  const waveforms: I2CWaveformSample[] = []

  // Sample rate from file header or default
  const SAMPLE_RATE = 40000000 // 40 MHz
  let sampleIndex = 0

  // Skip header (first 64 bytes typically)
  const HEADER_SIZE = 64
  for (let i = HEADER_SIZE; i < data.length; i++) {
    const byte = data[i]
    // Channel 0 = SCL, Channel 1 = SDA (example mapping)
    const scl = (byte & 0x01) !== 0
    const sda = (byte & 0x02) !== 0

    waveforms.push({
      timestamp: Math.floor((sampleIndex / SAMPLE_RATE) * 1000000), // microseconds
      scl,
      sda
    })
    sampleIndex++
  }

  // Decode I2C transactions from waveforms
  const transactions = decodeI2CWaveforms(waveforms)

  // Scan I2C transaction payloads for finger packet headers
  const fingerFrames: FingerFrame[] = []
  for (const tx of transactions) {
    // Scan data payload for finger packet header [0x2F, 0x00, 0x04]
    for (let i = 0; i < tx.data.length - 3; i++) {
      if (tx.data[i] === 0x2F && tx.data[i + 1] === 0x00 && tx.data[i + 2] === 0x04) {
        // Found finger packet header in I2C data payload
        // Extract 47 bytes starting from header
        if (i + 47 <= tx.data.length) {
          const payload = new Uint8Array(tx.data.slice(i, i + 47))
          const slots = parseFingerPacket(payload, tx.timestamp)

          fingerFrames.push({
            timestamp: tx.timestamp,
            frameIndex: fingerFrames.length,
            slots
          })
        }
        break // Move to next transaction after finding one header
      }
    }
  }

  return { waveforms, transactions, fingerFrames }
}
```

- [ ] **Step 2: Modify electron/preload.ts to expose parse-sal-file**

```typescript
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
  parseSalFile: (filePath: string) => ipcRenderer.invoke('parse-sal-file', filePath),
  onFileData: (callback: (data: unknown) => void) => {
    ipcRenderer.on('file-data', (_, data) => callback(data))
  }
})
```

- [ ] **Step 3: Modify electron/main.ts to add IPC handler**

```typescript
import { parseSalFile } from './parser/sal-parser'

// In app.whenReady(), add:
ipcMain.handle('parse-sal-file', async (_, filePath: string) => {
  try {
    const data = parseSalFile(filePath)
    return { success: true, data }
  } catch (error) {
    return { success: false, error: String(error) }
  }
})
```

- [ ] **Step 4: Commit**

```bash
git add electron/parser/sal-parser.ts electron/main.ts electron/preload.ts
git commit -m "feat: add SAL file parser with I2C decoding"
```

---

## Task 5a: Data Store

**Goal:** Shared state management with Zustand

**Files:**
- Create: `src/store/dataStore.ts`

- [ ] **Step 1: Create src/store/dataStore.ts**

```typescript
import { create } from 'zustand'
import type { SalFileData, I2CWaveformSample, I2CTransaction, FingerFrame } from '../types'

type Tab = 'waveform' | 'protocol' | 'trajectory'

interface DataState {
  // File state
  filePath: string | null
  waveformData: I2CWaveformSample[]
  transactions: I2CTransaction[]
  fingerFrames: FingerFrame[]

  // Playback state
  currentFrame: number
  isPlaying: boolean
  playbackSpeed: number

  // UI state
  currentTab: Tab
  zoom: number  // Waveform zoom level

  // Actions
  setFileData: (data: SalFileData) => void
  setCurrentFrame: (frame: number) => void
  setIsPlaying: (playing: boolean) => void
  setPlaybackSpeed: (speed: number) => void
  setCurrentTab: (tab: Tab) => void
  setZoom: (zoom: number) => void
}

export const useDataStore = create<DataState>((set) => ({
  filePath: null,
  waveformData: [],
  transactions: [],
  fingerFrames: [],
  currentFrame: 0,
  isPlaying: false,
  playbackSpeed: 130,
  currentTab: 'waveform',
  zoom: 1,

  setFileData: (data) => set({
    waveformData: data.waveforms,
    transactions: data.transactions,
    fingerFrames: data.fingerFrames,
    currentFrame: 0,
    isPlaying: false
  }),

  setCurrentFrame: (frame) => set({ currentFrame: frame }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),
  setCurrentTab: (tab) => set({ currentTab: tab }),
  setZoom: (zoom) => set({ zoom }),
}))
```

- [ ] **Step 2: Commit**

```bash
git add src/store/dataStore.ts
git commit -m "feat: add Zustand data store with tab state"
```

---

## Task 5b: Playback Hook

**Goal:** Implement playback timing logic for trajectory animation

**Files:**
- Create: `src/hooks/usePlayback.ts`

- [ ] **Step 1: Create src/hooks/usePlayback.ts**

```typescript
import { useEffect, useRef } from 'react'
import { useDataStore } from '../store/dataStore'

/**
 * Hook to manage trajectory playback timing
 * Advances frames at the configured playback speed (Hz)
 */
export function usePlayback() {
  const isPlaying = useDataStore((s) => s.isPlaying)
  const playbackSpeed = useDataStore((s) => s.playbackSpeed)
  const fingerFrames = useDataStore((s) => s.fingerFrames)
  const currentFrame = useDataStore((s) => s.currentFrame)
  const setCurrentFrame = useDataStore((s) => s.setCurrentFrame)

  const intervalRef = useRef<number | null>(null)

  useEffect(() => {
    if (isPlaying) {
      // Calculate interval from playback speed (Hz = frames per second)
      const intervalMs = 1000 / playbackSpeed

      intervalRef.current = window.setInterval(() => {
        setCurrentFrame((currentFrame + 1) % fingerFrames.length)
      }, intervalMs)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isPlaying, playbackSpeed, currentFrame, fingerFrames.length, setCurrentFrame])
}
```

- [ ] **Step 2: Commit**

```bash
git add src/hooks/usePlayback.ts
git commit -m "feat: add playback timing hook"
```

---

## Task 6: TabBar Component

**Goal:** Horizontal tab bar for switching between views

**Files:**
- Create: `src/components/TabBar.tsx`

- [ ] **Step 1: Create src/components/TabBar.tsx**

```typescript
import { useDataStore } from '../store/dataStore'

type Tab = 'waveform' | 'protocol' | 'trajectory'

interface Props {
  currentTab: Tab
  onTabChange: (tab: Tab) => void
}

export function TabBar({ currentTab, onTabChange }: Props) {
  const tabs: { id: Tab; label: string }[] = [
    { id: 'waveform', label: '波形' },
    { id: 'protocol', label: '协议' },
    { id: 'trajectory', label: '轨迹' },
  ]

  return (
    <div className="tab-bar">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab ${currentTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/TabBar.tsx
git commit -m "feat: add TabBar component"
```

---

## Task 7: WaveformTab Component

**Goal:** Display I2C waveform with zoom/pan controls

**Files:**
- Create: `src/components/WaveformTab/WaveformTab.tsx`
- Create: `src/components/WaveformTab/WaveformCanvas.tsx`
- Create: `src/components/WaveformTab/WaveformControls.tsx`

- [ ] **Step 1: Create WaveformCanvas.tsx**

```typescript
import { useRef, useEffect } from 'react'
import { useDataStore } from '../../store/dataStore'
import { theme } from '../../styles/theme'

export function WaveformCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const waveformData = useDataStore((s) => s.waveformData)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')!
    const { width, height } = canvas

    // Clear
    ctx.fillStyle = theme.colors.background
    ctx.fillRect(0, 0, width, height)

    // Draw SCL (blue) - simplified, just show samples
    ctx.strokeStyle = theme.colors.scl
    ctx.beginPath()
    ctx.moveTo(0, height / 2)

    waveformData.forEach((sample, i) => {
      const x = (i / waveformData.length) * width
      const y = sample.scl ? height * 0.25 : height * 0.75
      ctx.lineTo(x, y)
    })

    ctx.stroke()

    // Draw SDA (orange) - simplified
    ctx.strokeStyle = theme.colors.sda
    ctx.beginPath()
    ctx.moveTo(0, height * 0.6)

    waveformData.forEach((sample, i) => {
      const x = (i / waveformData.length) * width
      const y = sample.sda ? height * 0.45 : height * 0.75
      ctx.lineTo(x, y)
    })

    ctx.stroke()
  }, [waveformData])

  return <canvas ref={canvasRef} width={800} height={200} />
}
```

- [ ] **Step 2: Create WaveformControls.tsx**

```typescript
import { useDataStore } from '../../store/dataStore'

export function WaveformControls() {
  const zoom = useDataStore((s) => s.zoom)
  const setZoom = useDataStore((s) => s.setZoom)

  return (
    <div className="waveform-controls">
      <button onClick={() => setZoom(zoom * 1.2)}>+</button>
      <span>{Math.round(zoom * 100)}%</span>
      <button onClick={() => setZoom(zoom / 1.2)}>-</button>
    </div>
  )
}
```

- [ ] **Step 3: Create WaveformTab.tsx**

```typescript
import { WaveformCanvas } from './WaveformCanvas'
import { WaveformControls } from './WaveformControls'

export function WaveformTab() {
  return (
    <div className="waveform-tab">
      <WaveformControls />
      <WaveformCanvas />
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add src/components/WaveformTab/
git commit -m "feat: add WaveformTab with canvas and controls"
```

---

## Task 8: ProtocolTab Component

**Goal:** Display I2C transactions as hierarchical tree

**Files:**
- Create: `src/components/ProtocolTab/ProtocolTab.tsx`
- Create: `src/components/ProtocolTab/ProtocolTree.tsx`

- [ ] **Step 1: Create ProtocolTree.tsx**

```typescript
import type { I2CTransaction } from '../../types'

interface Props {
  transactions: I2CTransaction[]
  onSelect: (tx: I2CTransaction) => void
}

export function ProtocolTree({ transactions, onSelect }: Props) {
  return (
    <div className="protocol-tree">
      {transactions.map((tx, i) => (
        <div key={i} className="transaction" onClick={() => onSelect(tx)}>
          <div className="transaction-header">
            <span className="address">0x{tx.address.toString(16)}</span>
            <span className="direction">{tx.direction === 'read' ? '读' : '写'}</span>
            <span className="ack" style={{ color: tx.ack ? '#6a9955' : '#f14c4c' }}>
              {tx.ack ? 'ACK' : 'NACK'}
            </span>
          </div>
          <div className="transaction-data">
            数据: [{tx.data.map((b) => '0x' + b.toString(16)).join(', ')}]
          </div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Create ProtocolTab.tsx**

```typescript
import { useDataStore } from '../../store/dataStore'
import { ProtocolTree } from './ProtocolTree'

export function ProtocolTab() {
  const transactions = useDataStore((s) => s.transactions)
  const setCurrentFrame = useDataStore((s) => s.setCurrentFrame)

  return (
    <div className="protocol-tab">
      <ProtocolTree
        transactions={transactions}
        onSelect={(tx) => {
          // Navigate to timestamp
          setCurrentFrame(tx.timestamp)
        }}
      />
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/ProtocolTab/
git commit -m "feat: add ProtocolTab with hierarchical tree view"
```

---

## Task 9: TrajectoryTab Component

**Goal:** Display finger trajectory with playback controls

**Files:**
- Create: `src/components/TrajectoryTab/TrajectoryTab.tsx`
- Create: `src/components/TrajectoryTab/TrajectoryCanvas.tsx`

- [ ] **Step 1: Create TrajectoryCanvas.tsx**

```typescript
import { useRef, useEffect } from 'react'
import { useDataStore } from '../../store/dataStore'

const COLORS = ['#569cd6', '#ce9178', '#6a9955', '#dcdcaa', '#9cdcfe']

export function TrajectoryCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const fingerFrames = useDataStore((s) => s.fingerFrames)
  const currentFrame = useDataStore((s) => s.currentFrame)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || fingerFrames.length === 0) return

    const ctx = canvas.getContext('2d')!
    const { width, height } = canvas

    // Clear
    ctx.fillStyle = '#1e1e1e'
    ctx.fillRect(0, 0, width, height)

    const frame = fingerFrames[currentFrame]
    if (!frame) return

    // Draw each slot
    frame.slots.forEach((slot, i) => {
      if (slot.status === 0 || slot.status === 1) return // Released

      const x = (slot.x / 4096) * width // Normalize to canvas
      const y = (slot.y / 4096) * height

      ctx.fillStyle = COLORS[i % COLORS.length]

      if (slot.status === 3) {
        // Finger touch - small circle
        ctx.beginPath()
        ctx.arc(x, y, 4, 0, Math.PI * 2)
        ctx.stroke()
      } else if (slot.status === 2) {
        // Large touch - filled circle
        ctx.beginPath()
        ctx.arc(x, y, 8, 0, Math.PI * 2)
        ctx.fill()
      }
    })
  }, [fingerFrames, currentFrame])

  return <canvas ref={canvasRef} width={400} height={400} />
}
```

- [ ] **Step 2: Create TrajectoryTab.tsx**

```typescript
import { useDataStore } from '../../store/dataStore'
import { usePlayback } from '../../hooks/usePlayback'
import { TrajectoryCanvas } from './TrajectoryCanvas'

export function TrajectoryTab() {
  const fingerFrames = useDataStore((s) => s.fingerFrames)
  const currentFrame = useDataStore((s) => s.currentFrame)
  const isPlaying = useDataStore((s) => s.isPlaying)
  const playbackSpeed = useDataStore((s) => s.playbackSpeed)
  const setCurrentFrame = useDataStore((s) => s.setCurrentFrame)
  const setIsPlaying = useDataStore((s) => s.setIsPlaying)
  const setPlaybackSpeed = useDataStore((s) => s.setPlaybackSpeed)

  // Start playback loop
  usePlayback()

  return (
    <div className="trajectory-tab">
      <div className="controls">
        <button onClick={() => setCurrentFrame(Math.max(0, currentFrame - 1))}>◀</button>
        <button onClick={() => setIsPlaying(!isPlaying)}>
          {isPlaying ? '暂停' : '播放'}
        </button>
        <button onClick={() => setCurrentFrame(Math.min(fingerFrames.length - 1, currentFrame + 1))}>▶</button>
        <span>帧: {currentFrame + 1} / {fingerFrames.length}</span>
        <input
          type="range"
          min="10"
          max="500"
          value={playbackSpeed}
          onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
        />
        <span>{playbackSpeed} Hz</span>
      </div>
      <TrajectoryCanvas />
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/TrajectoryTab/
git commit -m "feat: add TrajectoryTab with playback controls"
```

---

## Task 10: App Integration

**Goal:** Wire up App.tsx with tabs and file loading

**Files:**
- Modify: `src/App.tsx`
- Create: `src/hooks/useSalFile.ts`

- [ ] **Step 1: Create src/hooks/useSalFile.ts**

```typescript
import { useDataStore } from '../store/dataStore'
import type { SalFileData } from '../types'

declare global {
  interface Window {
    electronAPI: {
      openFileDialog: () => Promise<string | null>
      parseSalFile: (filePath: string) => Promise<{ success: boolean; data?: SalFileData; error?: string }>
    }
  }
}

export function useSalFile() {
  const setFileData = useDataStore((s) => s.setFileData)

  const openFile = async () => {
    const filePath = await window.electronAPI.openFileDialog()
    if (!filePath) return

    // Parse file via IPC (runs in main process)
    const result = await window.electronAPI.parseSalFile(filePath)
    if (result.success && result.data) {
      setFileData(result.data)
    } else {
      console.error('Failed to parse file:', result.error)
    }
  }

  return { openFile }
}
```

- [ ] **Step 2: Modify src/App.tsx**

```typescript
import { useState } from 'react'
import { TabBar } from './components/TabBar'
import { WaveformTab } from './components/WaveformTab/WaveformTab'
import { ProtocolTab } from './components/ProtocolTab/ProtocolTab'
import { TrajectoryTab } from './components/TrajectoryTab/TrajectoryTab'
import { useSalFile } from './hooks/useSalFile'
import { theme } from './styles/theme'

type Tab = 'waveform' | 'protocol' | 'trajectory'

function App() {
  const [currentTab, setCurrentTab] = useState<Tab>('waveform')
  const { openFile } = useSalFile()

  return (
    <div className="app" style={{ background: theme.colors.background, color: theme.colors.foreground }}>
      <div className="toolbar">
        <button onClick={openFile}>打开 .sal 文件</button>
      </div>
      <TabBar currentTab={currentTab} onTabChange={setCurrentTab} />
      <div className="content">
        {currentTab === 'waveform' && <WaveformTab />}
        {currentTab === 'protocol' && <ProtocolTab />}
        {currentTab === 'trajectory' && <TrajectoryTab />}
      </div>
    </div>
  )
}

export default App
```

- [ ] **Step 3: Add basic CSS**

Create `src/styles/global.css`:
```css
.app { display: flex; flex-direction: column; height: 100vh; }
.toolbar { padding: 8px; border-bottom: 1px solid #3c3c3c; }
.content { flex: 1; overflow: auto; }
.tab-bar { display: flex; border-bottom: 1px solid #3c3c3c; }
.tab { padding: 8px 16px; border: none; background: transparent; color: #d4d4d4; cursor: pointer; }
.tab.active { border-bottom: 2px solid #569cd6; }
```

- [ ] **Step 4: Commit**

```bash
git add src/App.tsx src/hooks/useSalFile.ts src/styles/global.css
git commit -m "feat: integrate App with tabs and file loading"
```

---

## Task 11: Build and Test

**Goal:** Verify application builds and runs

- [ ] **Step 1: Run production build**

Run: `npm run build`
Expected: Build completes without errors

- [ ] **Step 2: Test with sample .sal file**

Open `Session 2.sal` and verify data loads

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: complete I2C analyzer application"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Project scaffold (Electron + React + Vite) |
| 2 | Theme and TypeScript types |
| 3 | Finger packet parser |
| 4 | SAL file parser |
| 5 | Zustand data store |
| 6 | TabBar component |
| 7 | WaveformTab component |
| 8 | ProtocolTab component |
| 9 | TrajectoryTab component |
| 10 | App integration |
| 11 | Build and test |
