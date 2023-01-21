import logging
from dataclasses import dataclass
from typing import Optional

import PySide6
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QFileDialog, QPushButton, QSlider, QLabel

from syncplayer.utils import ms_to_str_full
from syncplayer.videopanel import VideoPanel
from syncplayer.widgets import HLayoutWidget, VLayoutWidget

logger = logging.getLogger(__name__)


class PlayerControl(VLayoutWidget):
    play_clicked = Signal()
    seek = Signal(int)

    def __init__(self):
        super().__init__()
        self._current_pos = 0

        self._w_line1 = HLayoutWidget()
        self._w_line2 = HLayoutWidget()

        # basic controls
        self._w_btn_play = QPushButton('Play/Pause')
        self._w_position = QSlider(Qt.Orientation.Horizontal)
        self._w_position.setTickPosition(QSlider.TickPosition.TicksAbove)
        self._w_position.setTickInterval(1000)
        self._w_label_pos = QLabel()

        self._w_line1.add_widget(self._w_btn_play)
        self._w_line1.add_widget(self._w_position)
        self._w_line1.add_widget(self._w_label_pos)

        # advanced controls
        self._w_btn_set_a = QPushButton('A')
        self._w_btn_set_b = QPushButton('B')
        self._w_btn_set_anchor = QPushButton('⚓')

        self._w_line2.add_widget(self._w_btn_set_anchor)
        self._w_line2.add_spacer()
        self._w_line2.add_widget(self._w_btn_set_a)
        self._w_line2.add_widget(self._w_btn_set_b)

        self.add_widget(self._w_line1)
        self.add_widget(self._w_line2)

        self._w_btn_play.clicked.connect(self.play_clicked)
        self._w_position.valueChanged.connect(self.__on_slider_moved)

        self.__update_label()

    def set_length(self, length_ms: int):
        self._w_position.setRange(0, length_ms)

    def __on_slider_moved(self, value: int):
        self._current_pos = value
        self.seek.emit(self._current_pos)
        self.__update_label()

    def __update_label(self):
        self._w_label_pos.setText(ms_to_str_full(self._current_pos))

    def update_position(self, time_ms: int):
        self._w_position.blockSignals(True)
        self._current_pos = time_ms
        self._w_position.setValue(time_ms)
        self._w_label_pos.setText(ms_to_str_full(self._current_pos))
        self._w_position.blockSignals(False)

    def get_current_pos(self) -> int:
        return self._current_pos


@dataclass
class VideoRecord:
    panel: VideoPanel
    duration: Optional[int]
    offset: int
    fixing_time: int
    position: int


class AppWindow(QMainWindow):
    is_playing = False

    def __init__(self, parent: PySide6.QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setWindowTitle('Sync Player')
        self.resize(888, 1000)

        self.__fixings_invalid = True

        self._main_panel_layout = QVBoxLayout()
        #self._main_panel_layout.setContentsMargins(0, 0, 0, 0)

        self._w_main_panel = QWidget()
        self._w_main_panel.setLayout(self._main_panel_layout)

        self._w_player_control = PlayerControl()

        self.setCentralWidget(self._w_main_panel)

        self._records = [
            VideoRecord(VideoPanel(), None, 0, 0, 0),
            VideoRecord(VideoPanel(), None, 0, 0, 0),
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

        self.__update_control_status()

    def __update_range(self):
        max_length = min([panel.duration or 0 for panel in self._records])
        logger.debug('Current max length: %dms' % max_length)
        self._w_player_control.set_length(max_length)

    def __update_control_status(self):
        all_videos_loaded = all([x.panel.has_video() for x in self._records])
        self._w_player_control.setEnabled(all_videos_loaded)

    def __update_panels_status(self, is_playing: bool):
        for vr in self._records:
            vr.panel.set_controls_enabled(not is_playing)

    def __fn_panel_seek(self, vr: VideoRecord):
        def fn(time_ms: int):
            if self.__fixings_invalid:
                for vri in self._records:
                    vri.fixing_time = vri.position
                logger.debug('Fixings for panels: %s' % (', '.join([str(x.fixing_time) for x in self._records])))
            vr.fixing_time = time_ms
            self.__lock_offsets()
            min_fixing = min([x.fixing_time for x in self._records])
            self._w_player_control.update_position(min_fixing)
            self.__fixings_invalid = False
        return fn

    def __fn_panel_pos_changed(self, vr: VideoRecord):
        def fn(time_ms: int):
            vr.position = time_ms
            vr.panel.update_position(time_ms)
        return fn

    def __fn_playback_toggled(self, vr: VideoRecord):
        def fn(is_playing: bool):
            logger.debug('Video playback status changed for panel %s, is_playing=%s' % (str(vr), str(is_playing)))
            # if one of the videos stopped playing - stop all the videos
            # we are not afraid of reentrance, because the events are edge triggered
            if not is_playing:
                self.__stop_playback()
            else:
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
            fname, _ = QFileDialog.getOpenFileName(None, 'Open video', None, "Videos (*.mp4 *.avi *.lrv);;All files (*.*)")
            if fname:
                panel.set_video(fname)
                self.__update_control_status()
        return fn

    def __update_panels_positions(self):
        for vr in self._records:
            vr.panel.update_position(self._w_player_control.get_current_pos() + vr.offset)

    def __stop_playback(self):
        self.is_playing = False
        for vr in self._records:
            vr.panel.stop_playback()
        #self.__update_panels_positions()

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
        # do not update position when not playing
        if self.is_playing:
            self._w_player_control.update_position(time_ms - self._records[0].offset)
            # for vr in self._records:
            #     vr.panel.update_position(time_ms - self._records[0].offset + vr.offset)

    def __on_seek(self, time_ms: int):
        self._seek(time_ms)
        self.__update_panels_positions()

    def __lock_offsets(self):
        min_fixing = min([vr.fixing_time for vr in self._records])
        for vr in self._records:
            vr.offset = vr.fixing_time - min_fixing

    def _seek(self, time_ms: int):
        for vr in self._records:
            vr.panel.set_position(time_ms + vr.offset)


if __name__ == '__main__':
    import sys

    logFormatter = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)-5.5s]  %(message)s")

    logging.getLogger().setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logging.getLogger().addHandler(consoleHandler)

    app = QApplication(sys.argv)

    main_window = AppWindow()
    main_window.show()
    sys.exit(app.exec())


