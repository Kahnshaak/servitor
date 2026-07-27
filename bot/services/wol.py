from __future__ import annotations

import socket


def _build_magic_packet(mac: str) -> bytes:
    """Construct a standard WoL magic packet for the given MAC address."""
    mac_clean = mac.replace(":", "").replace("-", "").upper()
    if len(mac_clean) != 12:
        raise ValueError(f"Invalid MAC address: {mac!r}")
    mac_bytes = bytes.fromhex(mac_clean)
    # Magic packet: 6x 0xFF followed by 16 repetitions of the MAC address
    return b"\xff" * 6 + mac_bytes * 16


def send_wol(mac: str, broadcast: str, port: int = 9) -> None:
    """Send a Wake-on-LAN magic packet via UDP broadcast."""
    packet = _build_magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (broadcast, port))
