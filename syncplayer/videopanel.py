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

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QSlider, QSizePolicy, QLineEdit, QPushButton, \
    QSpacerItem

from syncplayer.utils import ms_to_str
from syncplayer.videowidget import VideoWidget
from syncplayer.widgets import HLayoutWidget, VLayoutWidget


class OffsetSlider(QSlider):
    def __init__(self):
        super().__init__(Qt.Orientation.Horizontal)
        self.setTickInterval(1000)
        self.setTickPosition(self.TickPosition.TicksAbove)


class ControlButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setMaximumWidth(30)


class OffsetDisplay(QLineEdit):
    def __init__(self, sign_always):
        super().__init__()
        self.setEnabled(False)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setMaximumWidth(100)
        self._sign_always = sign_always
        self.set_value(0)

    def set_value(self, value: int):
        self._value = value
        self.__update()

    def __update(self):
        self.setText(ms_to_str(self._value, self._sign_always))


class VideoPanelControl(HLayoutWidget):
    clicked_open_video = Signal()
    start_changed = Signal(int)
    offset_changed = Signal(int)
    seek = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._w_start_editor = OffsetSlider()
        self._w_start_editor.setRange(0, 0)
        self._w_start_label = OffsetDisplay(False)

        self._w_button_open_video = ControlButton('⏏')
        self._w_button_dec_ofs_l = ControlButton('<<<')
        self._w_button_dec_ofs_m = ControlButton('<<')
        self._w_button_dec_ofs_s = ControlButton('<')
        self._w_button_inc_ofs_l = ControlButton('>>>')
        self._w_button_inc_ofs_m = ControlButton('>>')
        self._w_button_inc_ofs_s = ControlButton('>')

        self.add_widget(self._w_button_open_video)

        self.add_widget(self._w_button_dec_ofs_l)
        self.add_widget(self._w_button_dec_ofs_m)
        self.add_widget(self._w_button_dec_ofs_s)
        self.add_widget(self._w_start_editor)
        self.add_widget(self._w_button_inc_ofs_s)
        self.add_widget(self._w_button_inc_ofs_m)
        self.add_widget(self._w_button_inc_ofs_l)
        self.add_widget(self._w_start_label)

        self._w_button_open_video.clicked.connect(self.clicked_open_video)
        self._w_start_editor.valueChanged.connect(self.seek)

        self._w_button_dec_ofs_l.clicked.connect(self.__fn_change_pos(-500))
        self._w_button_dec_ofs_m.clicked.connect(self.__fn_change_pos(-100))
        self._w_button_dec_ofs_s.clicked.connect(self.__fn_change_pos(-30))
        self._w_button_inc_ofs_l.clicked.connect(self.__fn_change_pos(500))
        self._w_button_inc_ofs_m.clicked.connect(self.__fn_change_pos(100))
        self._w_button_inc_ofs_s.clicked.connect(self.__fn_change_pos(30))

    def __fn_change_pos(self, delta: int):
        def fn():
            self._w_start_editor.setValue(self._w_start_editor.value() + delta)
        return fn

    def set_duration(self, time_ms: int):
        self._w_start_editor.setRange(0, time_ms)

    def update_position(self, time_ms: int):
        self._w_start_editor.blockSignals(True)
        self._w_start_editor.setValue(time_ms)
        self._w_start_label.set_value(time_ms)
        self._w_start_editor.blockSignals(False)


class VideoPanel(QWidget):
    clicked_open_video = Signal()
    duration = Signal(int)
    playback_toggled = Signal(bool)
    pos_changed = Signal(int)
    seek = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._w_video = VideoWidget()
        self._w_control = VideoPanelControl()
        self._layout.addWidget(self._w_video)
        self._layout.addWidget(self._w_control)

        self._w_control.clicked_open_video.connect(self.clicked_open_video)
        self._w_control.seek.connect(self.seek)
        self._w_control.seek.connect(self.__on_seek)
        self._w_video.duration.connect(self.duration)
        self._w_video.duration.connect(self.__on_duration_known)
        self._w_video.playback_toggled.connect(self.playback_toggled)
        self._w_video.pos_changed.connect(self.pos_changed)


    def __on_duration_known(self, duration):
        self._w_control.set_duration(duration)

    def set_video(self, fname: str):
        self._w_video.set_video(fname)

    def stop_playback(self):
        self._w_video.stop_playback()

    def start_playback(self):
        self._w_video.start_playback()

    def get_duration(self) -> int:
        return self._w_video.get_duration()

    def set_controls_enabled(self, enabled: bool):
        self._w_control.setEnabled(enabled)

    def set_position(self, time_ms: int):
        self._w_video.seek(time_ms)

    def __on_seek(self, time_ms: int):
        self._w_video.seek(time_ms)

    def update_position(self, time_ms: int):
        self._w_control.update_position(time_ms)

    def has_video(self):
        return self._w_video.has_video()

    def set_text_osd(self, *args, **kwargs):
        self._w_video.set_text_osd(*args, **kwargs)

    def clear_text_osd(self, *args, **kwargs):
        self._w_video.clear_text_osd(*args, **kwargs)

    def set_speed(self, *args, **kwargs):
        self._w_video.set_speed(*args, **kwargs)
