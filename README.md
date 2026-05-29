<div align="center">

<img src="https://raw.githubusercontent.com/kegelmeier/ha-saphir-ultra-x/main/custom_components/saphir_x/brand/logo.png" alt="Saphir X" width="180">

# Saphir X Pool

Local, **cloud-free** Home Assistant integration for
**SAPHIR Wassertechnologie** _Saphir Ultra X_ pool controllers.

[![HACS Custom][hacs-shield]][hacs]
[![GitHub Release][release-shield]][releases]
[![License][license-shield]][license]
![HA Min Version][ha-shield]

[![Open in HACS][hacs-repo-badge]][hacs-repo]

</div>

Talks directly to the controller over its local TCP protocol (port `8888`) — no
account, no cloud, no internet required. The protocol is not publicly documented;
it was reverse-engineered from a live packet capture and verified against the
official operating manual (see [`PROTOCOL.md`](PROTOCOL.md)).

> [!WARNING]
> Write entities actuate **real pool hardware and dosing setpoints**. The cover
> open/close commands were verified on real hardware; other writes follow the
> documented command set. Test each control once before relying on it in
> automations.

## ✨ Features

**Sensors (read-only)**
- Water temperature, pH
- Redox/ORP, chlorine, H₂O₂ _(shown only if the sensor is installed)_
- Tank fill levels: pH, chlorine, H₂O₂, copper
- Electrode current / voltage _(disabled by default)_
- Fault code _(enum, all documented error states)_
- Serial number & software version _(diagnostic)_

**Controls (write)**
- **Cover** — open/close the pool cover (Rollo)
- **Switches** — light, massage, counter-current (optimistic toggles); sleep mode
- **Numbers** — pH / chlorine / redox / temperature setpoints, chlorine & H₂O₂ boost
- **Buttons** — start backwash, acknowledge fault

## 📦 Installation

### HACS (recommended)

1. Make sure [HACS](https://hacs.xyz) is installed.
2. Add this repository as a **custom repository** (category **Integration**):

   [![Open in HACS][hacs-repo-badge]][hacs-repo]

   …or in HACS go to **⋮ → Custom repositories**, paste
   `https://github.com/kegelmeier/ha-saphir-ultra-x`, choose **Integration**, and add it.
3. Search for **Saphir X Pool**, install, and **restart Home Assistant**.

### Manual

1. Copy `custom_components/saphir_x/` into your `config/custom_components/` directory.
2. Restart Home Assistant.

## ⚙️ Configuration

After installing, add the integration:

[![Add Integration][config-flow-badge]][config-flow]

…or go to **Settings → Devices & Services → Add Integration → “Saphir X Pool”**, then enter:

| Field | Example | Notes |
|-------|---------|-------|
| **Host / IP** | `192.168.1.50` | The controller's local IP address |
| **Port** | `8888` | Default |
| **Device code** | `12345` | Your Saphir code (numeric) |
| **Password** | — | Your Saphir password (numeric) |

The integration polls every 30 seconds over a single short-lived TCP connection
(the controller allows one local session at a time).

## 📝 Notes & limitations

- Relay toggle switches (light / massage / counter-current) are **optimistic** —
  the controller doesn't report their on/off state, so Home Assistant assumes the
  state after a command.
- Sensors reading the “not installed” sentinel (`9999`) are reported as
  **unavailable** rather than showing a bogus value.
- The cover is **assumed-state** (no position feedback from the hardware).
- Brand icon/logo are bundled and served via the Home Assistant brands proxy API
  (requires **Home Assistant 2026.3+**).

## ⚠️ Disclaimer

This is an unofficial, community-built integration. It is **not affiliated with,
endorsed by, or supported by SAPHIR Wassertechnologie GmbH**. “Saphir” is a
trademark of its respective owner. Use at your own risk; the author accepts no
liability for damage to equipment, pools, or water chemistry.

## 📄 License

Released under the [MIT License](LICENSE).

<!-- badges -->
[hacs]: https://hacs.xyz
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[releases]: https://github.com/kegelmeier/ha-saphir-ultra-x/releases
[release-shield]: https://img.shields.io/github/v/release/kegelmeier/ha-saphir-ultra-x?style=for-the-badge
[license]: https://github.com/kegelmeier/ha-saphir-ultra-x/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/kegelmeier/ha-saphir-ultra-x?style=for-the-badge
[ha-shield]: https://img.shields.io/badge/Home%20Assistant-2024.8%2B-41BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white
[hacs-repo]: https://my.home-assistant.io/redirect/hacs_repository/?owner=kegelmeier&repository=ha-saphir-ultra-x&category=integration
[hacs-repo-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[config-flow]: https://my.home-assistant.io/redirect/config_flow_start/?domain=saphir_x
[config-flow-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
