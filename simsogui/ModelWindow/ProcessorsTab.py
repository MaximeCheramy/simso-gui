import re

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QHeaderView, \
    QAbstractItemView, QWidget, QHBoxLayout, QPushButton, QColor

from .AddRemoveButtonBar import AddRemoveButtonBar
from .Tab import Tab
from .CustomFieldsEditor import CustomFieldsEditor

convert_function = {
    'int': int,
    'float': float,
    'bool': bool,
    'str': str,
}


class CustomDataBar(QWidget):
    def __init__(self, parent, processors_table, configuration):
        QWidget.__init__(self, parent)
        self._configuration = configuration
        self._processors_table = processors_table
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 8, 0)

        edit_button = QPushButton("Edit data fields...", self)
        edit_button.clicked.connect(self.edit)
        layout.addWidget(edit_button)

        self.setLayout(layout)

    def edit(self):
        dialog = CustomFieldsEditor(self,
                                    self._configuration.proc_data_fields)
        if dialog.exec_():
            fields = dialog.get_fields()
            self._configuration.proc_data_fields = fields
            for proc in self._configuration.proc_info_list:
                proc.data = dict((k, v) for (k, v) in
                                 proc.data.items() if k in fields)
            self._processors_table.refresh_table()


class ProcessorsTab(Tab):
    def __init__(self, parent, configuration):
        Tab.__init__(self, parent, configuration)
        self._processors_table = ProcessorsTable(self, configuration)
        self._add_widget(self._processors_table)
        self._add_widget(CustomDataBar(self, self._processors_table,
                                       configuration))
        self._add_widget(ProcessorsButtonBar(self, self._processors_table))

    def update(self):
        self._processors_table.update()

    def etm_changed(self, etm):
        self._processors_table.etm_changed(etm)


class ProcessorsButtonBar(AddRemoveButtonBar):
    def __init__(self, parent, processors_table):
        AddRemoveButtonBar.__init__(
            self, parent, 'Remove selected processor(s)',
            processors_table.remove_selected_processors,
            'Add processor', processors_table.add_processor)


class ProcessorsTable(QTableWidget):
    def __init__(self, parent, configuration):
        QTableWidget.__init__(self, len(configuration.proc_info_list), 7,
                              parent)
        self._configuration = configuration
        self._manual_change = True
        self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self._header = ['id', 'Name', 'CS overhead', 'CL overhead', 'Caches',
                        'Cycles / mem access', 'Speed']
        self.setVerticalHeaderLabels([""])
        self.verticalHeader().hide()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.refresh_table()

    def refresh_table(self):
        self.setRowCount(0)
        self._manual_change = True

        self._custom_fields = list(
            self._configuration.proc_data_fields.keys())
        self.setColumnCount(len(self._header + self._custom_fields))
        self.setHorizontalHeaderLabels(self._header + self._custom_fields)
        curRow = 0
        for proc_info in self._configuration.proc_info_list:
            self.insertRow(curRow)
            self._add_proc_to_table(curRow, proc_info)
            curRow += 1

        self.cellChanged.connect(self._cell_changed)

    def update(self):
        row = 0
        for proc_info in self._configuration.proc_info_list:
            self.item(row, 4).setText(
                ', '.join([x.name for x in proc_info.caches]))
            self.item(row, 5).setText(str(proc_info.penalty))
            row += 1

    def etm_changed(self, etm):
        # TODO: the etm should specify the fields that maters.
        if etm == 'cache':
            self.horizontalHeader().showSection(4)
            self.horizontalHeader().showSection(5)
            self.horizontalHeader().hideSection(6)
        else:
            self.horizontalHeader().hideSection(4)
            self.horizontalHeader().hideSection(5)
            self.horizontalHeader().showSection(6)
        self.resizeColumnsToContents()

    def _add_proc_to_table(self, row, proc_info):
        self.setItem(row, 0, QTableWidgetItem(str(proc_info.identifier)))
        self.item(row, 0).setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 1, QTableWidgetItem(str(proc_info.name)))
        self.setItem(row, 2,
                     QTableWidgetItem(str(proc_info.cs_overhead)))
        self.item(row, 2).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, 3,
                     QTableWidgetItem(str(proc_info.cl_overhead)))
        self.item(row, 3).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(
            row, 4,
            QTableWidgetItem(', '.join([x.name for x in proc_info.caches])))
        penalty_item = QTableWidgetItem(str(proc_info.penalty))
        penalty_item.setFlags(penalty_item.flags() ^
                              (Qt.ItemIsEditable | Qt.ItemIsEnabled))
        self.setItem(row, 5, penalty_item)
        self.item(row, 5).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, 6, QTableWidgetItem(str(proc_info.speed)))

        for col in range(len(self._custom_fields)):
            key = self._custom_fields[col]
            if key in proc_info.data and proc_info.data[key] is not None:
                item = QTableWidgetItem(str(proc_info.data[key]))
            else:
                item = QTableWidgetItem('')
            item.setBackgroundColor(QColor.fromRgb(200, 255, 200))
            self.setItem(row, col + len(self._header), item)

    def _cell_changed(self, row, col):
        if not self._manual_change:
            self._manual_change = True
            return

        proc = self._configuration.proc_info_list[row]

        old_value = ''
        # Get old Value
        if col == 0:
            old_value = str(proc.identifier)
        elif col == 1:
            old_value = proc.name
        elif col == 2:
            old_value = str(proc.cs_overhead)
        elif col == 3:
            old_value = str(proc.cl_overhead)
        elif col == 4:
            old_value = str(', '.join([x.name for x in proc.caches]))
        elif col == 6:
            old_value = str(proc.speed)
        elif col >= len(self._header):
            key = self._custom_fields[col - len(self._header)]
            try:
                if proc.data[key] is not None:
                    old_value = str(proc.data[key])
                else:
                    old_value = ''

            except KeyError:
                old_value = ''

        try:
            if col == 0:
                identifier = int(self.item(row, col).text())
                proc.identifier = identifier
            elif col == 1:
                name = str(self.item(row, col).text()).strip()
                assert re.match('^[a-zA-Z][a-zA-Z0-9 _-]+$', name)
                proc.name = str(self.item(row, col).text())
            elif col == 2:
                cs_overhead = int(self.item(row, col).text())
                assert cs_overhead >= 0
                proc.cs_overhead = cs_overhead
            elif col == 3:
                cl_overhead = int(self.item(row, col).text())
                assert cl_overhead >= 0
                proc.cl_overhead = cl_overhead
            elif col == 4:
                caches = []
                cache_names = str(self.item(row, col).text()).replace(' ', '')
                if cache_names:
                    for name in cache_names.split(','):
                        cache = None
                        for c in self._configuration.caches_list:
                            if c.name == name:
                                cache = c
                                break

                        assert cache is not None
                        caches.append(cache)

                proc.caches = caches
                self._configuration.calc_penalty_cache()
            elif col == 6:
                speed = float(self.item(row, col).text())
                assert speed >= 0
                proc.speed = speed
            elif col >= len(self._header):
                key = self._custom_fields[col - len(self._header)]
                proc.data[key] = convert_function[
                    self._configuration.proc_data_fields[key]](
                        str(self.item(row, col).text()))

            self._configuration.conf_changed()
        except (ValueError, AssertionError):
            self._manual_change = False
            self.item(row, col).setText(old_value)

    def keyPressEvent(self, event):
        QTableWidget.keyPressEvent(self, event)
        if event.key() == Qt.Key_Delete:
            self.remove_selected_processors()

    def add_processor(self):
        row = self.rowCount()

        identifier = 1
        while identifier in [x.identifier for x in
                             self._configuration.proc_info_list]:
            identifier += 1

        name = "CPU " + str(identifier)

        proc = self._configuration.add_processor(name, identifier)
        self.insertRow(row)
        self._add_proc_to_table(row, proc)

        self._configuration.conf_changed()

    def remove_selected_processors(self):
        to_delete = sorted(
            set([x.row() for x in self.selectedIndexes()]), key=lambda x: -x)
        for index in to_delete:
            del self._configuration.proc_info_list[index]
            self.removeRow(index)
            self._configuration.conf_changed()
