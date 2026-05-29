# Saphir X Pool — Home Assistant Integration

Local-polling Home Assistant integration for **SAPHIR Wassertechnologie**
*Saphir Ultra X* pool controllers, talking directly to the controller over its
local TCP protocol (port 8888). No cloud dependency.

The protocol is undocumented publicly; it was reverse-engineered from a live
packet capture and confirmed against the official operating manual. Full details
are in [PROTOCOL.md](PROTOCOL.md).

## Features

**Sensors (read-only)**
- Water temperature, pH
- Redox/ORP, chlorine, H₂O₂ (shown only if the sensor is installed)
- Tank fill levels: pH, chlorine, H₂O₂, copper
- Electrode current/voltage (disabled by default)
- Fault code (enum, with all documented error states)
- Serial number, software version (diagnostic)

**Controls (write)**
- **Cover** — open/close (Rollo) as a `cover` entity
- **Switches** — light, massage, counter-current (optimistic relay toggles); sleep mode
- **Numbers** — pH / chlorine / redox / temperature setpoints, chlorine & H₂O₂ boost
- **Buttons** — start backwash, acknowledge fault

> ⚠️ Write entities actuate real pool hardware and dosing setpoints. The cover
> open/close commands were verified on real hardware; other writes follow the
> documented command set. Use with care.

## Installation

1. Copy `custom_components/saphir_x/` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → "Saphir X Pool"**.
4. Enter:
   - **Host / IP** — the controller's local IP (e.g. `192.168.1.50`)
   - **Port** — `8888`
   - **Device code** — your Saphir code (numeric, e.g. `12345`)
   - **Password** — your Saphir password (numeric)

The integration polls every 30 seconds over a single short-lived TCP connection
(the controller allows one local session at a time).

## Notes / limitations

- Relay toggle switches (light/massage/counter-current) are **optimistic** — the
  controller does not report their on/off state, so Home Assistant assumes state
  after a command.
- Sensors that read the "not installed" sentinel (`9999`) are reported as
  unavailable rather than showing a bogus value.
- The cover is assumed-state (no position feedback from the hardware).

## Project layout

```
custom_components/saphir_x/   the integration
PROTOCOL.md                   reverse-engineered protocol spec
_re/                          research artifacts (pcaps, decompile, client, analyzers)
```
