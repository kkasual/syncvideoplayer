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
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import PySide6
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QFileDialog, QPushButton, QSlider, \
    QLabel, QMessageBox

from syncvideoplayer.darkpalette import dark_palette
from syncvideoplayer.utils import ms_to_str_full, ms_to_str
from syncvideoplayer.videopanel import VideoPanel
from syncvideoplayer.widgets import HLayoutWidget, VLayoutWidget

logger = logging.getLogger(__name__)


ANCHOR_OVERLAY = 1

# more or less one frame
EDGE_ANCHOR_DELTA = 30

ABOUT_TEXT = r"""
<center><b>Sync Video Player</b></center>
<center>Version 0.1 (internal build, do not distribute)</center>
<center>(c) 2023, Roman Arsenikhin</center>
<br />
<center>Video player that can play two videos side-by-side</center>
<br /><br />
<center>The software is licensed under GPL v3.</center>
<br />
Built using the following libraries and frameworks:
<ul>
<li>libmpv (https://mpv.io/)</li>
<li>python-mpv (https://github.com/jaseg/python-mpv)</li>
<li>Qt6 (https://www.qt.io/product/qt6)</li>
<li>PySide6 (https://pypi.org/project/PySide6/)</li>
</ul>
The logo is generated using Stable Diffusion.
"""


class PlayerControl(VLayoutWidget):
    SPEED_VALUES = [25, 50, 75, 100, 125]

    play_clicked = Signal()
    seek = Signal(int)
    anchor_clicked = Signal(bool)
    return_to_anchor_clicked = Signal()
    about_clicked = Signal()
    speed_changed = Signal(float)

    def __init__(self):
        super().__init__()
        self._current_pos = 0

        self._w_line1 = HLayoutWidget()
        self._w_line2 = HLayoutWidget()

        # basic controls
        self._w_btn_play = QPushButton('Play')
        self._w_position = QSlider(Qt.Orientation.Horizontal)
        self._w_position.setTickPosition(QSlider.TickPosition.TicksAbove)
        self._w_position.setTickInterval(1000)
        self._w_label_pos = QLabel()

        self._w_line1.add_widget(self._w_btn_play)
        self._w_line1.add_widget(self._w_position)
        self._w_line1.add_widget(self._w_label_pos)

        # advanced controls
        self._w_speed = QSlider(Qt.Orientation.Horizontal)
        self._w_speed.setTickPosition(QSlider.TickPosition.TicksAbove)
        self._w_speed.setTickInterval(1)
        self._w_speed.setRange(0, len(self.SPEED_VALUES)-1)
        self._w_speed.setPageStep(1)
        self._w_speed.setMaximumWidth(80)
        self._w_speed_label = QLabel()

        # Not yet implemented
        # self._w_btn_set_a = QPushButton('A ⇥')
        # self._w_btn_set_a.setCheckable(True)
        # self._w_btn_set_b = QPushButton('⇤ B')
        # self._w_btn_set_b.setCheckable(True)
        self._w_btn_set_anchor = QPushButton('⚓')
        self._w_btn_set_anchor.setCheckable(True)
        self._w_btn_return_to_anchor = QPushButton('⚓ <-')
        self._w_btn_return_to_anchor.setEnabled(False)
        self._w_btn_about = QPushButton('About')

        self._w_line2.add_widget(self._w_btn_set_anchor)
        self._w_line2.add_widget(self._w_btn_return_to_anchor)
        self._w_line2.add_spacer()
        # Not yet implemented
        # self._w_line2.add_widget(self._w_btn_set_a)
        # self._w_line2.add_widget(self._w_btn_set_b)
        self._w_line2.add_widget(self._w_speed)
        self._w_line2.add_widget(self._w_speed_label)
        self._w_line2.add_widget(self._w_btn_about)

        self.add_widget(self._w_line1)
        self.add_widget(self._w_line2)

        self._w_btn_play.clicked.connect(self.play_clicked)
        self._w_position.valueChanged.connect(self.__on_slider_moved)
        self._w_btn_set_anchor.clicked.connect(self.__on_anchor_clicked)
        self._w_btn_return_to_anchor.clicked.connect(self.return_to_anchor_clicked)
        self._w_btn_about.clicked.connect(self.about_clicked)
        self._w_speed.valueChanged.connect(self.__on_speed_changed)

        self.__update_label()
        for idx, val in enumerate(self.SPEED_VALUES):
            if val == 100:
                self._w_speed.setValue(idx)

    def set_length(self, length_ms: int):
        self._w_position.setRange(0, length_ms)

    def __on_slider_moved(self, value: int):
        self._current_pos = value
        self.seek.emit(self._current_pos)
        self.__update_label()

    def __update_label(self):
        self._w_label_pos.setText(ms_to_str_full(self._current_pos))

    def update_position(self, time_ms: int):
        """
        Updates displayed position and internal variable
        :param time_ms: new position
        """
        self._w_position.blockSignals(True)
        self._current_pos = time_ms
        self._w_position.setValue(time_ms)
        self._w_label_pos.setText(ms_to_str_full(self._current_pos))
        self._w_position.blockSignals(False)

    def get_current_pos(self) -> int:
        return self._current_pos

    def __on_anchor_clicked(self):
        self.anchor_clicked.emit(self._w_btn_set_anchor.isChecked())
        self._w_btn_return_to_anchor.setEnabled(self._w_btn_set_anchor.isChecked())

    def __on_speed_changed(self, value):
        speed = self.SPEED_VALUES[value]
        self._w_speed_label.setText('%d%%' % speed)
        self.speed_changed.emit(speed/100.0)


@dataclass
class VideoRecord:
    index: int
    panel: VideoPanel
    duration: Optional[int]
    offset: int
    fixing_time: int
    position: int
    anchor: Optional[int]


class AppWindow(QMainWindow):
    is_playing = False

    def __init__(self, parent: PySide6.QtWidgets.QWidget = None):
        super().__init__(parent)

        if os.environ.get('SYNCVIDEOPLAYERDEBUG', None) is not None:
            basedir = Path('.')
        else:
            basedir = Path(os.path.dirname(__file__))

        icon_path = basedir / 'assets' / 'syncvideoplayer-logo-128.png'

        self.setWindowIcon(QIcon(str(icon_path)))
        self.setWindowTitle('Sync Video Player')
        self.resize(888, 1000)

        self.__fixings_invalid = True

        self._main_panel_layout = QVBoxLayout()

        self._w_main_panel = QWidget()
        self._w_main_panel.setLayout(self._main_panel_layout)

        self._w_player_control = PlayerControl()

        self.setCentralWidget(self._w_main_panel)

        self._records = [
            VideoRecord(0, VideoPanel(), None, 0, 0, 0, None),
            VideoRecord(1, VideoPanel(), None, 0, 0, 0, None),
        ]
        for vr in self._records:
            vr.panel.clicked_open_video.connect(self.__fn_click_open_video(vr.panel))
            vr.panel.duration.connect(self.__fn_duration_known(vr))
            vr.panel.playback_toggled.connect(self.__fn_playback_toggled(vr))
            vr.panel.seek.connect(self.__fn_panel_seek(vr))
            vr.panel.pos_changed.connect(self.__fn_panel_pos_changed(vr))
            self._main_panel_layout.addWidget(vr.panel)
        self._records[0].panel.pos_changed.connect(self.__on_pos_changed)

        self._main_panel_layout.addWidget(self._w_player_control)

        self._w_player_control.play_clicked.connect(self.__on_play_clicked)
        self._w_player_control.seek.connect(self.__on_seek)
        self._w_player_control.speed_changed.connect(self.__on_speed_changed)
        self._w_player_control.anchor_clicked.connect(self.__on_anchor)
        self._w_player_control.return_to_anchor_clicked.connect(self.__on_return_to_anchor)
        self._w_player_control.about_clicked.connect(self.__on_about)

        self.__update_control_status()

    def __update_range(self):
        min_length = min([panel.duration or 0 for panel in self._records])
        logger.debug('Current min length: %dms' % min_length)
        self._w_player_control.set_length(min_length)

    def __update_control_status(self):
        all_videos_loaded = all([x.panel.has_video() for x in self._records])
        self._w_player_control.setEnabled(all_videos_loaded)

    def __update_panels_status(self, is_playing: bool):
        for vr in self._records:
            vr.panel.set_controls_enabled(not is_playing)

    def __fix_after_seek_panel(self, vr: VideoRecord, time_ms: int):
        """
        Called after seek was performed for the panel. Updates global position considering current fixings.
        :param vr: video to update fixing for
        :param time_ms: fixing time
        """
        # if seek is performed after playing the videos, recalculate offsets based on positions of the videos
        if self.__fixings_invalid:
            for vri in self._records:
                vri.fixing_time = vri.position
            logger.debug('Fixings for panels: %s' % (', '.join([str(x.fixing_time) for x in self._records])))
        vr.fixing_time = time_ms
        self.__lock_offsets()
        min_fixing = min([x.fixing_time for x in self._records])
        self._w_player_control.update_position(min_fixing)
        self.__fixings_invalid = False

    def __fn_panel_seek(self, vr: VideoRecord):
        def fn(time_ms: int):
            self.__fix_after_seek_panel(vr, time_ms)
        return fn

    def __fn_panel_pos_changed(self, vr: VideoRecord):
        def fn(time_ms: int):
            vr.position = time_ms
            vr.panel.update_position(time_ms)
            if vr.anchor is not None:
                self.__update_anchor(vr)
        return fn

    def __fn_playback_toggled(self, vr: VideoRecord):
        def fn(is_playing: bool):
            logger.debug('Video playback status changed for panel %s, is_playing=%s' % (str(vr), str(is_playing)))
            # if one of the videos stopped playing - stop all the videos
            # we are not afraid of reentrance, because the events are edge triggered
            if not is_playing:
                self.__stop_playback()
            else:
                # This means that first panel seek after this will result in fixings recalculations
                self.__fixings_invalid = True

            self.__update_panels_status(is_playing)
        return fn

    def __fn_duration_known(self, vr: VideoRecord):
        def fn(duration: int):
            logger.debug('Known duration for panel %s, duration=%d' % (str(vr), duration))
            vr.duration = duration
            self.__update_range()
        return fn

    def __fn_click_open_video(self, panel: VideoPanel):
        def fn():
            self.__stop_playback()
            fname, _ = QFileDialog.getOpenFileName(None, 'Open video', None,
                                                   "Videos (*.mp4 *.mkv *.avi *.lrv *.MP4 *.AVI *.LRV *.MKV);;All files (*.*)")
            if fname:
                panel.set_video(fname)
                self.__update_control_status()
        return fn

    def __update_panels_positions(self):
        """
        Updates displayed position for each video.
        Called after performing global seek.
        """
        for vr in self._records:
            vr.panel.update_position(self._w_player_control.get_current_pos() + vr.offset)

    def __stop_playback(self):
        self.is_playing = False
        for vr in self._records:
            vr.panel.stop_playback()

    def __start_playback(self):
        self.is_playing = True
        for vr in self._records:
            vr.panel.start_playback()

    def __on_play_clicked(self):
        if self.is_playing:
            self.__stop_playback()
        else:
            self.__start_playback()

    def __on_pos_changed(self, time_ms: int):
        """
        Called when position of the first video changes. Updates internal position
        :param time_ms: position of the first video
        """
        # do not update position when not playing
        if self.is_playing:
            self._w_player_control.update_position(time_ms - self._records[0].offset)
            # for vr in self._records:
            #     vr.panel.update_position(time_ms - self._records[0].offset + vr.offset)

    def __on_seek(self, time_ms: int):
        self._seek(time_ms)
        self.__update_panels_positions()

    def __lock_offsets(self):
        """
        Calculates video offsets based on their fixings
        """
        min_fixing = min([vr.fixing_time for vr in self._records])
        for vr in self._records:
            vr.offset = vr.fixing_time - min_fixing

    def _seek(self, time_ms: int):
        """
        Sets positions of all the videos to the corresponding global position
        :param time_ms: global position
        """
        for vr in self._records:
            vr.panel.set_position(time_ms + vr.offset)

    def __on_anchor(self, is_anchor_set: bool):
        if is_anchor_set:
            self.__set_anchor()
        else:
            self.__clear_anchor()

    def __set_anchor(self):
        """
        Called when user presses anchor button.
        Store current videos positions in variables
        """
        for vr in self._records:
            vr.anchor = vr.position
            self.__update_anchor(vr)
            logger.debug('Set anchor positions: [%s]' % (', '.join([str(x.anchor) for x in self._records])))

    def __clear_anchor(self):
        """
        Called when user turns off anchor.
        Clears anchors in video records
        """
        for vr in self._records:
            vr.anchor = None
            vr.panel.clear_text_osd(ANCHOR_OVERLAY)
            logger.debug('Clear anchor positions: [%s]' % (', '.join([str(x.anchor) for x in self._records])))

    def __update_anchor(self, vr: VideoRecord):
        """
        Updates OSD for the anchor
        :param vr: video to update anchor for
        """
        delta = vr.position - vr.anchor
        text = ms_to_str(delta, sign_always=True)
        if vr.index != 0:
            delta_to_first = delta - (self._records[0].position - self._records[0].anchor)
            if abs(delta_to_first) > EDGE_ANCHOR_DELTA:
                text += ' (%s)' % ms_to_str(delta_to_first, sign_always=True)
        vr.panel.set_text_osd(ANCHOR_OVERLAY, text)

    def __on_about(self):
        QMessageBox.about(self, 'About', ABOUT_TEXT)

    def __on_speed_changed(self, speed: float):
        for vr in self._records:
            vr.panel.set_speed(speed)

    def __on_return_to_anchor(self):
        """
        Called when user presses "back to anchor" button. Seeks all the videos to their stored anchor positions.
        """
        for vr in self._records:
            vr.panel.set_position(vr.anchor)
            vr.panel.update_position(vr.anchor)
            vr.position = vr.anchor
            self.__update_anchor(vr)
            self.__fix_after_seek_panel(vr, vr.anchor)


if __name__ == '__main__':
    import sys

    logFormatter = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)-5.5s]  %(message)s")

    logging.getLogger().setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logging.getLogger().addHandler(consoleHandler)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(dark_palette)

    main_window = AppWindow()
    main_window.show()
    sys.exit(app.exec())
