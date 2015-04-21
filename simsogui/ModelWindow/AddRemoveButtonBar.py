from PyQt4.QtGui import QWidget, QHBoxLayout, QPushButton, QSpacerItem, \
    QSizePolicy, QStyle, qApp


class AddRemoveButtonBar(QWidget):
    def __init__(self, parent, remove_text, remove_method, add_text,
                 add_method):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        remove_button = QPushButton(remove_text, self)
        remove_button.setIcon(qApp.style().standardIcon(QStyle.SP_TrashIcon))
        remove_button.clicked.connect(remove_method)
        layout.addWidget(remove_button)
        layout.setContentsMargins(8, 0, 8, 0)

        horizontal_spacer = QSpacerItem(50, 20, QSizePolicy.Expanding,
                                        QSizePolicy.Minimum)
        layout.addItem(horizontal_spacer)

        add_button = QPushButton(add_text, self)
        add_button.clicked.connect(add_method)
        layout.addWidget(add_button)
        self.setLayout(layout)
