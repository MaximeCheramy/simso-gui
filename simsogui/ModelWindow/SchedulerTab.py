#!/usr/bin/python
# coding=utf-8

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QFileDialog, \
    QMessageBox, QPushButton, QHeaderView, QWidget, QHBoxLayout

from .CustomFieldsEditor import CustomFieldsEditor
from .Tab import Tab

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
        QTableWidget.__init__(self, 4, 2, parent)
        self._header = ['Scheduler', 'Overhead schedule (cycles)',
                        'Overhead on activate (cycles)',
                        'Overhead on terminate (cycles)']
        self._configuration = configuration
        self._simulation_tab = simulation_tab
        self.refresh_table()
        self.cellChanged.connect(self._cell_changed)
        self.cellActivated.connect(self._cell_activated)

    def refresh_table(self):
        self._manual_change = True
        self._custom_fields = list(self._configuration.scheduler_info.data.keys())
        labels = self._header + self._custom_fields
        self.setRowCount(len(labels))
        self.setVerticalHeaderLabels(labels)
        self.horizontalHeader().setStretchLastSection(False)
        header = self.horizontalHeader()
        header.setResizeMode(0, QHeaderView.Stretch)
        header.setResizeMode(1, QHeaderView.Interactive)
        #header.setResizeMode(2, QHeaderView.Interactive)
        self.horizontalHeader().hide()

        scheduler_item = QTableWidgetItem(
            self._configuration.scheduler_info.name)
        scheduler_item.setFlags(scheduler_item.flags() ^ (Qt.ItemIsEditable))
        self.setItem(0, 0, scheduler_item)

        btn_open = QPushButton(self)
        btn_open.setText('Open')
        btn_open.clicked.connect(self._open_scheduler)
        self.setCellWidget(0, 1, btn_open)

        #self.btn_edit = QPushButton(self)
        #self.btn_edit.setText('Edit')
        #self.btn_edit.clicked.connect(self._simulation_tab.openEditor)
        #self.btn_edit.setEnabled(bool(self._configuration.scheduler_info.name))
        #self.setCellWidget(0, 2, self.btn_edit)

        self.setItem(
            1, 0, QTableWidgetItem(str(
                self._configuration.scheduler_info.overhead))
        )
        self.setSpan(1, 0, 1, 2)
        self.setItem(
            2, 0, QTableWidgetItem(str(
                self._configuration.scheduler_info.overhead_activate))
        )
        self.setSpan(2, 0, 1, 2)

        self.setItem(
            3, 0, QTableWidgetItem(str(
                self._configuration.scheduler_info.overhead_terminate))
        )
        self.setSpan(3, 0, 1, 2)

        i = 4
        for name, value in self._configuration.scheduler_info.data.items():
            self.setItem(i, 0, QTableWidgetItem(str(value)))
            self.setSpan(i, 0, 1, 2)
            i += 1

    def _cell_activated(self, row, col):
        if row == 0 and col == 0:
            self._open_scheduler()

    def _open_scheduler(self):
        name = QFileDialog.getOpenFileName(
            self, caption="Open scheduler",
            directory=self._configuration.cur_dir, filter="*.py")
        try:
            name = unicode(name)
        except NameError:
            pass
        if name:
            self._configuration.scheduler_info.set_name(
                name, self._configuration.cur_dir)
            try:
                self.item(0, 0).setText(
                    self._configuration.scheduler_info.name)
                #self.btn_edit.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(None, "Error loading scheduler",
                                     str(e),
                                     QMessageBox.Ok | QMessageBox.Default,
                                     QMessageBox.NoButton)

                #self.btn_edit.setEnabled(False)

    def _cell_changed(self, row, col):
        if not self._manual_change:
            self._manual_change = True
            return

        if row == 1:
            old_value = str(self._configuration.scheduler_info.overhead)
        elif row == 2:
            old_value = str(self._configuration.scheduler_info.overhead_activate)
        elif row == 3:
            old_value = str(self._configuration.scheduler_info.overhead_terminate)
        elif row >= len(self._header):
            key = self._custom_fields[row - len(self._header)]
            try:
                old_value = str(self._configuration.scheduler_info.data[key])
            except KeyError:
                old_value = ''

        try:
            if row == 1:
                overhead = int(self.item(1, 0).text())
                assert overhead >= 0
                self._configuration.scheduler_info.overhead = overhead
            elif row == 2:
                overhead = int(self.item(2, 0).text())
                assert overhead >= 0
                self._configuration.scheduler_info.overhead_activate = overhead
            elif row == 3:
                overhead = int(self.item(3, 0).text())
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
        self._manual_change = False
        self.item(0, 0).setText(self._configuration.scheduler_info.name)
        self._manual_change = True

    def set_name(self, name):
        self._configuration.scheduler_info.set_name(
            name, self._configuration.cur_dir)
        self.update_path()
