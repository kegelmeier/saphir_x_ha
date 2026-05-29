# Saphir X Local Protocol — Reverse-Engineering Notes

Target: `<controller-ip>:8888` · Device code `<device-code>` · Password `<password>`
App: Saphir X v2.0.3 (Flutter), pkg `com.example.saphir_x_flutter` / `com.Saphir.SaphirX`
Pool = **<controller-ip>** (SSH+8888; locally-administered MAC, resets on bad TLS).
NOT the pool: a separate device on the LAN (different MAC, web UI) may also have 8888 open.

Status: **Protocol CRACKED from live pcap (`_re/saphir.pcap`, 416 pkts).** The wire
framing, login, and all channel types below are confirmed by real bytes. Remaining work
is the **A999 register→field map** (offsets/scaling), recovered by correlation.

---

## Wire framing (CONFIRMED)
Every message: `55 55 | u16le messageType | 4 bytes (zero/reserved) | u32le payloadLen | payload`
(12-byte header, magic `0x5555` = "UU"). Multiple frames concatenate on one TCP stream.

## Login (CONFIRMED)
- Client → `messageType=3`, payload = ASCII `SAPHIR<user>\n<pass>\n\n`
  → for us: `SAPHIR<device-code>\n<password>\n\n` (24 bytes).
- Device → `messageType=1`, payload = `0x06` (ACK) on success.

## Channels / messageType (CONFIRMED)
| type | direction | purpose | payload |
|------|-----------|---------|---------|
| 3 | C→D | **login** | `SAPHIR<user>\n<pass>\n\n` → reply type1 `0x06` |
| 1 | C↔D | **register read / command** | text cmd framed `STX … ETX` |
| 2 | C↔D | **file/log access** (history graphs) | `\x04/log_data/<YYYYMMDD>`, `\x01<file>.log`, dir-list `c …`/`f …` |
| 5 | C↔D | **system health** | req len 0; reply = text (below) |
| 12 | C↔D | **config JSON** | req `0x01`; reply `\x03{…}` |

### type 1 — register channel (the live values)
- Poll request (sent every ~1s): `\x02R999/00000/587\x03`.
- Response: `\x02A999/<3004 bytes binary>515\x03`
  - `STX "A999/"` header, then **~1500 × u16 big-endian register words**, then an
    ASCII checksum (`515`) + `ETX`. (Request likewise ends in a checksum, `587`.)
  - `9999` (0x270F) = "no sensor / disabled" sentinel.
  - **[MAP]** offset→field still to pin by correlation (see below). Early non-zero words:
    w2=207, w4=2304, w5=8, w6=23, w11=712, w12=505, w15=39, w20=211, w21=64, w32=8753…
- `R<cmd>/<arg>/<arg>` = Read; device answers `A<cmd>/…`. Read-only.

### Individual data read/write (CONFIRMED — primary method, official doc + live test)
Source: official manual "Saphir Ultra X Green 2020.5" (sstpool.at) + verified against device.
- **Read single value:** send `\x02R<num3>/00000/<cksum3>\x03` → reply `\x02A<num3>/<value>/<cksum3>\x03`.
  `value` is decimal (variable width). `9999` = sensor not installed/disabled → treat unavailable.
- **Write single value:** `\x02W<num3>/<value5>/<cksum3>\x03`.
- This replaces the need to decode the binary `R999/A999` blob. Build from these.

**Read-only data numbers (with scale):**
| # | field | scale → unit | live read |
|---|-------|--------------|-----------|
| 001 | Seriennummer | — | <device-code> |
| 002 | Gerätetyp | — | |
| 003 | HW Version | — | |
| 004 | SW Version | — | 06059 |
| 006 | Wassertemperatur (ist) | ÷10 → °C | 21.2 |
| 007 | pH Wert | ÷100 | 7.13 |
| 008 | Redox Wert | ×1 → mV | (9999/na) |
| 009 | Cl Wert | ÷1000 → mg/l | (9999/na) |
| 010 | H2O2 Wert | ÷10 → mg/l | (9999/na) |
| 011 | Strom | ÷100 → A | 0 |
| 012 | Spannung | ÷10 → V | 0 |
| 020 | Füllstand Cu | ÷100 → % | 0 |
| 021 | Füllstand pH | ÷100 → % | 87.53 |
| 022 | Füllstand H2O2 | ÷100 → % | 42.86 |
| 023 | Füllstand Cl | ÷100 → % | 37.56 |
| 030 | Fehlercode (aktuell) | enum | 0 = OK (codes below) |

**Fehlercodes (data 030):** 0=OK, 1=RTC_CLK, 2=PARAMETER, 3=NO_TIMESET, 4=PH_OFRANGE,
5=CU_EMPTY, 6=PH_EMPTY, 7=H2O2_EMPTY, 8=CU_PERDAY, 9=CL_OFRANGE_HI, 10=CL_INJ_LIMIT,
11=CL_EMPTY, 12=FLOW, 13=CL_OFRANGE_LO, 14=REDOX_HI, 15=H2O2_OFRANGE_HI, 16=H2O2_INJ_LIMIT,
17=H2O2_SENSOR, 18=CAN_TRANSMIT, 19=LOW_WATER_LEVEL, 20=BACKFEED.

**Read/Write data numbers:**
| # | field | scale | notes |
|---|-------|-------|-------|
| 100 | Quit Error | — | write-only |
| 110 | Sleepmode | 0/1 | |
| 290 | Soll-Temperatur | ÷10 °C | target temp |
| 200 | pH Sollwert | ÷100 | setpoint |
| 240 | Cl Sollwert | ÷100 mg/l | setpoint |
| 241 | Redox Target | mV | setpoint |
| 102 | Cu-Tagesmenge | ÷1000 g | |
| 222 | H2O2 Tagesmenge | ÷100 l | |
| 247 | Cl Boost | ÷100 l | |
| 223 | H2O2 Boost | ÷100 l | |
| 270 | Start Backwash | — | |
| 130/132 | CAN relay outputs 12–16 (toggle) | bitmask | see below |

**CAN relay bitcodes (write to reg 130/132 — value = bitcode; momentary toggle):**
GEGENSTROM(12)=8 · MASSAGE(13)=16 · ROLLO_OPEN(14)=**32** · ROLLO_CLOSE(15)=**64** · LIGHT(16)=128.
(Verified live: 32 opened, 64 closed the cover. Note: device used reg **132**; manual lists 130.)

### type 1 — command/checksum format (CONFIRMED)
Payload = `STX <OP><reg3>/<val5>/<cksum3> ETX`.
- `OP` = `R` (read) or `W` (write).
- **Checksum** = `sum(ASCII bytes of "<OP><reg3>/<val5>/") mod 1000`, zero-padded to 3 digits.
  Verified: `R999/00000/`→587, `W132/00032/`→576, `W132/00064/`→581.
- Read-all poll: `R999/00000` → `A999/<binary>`.

### Relay control — register W132 (CONFIRMED by open+close test)
Writing a bitmask value to register **132** triggers relays (momentary button press):
| Action | Command (full payload) | value | bit |
|--------|------------------------|-------|-----|
| Cover OPEN (relais14 / "Rollo auf" / BlindsUp)  | `\x02W132/00032/576\x03` | 32 (0x20) | 5 |
| Cover CLOSE (relais15 / "Rollos zu" / BlindsDown) | `\x02W132/00064/581\x03` | 64 (0x40) | 6 |
Mapping looks like bit = (relaisNumber − 9): relais14→bit5, relais15→bit6. Other relays
in register 132 (and likely sibling registers for relais ≤8 / >16) by extension — confirm
each before actuating. **Writes drive physical hardware — verify command + clear area first.**

### type 5 — system health (CONFIRMED, ready as diagnostic sensors)
Plain text, e.g.: `LocalUsers 1`, `InetUsers 0`, `CPUs 2 Utilization(1/5/15min) …`,
`RAM 1008 MiB`, `DiscUsage 819/3845 MiB`, **`SoftwareInfo 0.16`**, **`Uptime 138 days …`**,
`System-Time …`. Easy wins: software version, uptime, local/inet user counts, CPU/RAM/disk.

### type 12 — config JSON (CONFIRMED)
Keys: `CanModules`, `Relais`, `RelaisExtended`, `RelaisAdditionalActivated`, `FlutterConfig`.
`Relais`/`CanModules` map relay numbers → module roles (BlindsUp/Down, etc., with `Switch`).
`FlutterConfig` (stringified JSON) = app-side config: module names ("Rollo auf"), relay
assignment, `moduleSafetySettings`, `pumpPresets`, `location` (lat/long). Does NOT contain
the A999 register map.

## Register map — TO DO by correlation
The A999 u16 array positions for pH / redox(ORP) / water temp / chlor / H2O2 / Cu / flow
are hardcoded in the app's Dart. Recover by matching live app-displayed readings to words
(try scalings: pH×10, temp×10, ORP as-is mV). Relay on/off states likely as bitfields or
in `Relais` config `Switch`. blutter decompile is the fallback for exact offsets/scaling.

---

## Transport (confirmed)
- **Plaintext TCP** on port 8888. **Not TLS** — sending a TLS ClientHello triggers an
  immediate `Connection reset by peer`. The server also stays **silent on connect**
  (no banner) and resets on unexpected first bytes → it expects a specific first frame.
- Custom Dart class **`SaphirSocket`** wraps a plain `dart:io` `Socket`
  (`connectToHost`, `readToSocket`, auto-reconnect via `ReconnectIfLost`).
- Keepalive: `KeepAlive` / `PING` / `KeepAliveNotification` (periodic).

## Framing (confirmed shape, [CAPTURE] for exact encoding)
- Frames are **length-prefixed**: strings `payloadLength`, `"Error on add payload to
  socket"`, `"Error while adding new payload to socket"`, `getDataLength`.
- Payload is **JSON** (`getDataMap`, `*.fromJson`/`toJson` model classes).
- **[CAPTURE]** Need: width/endianness of the length header (likely 4-byte big-endian
  `Uint8List`/`ByteData` — `getInt32List` present), and whether length covers header.

## Message envelope (confirmed)
- JSON object with a **`messageType`** field + payload.
- Response envelope: `BaseResponse` with **`errorCode`** (`ErrorCode`, `_errorCodes`).
- **[CAPTURE]** Need: the integer/string values of `messageType` and `errorCode`.

## Authentication (confirmed)
- Login carries **`username`** (numeric only — "Username must only include numbers",
  "Saphir username") and **`password`** (numeric only — "Saphir password").
  → `<device-code>` / `<password>` fit. Model class **`LoginData.fromJson`**.
- Related fields seen: `deviceId`, `Serial number`, `token`, `domain`.
- Result strings: `login_success`, `login_failed`, `LoginStatus`,
  "Please check your username and password!", "Logging in ... Username: ".
- **[CAPTURE]** Need: exact login JSON keys + the success/challenge response.

## Requests (confirmed names)
- `_systemStatusRequest` — system/status poll.
- `_waterTechRequest` / `waterTechCommand` — water-technology data/command.
- `KeepAlive` / `PING`.
- **[CAPTURE]** Need: which request the dashboard sends on load, and its response body.

## Data model — candidate sensor fields (from strings + i18n)
Water chemistry: `ph`, `redox` (ORP), `chlor`, `h2o2`, `cu` (copper), `flow`, temperature(s).
Status flags: `mainPumpStatus`, `chlorPumpStatus`, `chlorBoostStatus`, `h2o2BoostStatus`,
`backwashStatus`, `ecoStatus`, `dryRunHeightStatus`, `highLevelHeightStatus`,
`pressureStatus`, `dmxStatus`, `dmxColorStatus`, `connectionStatus`,
`relais12Status`…`relais16Status`.
Config/data models (JSON): `SaphirSettings`, `SaphirModuleConfiguration`, `PumpPreset`,
`ModuleSafety`, `SelectedLight`, `LoginData`.
Alarm strings present: chlor empty/overdose/range, `cuEmpty`, `backfeedSensor`,
`cANTransmit`, etc. (good candidates for an alarm/diagnostic sensor).

## Artifacts
- `_re/jadx_out/` — jadx output (Java shell only; logic is in `libapp.so`).
- `_re/libs/libapp.so` — Flutter AOT Dart snapshot (source of the above strings).
- `_re/libapp_strings.txt` — extracted strings.
- `_re/i18n/{en,de}.json` — full UI label map (field/alarm names).

## Open items for the live capture (Phase 1B)
1. Exact length-header encoding (bytes 0..N of each frame).
2. Login request JSON + login response.
3. Dashboard status request + the JSON keys/values of the response (map to fields above).
4. KeepAlive cadence + payload.
