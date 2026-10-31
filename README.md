# Telemetry Protocol Generator

一套用於**火箭飛控（Rocket / STM32）**與**地面站（Ground Station）**之間的通訊協定程式碼產生器（Code Generator）。

核心設計理念是以單一 `protocol.yaml` 作為 **Single Source of Truth（唯一真實來源）**，自動解析、驗證並產生飛控端與地面站端的協定封包定義與序列化（encode / decode）程式碼，確保雙邊實作完全一致。

---

## 架構與工作流程

```text
protocol.yaml
      │
      ▼
Parser & Validator (protocol/)
      │
      ▼
Protocol Model
      │
      ├──► Rocket C Generator        ──► generated/rocket/{protocol.h, protocol.c}
      ├──► Ground C Generator        ──► generated/ground/{protocol.h, protocol.c}
      └──► Ground Python Generator   ──► Python module (.py)
```

### 各端職責

| 端點 | 支援語言 | 負責功能 |
| :--- | :--- | :--- |
| **Rocket（飛控端 / STM32）** | C (`protocol.h` / `protocol.c`) | **Encode Telemetry**（打包遙測資料）<br>**Decode Command**（解析控制指令） |
| **Ground Station（地面站）** | C (`protocol.h` / `protocol.c`)<br>Python (`.py`) | **Decode Telemetry**（解析遙測資料）<br>**Encode Command**（打包控制指令） |

---

## 封包格式（Packet Frame）

所有遙測與指令封包皆使用固定 Header + Payload 格式，多位元組數值統一採用 **Little-Endian** 編碼：

```text
┌───────────────┬───────────────┬──────────────────────┐
│ Packet/Cmd ID │ Payload Length│       Payload        │
│    1 byte     │    1 byte     │       N bytes        │
└───────────────┴───────────────┴──────────────────────┘
```

- **Packet / Command ID** (`1 byte`)：封包或指令識別碼
- **Payload Length** (`1 byte`)：Payload 長度（不含 2-byte Header）
- **Payload** (`N bytes`)：依 `protocol.yaml` 定義依序排列的欄位資料

### 支援資料型別（Scalar Types）

| YAML 型別（支援別名） | C 型別 | Python `struct` | 大小 (Bytes) |
| :--- | :--- | :--- | :---: |
| `uint8` / `uint8_t` | `uint8_t` | `B` | 1 |
| `int16` / `int16_t` | `int16_t` | `h` | 2 |
| `uint16` / `uint16_t` | `uint16_t` | `H` | 2 |
| `int32` / `int32_t` | `int32_t` | `i` | 4 |
| `uint32` / `uint32_t` | `uint32_t` | `I` | 4 |
| `float32` | `float` | `f` | 4 |

---

## 專案結構

```text
Telemetry/
├── protocol.yaml             # 協定定義檔（Single Source of Truth）
├── generate_protocol.py      # CLI 程式碼產生器入口
├── protocol_design.md        # 專案設計規格與開發進度文件
├── requirements.txt          # Python 相依套件
├── protocol/                 # 核心協定解析與驗證模組
│   ├── types.py              # 資料型別定義與轉換
│   ├── model.py              # 內部資料模型 (Protocol, Packet, Command, Field, Argument)
│   ├── parser.py             # YAML 解析器
│   └── validator.py          # 協定規則檢查（重複 ID、欄位、型別等驗證）
├── generators/               # 目標語言產生器
│   ├── c_generator.py        # Rocket 端與 Ground 端 C 程式碼產生器
│   └── python_generator.py   # Ground 端 Python 程式碼產生器
├── generated/                # 自動產生的程式碼輸出目錄（請勿手動修改）
│   ├── rocket/               # 飛控端 C 程式碼 (protocol.h, protocol.c)
│   └── ground/               # 地面站 C 程式碼 (protocol.h, protocol.c)
└── tests/                    # 單元測試與 C/Python 跨平台整合測試
```

---

## 快速開始

### 1. 建立虛擬環境與安裝依賴

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 2. 檢視協定模型與封包配置（Layout）

直接執行 `generate_protocol.py` 並傳入 `protocol.yaml`，可驗證語法並印出各欄位 offset 與封包大小：

```powershell
.\.venv\Scripts\python generate_protocol.py protocol.yaml
```

### 3. 產生程式碼

- **產生飛控端（Rocket / STM32）C 程式碼（`.h` + `.c`）：**

  ```powershell
  .\.venv\Scripts\python generate_protocol.py protocol.yaml --c-output-dir generated/rocket
  ```

- **產生地面站（Ground Station）C 程式碼（`.h` + `.c`）：**

  ```powershell
  .\.venv\Scripts\python generate_protocol.py protocol.yaml --ground-output-dir generated/ground
  ```

- **產生地面站（Ground Station）Python 模組：**

  ```powershell
  .\.venv\Scripts\python generate_protocol.py protocol.yaml --python-output generated/ground/protocol.py
  ```

- **單獨產生 Header 檔（選用）：**

  ```powershell
  .\.venv\Scripts\python generate_protocol.py protocol.yaml --c-output generated/rocket/protocol.h
  .\.venv\Scripts\python generate_protocol.py protocol.yaml --ground-output generated/ground/protocol.h
  ```

---

## 定義協定（`protocol.yaml` 範例）

修改協定時，**請只編輯 `protocol.yaml`** 並重新執行產生器，切勿手動修改 `generated/` 下的檔案：

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

## 測試與驗證

執行完整測試套件（包含 Model、Parser、Validator、C / Python Generator 以及透過 `gcc` 編譯驗證的跨平台雙向序列化測試）：

```powershell
.\.venv\Scripts\python -m pytest -q
```

或使用 Python 內建 `unittest`：

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```
