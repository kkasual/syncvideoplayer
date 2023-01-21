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

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout


def __make_layout_widget_class(layout):
    class LayoutWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self._layout = layout()
            self._layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(self._layout)

        def add_spacer(self):
            self._layout.addStretch()

        def add_widget(self, widget: QWidget):
            self._layout.addWidget(widget)

    return LayoutWidget


HLayoutWidget = __make_layout_widget_class(QHBoxLayout)
VLayoutWidget = __make_layout_widget_class(QVBoxLayout)
