import threading
import logging
import json
import time

import win32file
import win32pipe

logger = logging.getLogger(__name__)

class WinPipeClient(threading.Thread):

    def __init__(self, ipc_socket):
        logger.info('Opening named pipe %s' % ipc_socket)
        self.handle = win32file.CreateFile(ipc_socket, win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None,
                                           win32file.OPEN_EXISTING, 0, None)
        res = win32pipe.SetNamedPipeHandleState(self.handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)

        threading.Thread.__init__(self)

    def stop(self, join=True):
        logger.debug("Request to stop pipe thread")
        if self.handle is not None:
            try:
                win32file.CloseHandle(self.handle)
                self.handle = None
            except OSError:
                pass
        if join:
            self.join()
        logger.debug("Stopped pipe thread")

    def send(self, data):
        if self.handle is None:
            raise BrokenPipeError("pipe is closed")
        json_str = json.dumps(data).encode('utf-8') + b'\n'
        win32file.WriteFile(self.handle, json_str)

    def run(self):
        data = b''
        while True:
            try:
                _, bytes_pending, result = win32pipe.PeekNamedPipe(self.handle, 0)

                if bytes_pending:
                    result, current_data = win32file.ReadFile(self.handle, 64*1024)
                    if len(current_data) == 0:
                        logger.debug("Breaking loop")
                        break

                    data += current_data
                    if data[-1] != 10:
                        continue

                data = b''
                if bytes_pending == 0:
                    time.sleep(0.1)

            except Exception as ex:
                logger.error("Socket connection died.", exc_info=1)
                return
