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
