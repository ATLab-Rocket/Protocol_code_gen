# Rocket Protocol Generator — Project Handoff

## 1. Project Goal

我要設計一套火箭飛控（STM32）與 Ground Station 之間的通訊協定。

核心目標：

> 只維護一份 `protocol.yaml`，作為 Protocol 的唯一 Source of Truth。

透過：

```text
protocol.yaml
      ↓
generate_protocol.py
      ↓
┌───────────────┬────────────────┐
│ Rocket / STM32│ Ground Station │
└───────────────┴────────────────┘
```

自動產生兩邊需要的 Protocol Code。

修改 Protocol 時，只修改 `protocol.yaml`，然後重新執行 Generator。

---

# 2. Current Design Philosophy

人負責描述：

> 「Protocol 是什麼」

Generator 負責決定：

> 「Protocol 如何實作」

不要讓 Rocket 與 Ground Station 各自維護 Protocol。

---

# 3. Current MVP Scope

第一版只需要支援：

### Telemetry

- IMU

### Command

- OPEN_VALVE

### Data types

```text
uint8
int16
uint16
int32
uint32
float32
```

第一版暫時不要：

- CRC
- ACK
- sequence number
- timestamp
- scale
- unit
- legal_states
- variable-length payload
- fragmentation

先讓最基本的：

```text
YAML
→ Protocol Model
→ encode
→ bytes
→ decode
```

完整跑通。

---

# 4. Current protocol.yaml

目前設計：

```yaml
protocol:
  version: 1
  endian: little

telemetry:

  IMU:
    packet_id: 0x01
    rate_hz: 50

    data:
      - name: a_x
        type: int16_t

      - name: a_y
        type: int16_t

      - name: a_z
        type: int16_t
      
      - name: roll
        type: int16_t

      - name: pitch
        type: int16_t

      - name: yaw
        type: int16_t


commands:

  OPEN_VALVE:
    command_id: 0x10

    arguments:
      - name: valve_id
        type: uint8
```

---

# 5. Packet Frame

第一版統一使用：

```text
┌────────────┬────────────┬──────────────┐
│ Packet ID  │   Length   │    Payload   │
│  1 byte    │   1 byte   │    N bytes   │
└────────────┴────────────┴──────────────┘
```

其中：

- `packet_id`: 1 byte
- `length`: Payload 長度，不包含 header
- `payload`: 根據 Protocol 定義

---

# 6. IMU Example

IMU：

```yaml
packet_id: 0x01
```

Payload：

```text
a_x       int16_t    offset 0    size 2
a_y       int16_t    offset 2    size 2
a_z       int16_t    offset 4    size 2
roll      int16_t    offset 6    size 2
pitch     int16_t    offset 8    size 2
yaw       int16_t    offset 10   size 2
```

Payload size：

```text
12 bytes
```

因此封包：

```text
01 0C [a_x 2 bytes] [a_y 2 bytes] [a_z 2 bytes] [roll 2 bytes] [pitch 2 bytes] [yaw 2 bytes]
```

總長：

```text
14 bytes
```

---

# 7. Endianness

Protocol 使用：

```yaml
endian: little
```

所有多 byte integer / float 都使用 little endian。

例如：

```text
uint16 0x1234
→ 34 12
```

```text
uint32 0x12345678
→ 78 56 34 12
```

C 與 Ground Station 必須使用相同規則。

---

# 8. Protocol Model

下一步要設計 Generator 的內部資料模型。

預計至少需要：

```text
Protocol
Packet
Field
Command
Argument
DataType
```

概念：

```text
Protocol
├── version
├── endian
├── telemetry
│   └── Packet
│       ├── packet_id
│       ├── rate_hz
│       └── fields
│           └── Field
│               ├── name
│               ├── type
│               ├── size
│               └── offset
│
└── commands
    └── Command
        ├── command_id
        └── arguments
            └── Argument
```

---

# 9. Important Design Rule

不要直接：

```text
YAML → C code
```

而要：

```text
YAML
 ↓
Parser
 ↓
Protocol Model
 ↓
Validation
 ↓
Generators
 ↓
C / Python / other outputs
```

Protocol Model 是 Generator 的核心。

---

# 10. First Milestone

第一個 Milestone 不要生成 C code。

先完成：

```bash
python generate_protocol.py protocol.yaml
```

輸出類似：

```text
Protocol version: 1
Endian: little

Telemetry:

IMU
  Packet ID: 0x01
  Rate: 50 Hz

  roll
    type: float32
    offset: 0
    size: 4

  pitch
    type: float32
    offset: 4
    size: 4

  yaw
    type: float32
    offset: 8
    size: 4

  payload size: 12 bytes
```

這代表：

```text
YAML
 ↓
Parser
 ↓
Protocol Model
```

已經正常。

---

# 11. Development Order

請按照以下順序實作：

## Phase 1 — Protocol Model

設計：

```text
DataType
Field
Packet
Argument
Command
Protocol
```

---

## Phase 2 — YAML Parser

將：

```text
protocol.yaml
```

轉成：

```text
Protocol object
```

---

## Phase 3 — Validation

至少檢查：

- duplicate packet ID
- duplicate command ID
- unsupported data type
- duplicate field name
- invalid packet definition
- invalid command definition

---

## Phase 4 — Packet Layout

自動計算：

```text
field size
field offset
payload size
packet size
```

---

## Phase 5 — C Generator

產生 STM32：

```c
typedef struct {
    float roll;
    float pitch;
    float yaw;
} IMU_Packet_t;
```

以及 packet IDs。

---

## Phase 6 — Python Generator

產生 Ground Station：

- packet definitions
- telemetry decoder
- command encoder

Ground Station 不需要：

- encode telemetry
- decode command

---

## Phase 7 — Serialization

實作：

```text
Rocket / C:
  encode telemetry
  decode command

Ground Station / Python:
  decode telemetry
  encode command
```

並遵守：

```text
little endian
```

---

## Phase 8 — Cross-platform Test

測試：

```text
Python encode command
      ↓
raw bytes
      ↓
C decode command
```

以及：

```text
C encode telemetry
      ↓
raw bytes
      ↓
Python decode telemetry
```

兩邊結果必須一致。

---

# 12. Important Constraint

第一版不要過度設計。

優先驗證：

> 一份 YAML 能否可靠地生成兩邊一致的 Protocol implementation。

等 MVP 完成後，再逐步加入：

```text
scale
unit
CRC
ACK
timestamp
sequence number
legal_states
protocol version
documentation generation
CI
```

---

# 13. Current Next Task

目前最優先：

> 擴充 cross-platform test，加入更多 data type 的 encode/decode 驗證。

Rocket 端 C generator 已整理為：

```text
generated/rocket/
├── protocol.h   # constants, typedefs, function prototypes
└── protocol.c   # encode/decode implementation and internal helpers
```

目前 cross-platform test 已驗證：

```text
Python encode command → C decode command
C encode telemetry → Python decode telemetry
```

下一步可以用額外測試 protocol 覆蓋：

```text
uint8
int16
uint16
int32
uint32
float32
```

---

# 14. Expected Project Structure

可以朝以下方向：

```text
project/
│
├── protocol.yaml
├── generate_protocol.py
├── PROTOCOL_DESIGN.md
│
├── protocol/
│   ├── model.py
│   ├── parser.py
│   ├── validator.py
│   └── types.py
│
├── generators/
│   ├── c_generator.py
│   └── python_generator.py
│
├── generated/
│   ├── rocket/
│   └── ground/
│
└── tests/
```

這個結構可以依實際程式碼狀況調整，不需要現在一次建立全部。

---

# 15. Current Commands

## 建立 / 使用 Python 環境

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## 檢查 YAML → Protocol Model

```powershell
.\.venv\Scripts\python generate_protocol.py protocol.yaml
```

## 產生 Rocket / STM32 C code

產生：

```text
generated\rocket\protocol.h
generated\rocket\protocol.c
```

```powershell
.\.venv\Scripts\python generate_protocol.py protocol.yaml --c-output-dir generated\rocket
```

`protocol.h` 包含：

```text
constants
typedefs
function prototypes
```

`protocol.c` 包含：

```text
encode/decode implementation
internal little-endian helpers
```

## 產生 Ground Station Python code

```powershell
.\.venv\Scripts\python generate_protocol.py protocol.yaml --python-output generated\ground\protocol.py
```

## 跑測試

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

目前測試包含：

- model tests
- parser tests
- validator tests
- C generator tests
- Python generator tests
- cross-platform tests

Cross-platform tests 會使用 `gcc` 編譯小型 C 測試程式，驗證：

```text
Python encode command → C decode command
C encode telemetry → Python decode telemetry
```

---

# 16. Current Progress

目前已完成：

- Phase 1 — Protocol Model
- Phase 2 — YAML Parser
- Phase 3 — Validation
- Phase 4 — Packet Layout
- Phase 5 — C Generator MVP
- Phase 6 — Python Generator MVP
- Phase 7 — Serialization MVP
- Phase 8 — Cross-platform Test MVP

目前已產生：

```text
generated/rocket/protocol.h
generated/rocket/protocol.c
generated/ground/protocol.py
```

目前 Rocket / C 端能力：

```text
encode telemetry
decode command
```

目前 Ground Station / Python 端能力：

```text
decode telemetry
encode command
```

目前測試狀態：

```text
Ran 22 tests
OK
```

下一步：

```text
Cross-platform tests:
  add coverage for all MVP scalar types
```

---

# 17. Coding Style / Learning Preference
希望採用：

1. 先解釋設計
2. 確認目前要解決的問題
3. 實作一小部分
4. 測試
5. 再進下一步

回答時優先給：

- 核心概念
- 必要程式碼
- 測試方法

不要一次給很長的教學文章。
