# Copyright (C) 2026 Maryam Sheikh (Mahid Sheikh) <mahid@standingpad.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import atexit
import enum
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import time
from typing import Any

CONFIGS = {
        "default": "Modded",
        "expanded": "Modded (Stardew Valley Expanded)"
    }
ARRPC_PATH = Path.home() / "Documents" / "arrpc"
MODDED_STARDEW_PATH = (
    Path.home() / "Games" / "Heroic" / "Stardew Valley" / "game" / "StardewModdingAPI"
)
UNMODDED_STARDEW_PATH = (
    Path.home() / "Games" / "Heroic" / "Stardew Valley" / "game" / "Stardew Valley"
)

# This Application ID is what Discord uses
# for Stardew Valley when it detects it
# as a process in the normal app. We can
# use this directly to avoid having to register
# an app with them.
APPLICATION_ID = "359509387670192128"
GAME_DETAILS = "Farming All Day and Night"
GAME_STATE = "Playing {group}"

# Not a fan of Discord's default cover image
STARDEW_COVER_IMAGE = "https://images.gog.com/77fef322229973b009db0cac533afbee2a72e61d257486412e3f3020f86c7487.jpg"


class DiscordRPCOpCodes(enum.Enum):
    HANDSHAKE = 0
    FRAME = 1
    CLOSE = 2
    PING = 3
    PONG = 4


def kill_arrpc(arrpc_process: subprocess.Popen[bytes]) -> None:
    """Kill arRPC and its child processes"""
    if not arrpc_process.poll():
        try:
            os.killpg(os.getpgid(arrpc_process.pid), signal.SIGTERM)
            arrpc_process.wait(timeout=2)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            # Force kill it, we tried to be nice >:3
            try:
                os.killpg(os.getpgid(arrpc_process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass


def close_discord_ipc_connection(discord_socket: socket.socket) -> None:
    """Send the close payload to Discord IPC, than close the socket connection"""
    close_payload = {"code": 1000, "message": "Game closed"}
    _ = send_ipc_message(discord_socket, DiscordRPCOpCodes.CLOSE, close_payload)
    discord_socket.close()


def send_ipc_message(
    sock: socket.socket, opcode: DiscordRPCOpCodes, payload: dict[str, Any]
) -> dict[str, Any] | None:
    """Generalized function for sending payloads to Discord IPC"""
    json_bytes: bytes = json.dumps(payload).encode("utf-8")

    # Discord IPC expects two unsigned, 4 byte
    # integers before the JSON payload: one for
    # the opcode, and one for the length of the
    # JSON payload itself
    header: bytes = struct.pack("<II", opcode.value, len(json_bytes))
    sock.sendall(header + json_bytes)

    response_header: bytes = sock.recv(8)
    if not response_header:
        return None

    res_length: int
    _, res_length = struct.unpack("<II", response_header)

    response_data: bytes = sock.recv(res_length)
    return json.loads(response_data.decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--no-arrpc", action="store_true")
    _ = parser.add_argument("--no-discord-rpc", action="store_true")
    _ = parser.add_argument("--vanilla", action="store_true")
    _ = parser.add_argument("--mod-config", type=str)
    args = parser.parse_args()

    vanilla = args.vanilla

    selected_config = None
    if not vanilla:
        if args.mod_config:
            selected_config = args.mod_config
        else:
            for c in CONFIGS:
                print(c)
            while (selected_config := input("Select mod config [or vanilla]: ").lower()) not in tuple(CONFIGS) + ("vanilla",):
                pass

        assert isinstance(selected_config, str)
        vanilla = selected_config == "vanilla"

    # Set up arRPC and RPC status,
    # unless explictly told not to
    if not args.no_arrpc and not args.no_discord_rpc:
        arrpc_process = subprocess.Popen(
            ["/usr/bin/npm", "exec", f"--package={str(ARRPC_PATH)}", "--", "arrpc"],
            start_new_session=True,
        )
        _ = atexit.register(kill_arrpc, arrpc_process)

        # Wait for arRPC to load up
        time.sleep(2)

    if not args.no_discord_rpc:
        socket_path = None
        for location in ("XDG_RUNTIME_DIR", "TMPDIR", "TMP", "TEMP"):
            env_value = os.environ.get(location)
            if not env_value:
                continue
            tmp_socket_path = Path(env_value) / "discord-ipc-0"
            if tmp_socket_path.exists():
                socket_path = tmp_socket_path
                break

        if socket_path:
            print("[Launch Script] Connecting to IPC at", str(socket_path))
            # We can't use with because we want
            # to continue on from this point
            discord_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            discord_socket.connect(str(socket_path))

            handshake_payload = {"v": 1, "client_id": APPLICATION_ID}
            _ = send_ipc_message(
                discord_socket, DiscordRPCOpCodes.HANDSHAKE, handshake_payload
            )

            presence_payload = {
                "cmd": "SET_ACTIVITY",
                "args": {
                    "pid": os.getpid(),
                    "activity": {
                        "details": GAME_DETAILS,
                        "state": GAME_STATE.format(group=(CONFIGS[selected_config] if selected_config else "Vanilla")),
                        "assets": {
                            "large_image": STARDEW_COVER_IMAGE,
                            "large_text": "Stardew Valley :3",
                        },
                        "timestamps": {
                            "start": int(time.time()),
                        },
                    },
                },
                "nonce": "stardew-presence",
            }

            _ = send_ipc_message(discord_socket, DiscordRPCOpCodes.FRAME, presence_payload)

            # Make sure we register the close function
            # when the script exits, since we're not
            # using the with handler
            _ = atexit.register(close_discord_ipc_connection, discord_socket)
        else:
            print("[Launch Script] Could not find IPC!")

    # Finally start the game up
    mod_env = os.environ.copy()
    stardew_path = MODDED_STARDEW_PATH
    if vanilla:
        stardew_path = UNMODDED_STARDEW_PATH
    else:
        if not selected_config:
            print("[Launch Script] Config invalid, exiting...")
            return
        mod_env["SMAPI_MODS_PATH"] = CONFIGS[selected_config]
    _ = subprocess.run([stardew_path], env=mod_env)


if __name__ == "__main__":
    main()
