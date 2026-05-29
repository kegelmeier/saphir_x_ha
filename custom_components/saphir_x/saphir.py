"""Async client for the Saphir X pool controller local TCP protocol.

Wire format (reverse-engineered, see PROTOCOL.md):
  frame  = b"\\x55\\x55" | u16le messageType | 4 reserved | u32le payloadLen | payload
  login  = messageType 3, payload b"SAPHIR<user>\\n<pass>\\n\\n"  -> reply type1 b"\\x06"
  read   = messageType 1, payload b"\\x02R<num>/00000/<cksum>\\x03" -> b"\\x02A<num>/<val>/<cksum>\\x03"
  write  = messageType 1, payload b"\\x02W<num>/<val>/<cksum>\\x03"
  cksum  = sum(ASCII of "<cmd>/") % 1000, 3-digit zero-padded
"""

from __future__ import annotations

import asyncio
import struct

MAGIC = b"\x55\x55"
STX = 0x02
ETX = 0x03

MSG_LOGIN = 3
MSG_CMD = 1

ACK = b"\x06"

_IO_TIMEOUT = 8.0


class SaphirError(Exception):
    """Base error for the Saphir client."""


class SaphirConnectionError(SaphirError):
    """Could not connect to / communicate with the controller."""


class SaphirAuthError(SaphirError):
    """Login was rejected by the controller."""


def _checksum(cmd: str) -> str:
    return f"{sum(ord(c) for c in cmd + '/') % 1000:03d}"


def _frame(mtype: int, payload: bytes) -> bytes:
    return MAGIC + struct.pack("<H", mtype) + b"\x00\x00\x00\x00" + struct.pack("<I", len(payload)) + payload


def _cmd_frame(op: str, num: str, value: str = "00000") -> bytes:
    cmd = f"{op}{num}/{value}"
    body = f"{cmd}/{_checksum(cmd)}".encode("ascii")
    return _frame(MSG_CMD, bytes([STX]) + body + bytes([ETX]))


class SaphirClient:
    """Minimal serialized client: one TCP connection per operation."""

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self._host = host
        self._port = port
        self._user = username
        self._pw = password
        self._lock = asyncio.Lock()

    async def _read_frame(self, reader: asyncio.StreamReader) -> tuple[int, bytes]:
        hdr = await asyncio.wait_for(reader.readexactly(12), _IO_TIMEOUT)
        # resync to magic if needed
        guard = 0
        while hdr[:2] != MAGIC:
            extra = await asyncio.wait_for(reader.readexactly(1), _IO_TIMEOUT)
            hdr = hdr[1:] + extra
            guard += 1
            if guard > 4096:
                raise SaphirConnectionError("frame sync lost")
        mtype = struct.unpack_from("<H", hdr, 2)[0]
        length = struct.unpack_from("<I", hdr, 8)[0]
        payload = b""
        if length:
            payload = await asyncio.wait_for(reader.readexactly(length), _IO_TIMEOUT)
        return mtype, payload

    async def _open_and_login(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), _IO_TIMEOUT
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise SaphirConnectionError(f"connect failed: {err}") from err
        try:
            writer.write(_frame(MSG_LOGIN, f"SAPHIR{self._user}\n{self._pw}\n\n".encode()))
            await writer.drain()
            mtype, payload = await self._read_frame(reader)
        except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError) as err:
            writer.close()
            raise SaphirConnectionError(f"login I/O error: {err}") from err
        if not (mtype == MSG_CMD and payload == ACK):
            writer.close()
            raise SaphirAuthError("login rejected (no ACK)")
        return reader, writer

    @staticmethod
    async def _close(writer: asyncio.StreamWriter) -> None:
        try:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), 3.0)
        except Exception:  # noqa: BLE001 - best-effort close
            pass

    async def _await_answer(self, reader: asyncio.StreamReader, num: str) -> int | None:
        """Read frames until the A<num> answer; return its integer value."""
        prefix = b"\x02A" + num.encode("ascii") + b"/"
        for _ in range(8):  # tolerate a few interleaved frames
            mtype, payload = await self._read_frame(reader)
            if mtype == MSG_CMD and payload.startswith(prefix):
                inner = payload.strip(bytes([STX, ETX]))
                parts = inner.split(b"/")
                if len(parts) >= 2 and parts[1].lstrip(b"-").isdigit():
                    return int(parts[1])
                return None
        return None

    async def async_login_test(self) -> None:
        """Validate credentials/connectivity (used by config flow)."""
        async with self._lock:
            reader, writer = await self._open_and_login()
            await self._close(writer)

    async def async_read(self, numbers: list[str]) -> dict[str, int]:
        """Read a set of data numbers in one connection. Returns {num: value}."""
        async with self._lock:
            reader, writer = await self._open_and_login()
            try:
                out: dict[str, int] = {}
                for num in numbers:
                    writer.write(_cmd_frame("R", num))
                    await writer.drain()
                    val = await self._await_answer(reader, num)
                    if val is not None:
                        out[num] = val
                return out
            except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError) as err:
                raise SaphirConnectionError(f"read I/O error: {err}") from err
            finally:
                await self._close(writer)

    async def async_write(self, num: str, value: int) -> None:
        """Write a value (5-digit) to a data number. Actuates hardware."""
        async with self._lock:
            reader, writer = await self._open_and_login()
            try:
                writer.write(_cmd_frame("W", num, f"{value:05d}"))
                await writer.drain()
                # controller echoes an answer frame; read it best-effort
                try:
                    await self._await_answer(reader, num)
                except (asyncio.TimeoutError, asyncio.IncompleteReadError):
                    pass
            except OSError as err:
                raise SaphirConnectionError(f"write I/O error: {err}") from err
            finally:
                await self._close(writer)

    async def async_pulse_relay(self, bitcode: int, register: str) -> None:
        """Toggle a CAN relay by writing its bitcode to the relay register."""
        await self.async_write(register, bitcode)
