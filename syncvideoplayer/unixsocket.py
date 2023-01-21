# Sync Player
# Copyright (C) 2023, Roman Arsenikhin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import threading
import logging
import socket
import json


logger = logging.getLogger(__name__)


class UnixSocket(threading.Thread):
    def __init__(self, ipc_socket):
        self.ipc_socket = ipc_socket
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.connect(self.ipc_socket)

        threading.Thread.__init__(self)

    def stop(self, join=True):
        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_WR)
                self.socket.close()
                self.socket = None
            except OSError:
                pass
        if join:
            self.join()

    def send(self, data):
        if self.socket is None:
            raise BrokenPipeError("socket is closed")
        json_str = json.dumps(data).encode('utf-8') + b'\n'
        self.socket.send(json_str)

    def run(self):
        data = b''
        while True:
            try:
                current_data = self.socket.recv(1024)
                if current_data == b'':
                    break

                data += current_data
                if data[-1] != 10:
                    continue

                data = b''
            except Exception as ex:
                logger.error("Socket connection died.", exc_info=1)
                return
