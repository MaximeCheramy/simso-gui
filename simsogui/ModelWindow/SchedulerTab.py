# coding=utf-8

import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QPushButton, QTableWidgetItem, QTableWidget, QWidget

from .CustomFieldsEditor import CustomFieldsEditor
from .Tab import Tab

from simso.core.Scheduler import get_schedulers

convert_function = {
    'int': int,
    'float': float,
    'bool': bool,
    'str': str
}


class SchedulerTab(Tab):
    def __init__(self, parent, configuration, simulation_tab):
        Tab.__init__(self, parent, configuration)
        self._table = SchedulerTable(self, configuration, simulation_tab)
        self._add_widget(self._table)
        self._add_widget(CustomDataBar(self, self._table, configuration))

    def update_path(self):
        self._table.update_path()

    def set_name(self, name):
        self._table.set_name(name)


class CustomDataBar(QWidget):
    def __init__(self, parent, table, configuration):
        QWidget.__init__(self, parent)
        self._configuration = configuration
        self._table = table
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 8, 0)

        edit_button = QPushButton("Edit extra fields...", self)
        edit_button.clicked.connect(self.edit)
        layout.addWidget(edit_button)

        self.setLayout(layout)

    def edit(self):
        dialog = CustomFieldsEditor(
            self, self._configuration.scheduler_info.fields_types)
        if dialog.exec_():
            fields = dialog.get_fields()
            self._configuration.scheduler_info.fields_types = fields

            to_remove = []
            for name, value in self._configuration.scheduler_info.data.items():
                if name not in fields:
                    to_remove.append(name)
                else:
                    try:
                        self._configuration.scheduler_info.data[name] = \
                            convert_function[fields[name]](
                                self._configuration.scheduler_info.data[name])
                    except:
                        self._configuration.scheduler_info.data[name] = \
                            convert_function[fields[name]]()
            for name in to_remove:
                del self._configuration.scheduler_info.data[name]

            for name, type_ in fields.items():
                if name not in self._configuration.scheduler_info.data:
                    self._configuration.scheduler_info.data[name] = \
                        convert_function[type_]()

            self._table.refresh_table()


class SchedulerTable(QTableWidget):
    def __init__(self, parent, configuration, simulation_tab):
        QTableWidget.__init__(self, 5, 2, parent)
        self._header = ['Scheduler', 'Scheduler Path',
                        'Overhead schedule (cycles)',
                        'Overhead on activate (cycles)',
                        'Overhead on terminate (cycles)']
        self._dict_header = {
            'scheduler': 0,
            'scheduler_path': 1,
            'overhead_schedule': 2,
            'overhead_activate': 3,
            'overhead_terminate': 4
        }
        self._configuration = configuration
        self._simulation_tab = simulation_tab
        self.refresh_table()
        self.cellChanged.connect(self._cell_changed)
        self.cellActivated.connect(self._cell_activated)

    def refresh_table(self):
        self._manual_change = True
        self._custom_fields = list(
            self._configuration.scheduler_info.data.keys())
        labels = self._header + self._custom_fields
        self.setRowCount(len(labels))
        self.setVerticalHeaderLabels(labels)
        self.horizontalHeader().setStretchLastSection(False)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        #header.setSectionResizeMode(2, QHeaderView.Interactive)
        self.horizontalHeader().hide()

        combo = QComboBox()
        combo.addItems(['Custom scheduler...'] + list(get_schedulers()))

        self.setCellWidget(0, 0, combo)
        self.setSpan(0, 0, 1, 2)

        name = self._configuration.scheduler_info.filename
        scheduler_item = QTableWidgetItem(name and os.path.relpath(
            name, self._configuration.cur_dir))
        scheduler_item.setFlags(scheduler_item.flags() ^ (Qt.ItemIsEditable))
        self.setItem(1, 0, scheduler_item)

        self._btn_open = QPushButton(self)
        self._btn_open.setText('Open')
        self._btn_open.clicked.connect(self._open_scheduler)
        self.setCellWidget(1, 1, self._btn_open)

        combo.currentIndexChanged['QString'].connect(self._select_scheduler)
        if self._configuration.scheduler_info.clas:
            i = combo.findText(self._configuration.scheduler_info.clas)
            if i <= 0:
                i = 0
            combo.setCurrentIndex(i)

        self.setItem(
            2, 0, QTableWidgetItem(str(
                self._configuration.scheduler_info.overhead))
        )
        self.setSpan(2, 0, 1, 2)
        self.setItem(
            3, 0, QTableWidgetItem(str(
                self._configuration.scheduler_info.overhead_activate))
        )
        self.setSpan(3, 0, 1, 2)

        self.setItem(
            4, 0, QTableWidgetItem(str(
                self._configuration.scheduler_info.overhead_terminate))
        )
        self.setSpan(4, 0, 1, 2)

        i = 5
        for name, value in self._configuration.scheduler_info.data.items():
            self.setItem(i, 0, QTableWidgetItem(str(value)))
            self.setSpan(i, 0, 1, 2)
            i += 1

    def _cell_activated(self, row, col):
        if row == 1 and col == 0:
            self._open_scheduler()

    def _select_scheduler(self, name):
        try:
            name = unicode(name)
        except NameError:
            pass

        if name == 'Custom scheduler...':
            self._configuration.scheduler_info.clas = ''
            self.item(1, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            if self._configuration.scheduler_info.filename:
                self.item(1, 0).setText(os.path.relpath(
                    self._configuration.scheduler_info.filename,
                    self._configuration.cur_dir))
            self._btn_open.setEnabled(True)
        else:
            self.item(1, 0).setFlags(Qt.ItemIsSelectable)
            self.item(1, 0).setText('')
            self._btn_open.setEnabled(False)
            self._configuration.scheduler_info.clas = name
        self._configuration.conf_changed()

    def _open_scheduler(self):
        name = QFileDialog.getOpenFileName(
            self, caption="Open scheduler",
            directory=self._configuration.scheduler_info.filename,
            filter="*.py")[0]
        try:
            name = unicode(name)
        except NameError:
            pass
        if name:
            self._configuration.scheduler_info.filename = name
            self.item(1, 0).setText(os.path.relpath(
                name, self._configuration.cur_dir))

    def _cell_changed(self, row, col):
        if not self._manual_change:
            self._manual_change = True
            return

        if row == self._dict_header['overhead_schedule']:
            old_value = str(self._configuration.scheduler_info.overhead)
        elif row == self._dict_header['overhead_activate']:
            old_value = str(self._configuration.scheduler_info.overhead_activate)
        elif row == self._dict_header['overhead_terminate']:
            old_value = str(self._configuration.scheduler_info.overhead_terminate)
        elif row >= len(self._header):
            key = self._custom_fields[row - len(self._header)]
            try:
                old_value = str(self._configuration.scheduler_info.data[key])
            except KeyError:
                old_value = ''

        try:
            if row == self._dict_header['overhead_schedule']:
                overhead = int(self.item(row, 0).text())
                assert overhead >= 0
                self._configuration.scheduler_info.overhead = overhead
            elif row == self._dict_header['overhead_activate']:
                overhead = int(self.item(row, 0).text())
                assert overhead >= 0
                self._configuration.scheduler_info.overhead_activate = overhead
            elif row == self._dict_header['overhead_terminate']:
                overhead = int(self.item(row, 0).text())
                assert overhead >= 0
                self._configuration.scheduler_info.overhead_terminate = overhead
            elif row >= len(self._header):
                self._configuration.scheduler_info.data[key] = \
                    convert_function[
                        self._configuration.scheduler_info.fields_types[key]
                    ](self.item(row, col).text())

            self._configuration.conf_changed()
        except (ValueError, AssertionError):
            self._manual_change = False
            self.item(row, col).setText(old_value)

    def update_path(self):
        if not self._configuration.scheduler_info.clas:
            self._manual_change = False
            name = self._configuration.scheduler_info.filename
            self.item(1, 0).setText(name and os.path.relpath(
                name, self._configuration.cur_dir))
            self._manual_change = True
