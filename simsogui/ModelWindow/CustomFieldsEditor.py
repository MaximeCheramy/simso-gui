from PyQt4.QtGui import QDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, \
    QLineEdit, QComboBox, QPushButton, QListWidget, QAbstractItemView
from .AddRemoveButtonBar import AddRemoveButtonBar
import re


class AddFieldDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(QLabel('Enter the field name:', self))
        self._field_name_edit = QLineEdit(self)
        self._field_name_edit.textChanged.connect(self._text_changed)
        layout.addWidget(self._field_name_edit)
        layout.addWidget(QLabel('Type:', self))
        self._type_combo = QComboBox(self)
        self._type_combo.addItems(['int', 'float', 'bool', 'str'])
        layout.addWidget(self._type_combo)

        buttons = QWidget(self)
        buttons_layout = QHBoxLayout()
        buttons.setLayout(buttons_layout)
        buttons_layout.addStretch()
        self._ok_button = QPushButton("Ok")
        self._ok_button.setEnabled(False)
        cancel_button = QPushButton("Cancel")
        self._ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self._ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addWidget(buttons)

    def _text_changed(self, text):
        self._ok_button.setEnabled(
            re.match('^[a-zA-Z][a-zA-Z0-9_-]*$', text) is not None)

    @property
    def name(self):
        return self._field_name_edit.text()

    @property
    def ftype(self):
        return str(self._type_combo.currentText())


class CustomFieldsEditor(QDialog):

    def __init__(self, parent, fields):
        QDialog.__init__(self, parent)

        layout = QVBoxLayout(self)

        self._list_elements = QListWidget(self)
        self._fields = dict(fields)
        for field, ftype in fields.items():
            self._list_elements.addItem(field + ' (' + ftype + ')')

        self._list_elements.setSelectionMode(
            QAbstractItemView.ExtendedSelection)

        layout.addWidget(self._list_elements)

        add_remove = AddRemoveButtonBar(self, 'Remove selected field(s)',
                                        self.remove, 'Add field', self.add)
        layout.addWidget(add_remove)

        buttons = QWidget(self)
        buttons_layout = QHBoxLayout()
        buttons.setLayout(buttons_layout)
        buttons_layout.addStretch()
        ok_button = QPushButton("Ok")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def remove(self):
        res = []
        for item in self._list_elements.selectedItems():
            del self._fields[str(item.text()).split(' ')[0]]
            res.append(self._list_elements.row(item))

        for row in sorted(res, key=lambda x: -x):
            self._list_elements.takeItem(row)

    def add(self):
        dialog = AddFieldDialog(self)
        if dialog.exec_():
            self._fields[str(dialog.name)] = dialog.ftype
            self._list_elements.addItem(
                dialog.name + ' (' + dialog.ftype + ')')

    def get_fields(self):
        return self._fields
