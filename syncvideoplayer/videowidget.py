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

import logging
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout

logger = logging.getLogger(__name__)

class VideoWidget(QWidget):
    duration = Signal(int)
    playback_toggled = Signal(bool)
    pos_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._layout = QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self.setStyleSheet("background-color:#222;")

        self._w_panel = QWidget()
        self._w_panel.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self._w_panel.setAttribute(Qt.WA_NativeWindow)
        self._layout.addWidget(self._w_panel)

        self._player = None
        self._has_video = False

    def set_video(self, fname: str):
        if self._player is None:
            self._init_player()

        self._player.play(fname)
        self._has_video = True

    def _init_player(self):
        from mpv import MPV

        init_args = {
            'loglevel': 'warn',
            'audio': False,
            'merge_files': True,
            'config': False,
            'input_default_bindings': False,
            'start_event_thread': True,
            'log_handler': print,
            'keep-open': True,
        }
        logger.info('Creating new MPV player on window_id=%d' % int(self._w_panel.winId()))
        self._player = MPV(wid=str(int(self._w_panel.winId())), **init_args)
        self._player['pause'] = True

        self._player.observe_property('pause', self.__on_play_pause)
        self._player.observe_property('time-pos', self.__on_time_changed)
        self._player.observe_property('duration', self.__on_duration_known)

    def stop_playback(self):
        if self._player is not None:
            self._player['pause'] = True

    def start_playback(self):
        if self._player is not None:
            self._player['pause'] = False

    def get_duration(self) -> int:
        if self._player is not None:
            return int(self._player['duration'] * 1000)

    def __on_play_pause(self, name, value):
        self.playback_toggled.emit(not bool(value))

    def __on_time_changed(self, name, value):
        if value:
            self.pos_changed.emit(int(float(value) * 1000))


    def __on_duration_known(self, name, value):
        try:
            duration = int(float(value) * 1000)
            self.duration.emit(duration)
        except Exception:
            ...

    def seek(self, time_ms: int):
        if self._player is not None:
            self._player.seek(float(time_ms) / 1000.0, reference="absolute", precision="exact")

    def has_video(self) -> bool:
        return self._has_video

    def set_text_osd(self, id: int, text: str):
        self._player.command('osd_overlay', id=id, data=text, res_x=1920, res_y=1080, z=0,
                             hidden=False, format='ass-events')

    def clear_text_osd(self, id: int):
        self._player.command('osd_overlay', id=id, data=None, res_x=1920, res_y=1080, z=0,
                             hidden=False, format='none')

    def set_speed(self, speed: float):
        self._player['speed'] = speed
