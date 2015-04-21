#!/usr/bin/python
# coding=utf-8

import re

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QHeaderView, \
    QAbstractItemView, QFileDialog, QColor, QWidget, QPushButton, \
    QHBoxLayout, QComboBox

from .Tab import Tab
from .AddRemoveButtonBar import AddRemoveButtonBar
from ..TaskGenerator import TaskGeneratorDialog
from .CustomFieldsEditor import CustomFieldsEditor

from simso.core import Task
from simso.generator.task_generator import gen_arrivals

convert_function = {
    'int': int,
    'float': float,
    'bool': bool,
    'str': str,
}


class CustomDataBar(QWidget):
    def __init__(self, parent, tasks_table, configuration):
        QWidget.__init__(self, parent)
        self._configuration = configuration
        self._tasks_table = tasks_table
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 8, 0)

        edit_button = QPushButton("Edit data fields...", self)
        edit_button.clicked.connect(self.edit)
        layout.addWidget(edit_button)

        self.setLayout(layout)

    def edit(self):
        dialog = CustomFieldsEditor(self, self._configuration.task_data_fields)
        if dialog.exec_():
            fields = dialog.get_fields()
            self._configuration.task_data_fields = fields
            for task in self._configuration.task_info_list:
                task.data = dict((k, v) for (k, v) in
                                 task.data.items() if k in fields)
            self._tasks_table.refresh_table()


class TasksTab(Tab):
    def __init__(self, parent, configuration):
        Tab.__init__(self, parent, parent)
        self.configuration = configuration
        self._tasks_table = TasksTable(self, configuration)
        self._add_widget(self._tasks_table)
        self._add_widget(CustomDataBar(self, self._tasks_table, configuration))
        self._add_widget(TasksButtonBar(self, self._tasks_table))

    def update_path(self):
        self._tasks_table.update_path()

    def etm_changed(self, etm):
        self._tasks_table.etm_changed(etm)

    def generate(self):
        generator = TaskGeneratorDialog(len(self.configuration.proc_info_list))
        if generator.exec_():
            self._tasks_table.remove_all_tasks()
            periodic_tasks = generator.get_nb_periodic_tasks()
            i = 0
            for ci, pi in generator.taskset:
                i += 1
                if i <= periodic_tasks:
                    task = self.configuration.add_task(
                        "Task " + str(i), i, period=pi, wcet=ci, deadline=pi)
                else:
                    task = self.configuration.add_task(
                        "Task " + str(i), i, period=pi, wcet=ci, deadline=pi,
                        task_type="Sporadic",
                        list_activation_dates=gen_arrivals(
                            pi, 0, self.configuration.duration_ms))

                self._tasks_table.add_task(task)


class TasksButtonBar(AddRemoveButtonBar):
    def __init__(self, parent, tasks_table):
        AddRemoveButtonBar.__init__(self, parent, 'Remove selected task(s)',
                                    tasks_table.remove_selected_tasks,
                                    'Add task', tasks_table.add_task)
        generate = QPushButton("Generate Task Set")
        generate.clicked.connect(parent.generate)
        self.layout().addWidget(generate)


class TasksTable(QTableWidget):
    def __init__(self, parent, configuration):
        QTableWidget.__init__(self, 0, 0, parent)
        self._ignore_cell_changed = False
        self.horizontalHeader().setResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()
        self._configuration = configuration
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self._header = ["id", "Name", "Task type", "Abort on miss",
                        "Act. Date (ms)", "Period (ms)",
                        "List of Act. dates (ms)", "Deadline (ms)",
                        "WCET (ms)", "ACET (ms)", "ET Std Dev (ms)",
                        "Base CPI", "Instructions", "MIX",
                        "Stack file", "Preemption cost", "Followed by"]

        self._dict_header = {
            'id': 0,
            'name': 1,
            'task_type': 2,
            'abort': 3,
            'activation_date': 4,
            'period': 5,
            'list_activation_dates': 6,
            'deadline': 7,
            'wcet': 8,
            'acet': 9,
            'et_stddev': 10,
            'base_cpi': 11,
            'n_instr': 12,
            'mix': 13,
            'sdp': 14,
            'preemption_cost': 15,
            'followed': 16
        }

        self.refresh_table()
        self.resizeColumnsToContents()

        self.cellChanged.connect(self._cell_changed)
        self.cellActivated.connect(self._cell_activated)

    def etm_changed(self, etm):
        self.horizontalHeader().hideSection(self._dict_header['base_cpi'])
        self.horizontalHeader().hideSection(
            self._dict_header['n_instr'])
        self.horizontalHeader().hideSection(self._dict_header['mix'])
        self.horizontalHeader().hideSection(self._dict_header['sdp'])
        self.horizontalHeader().hideSection(self._dict_header['acet'])
        self.horizontalHeader().hideSection(self._dict_header['et_stddev'])
        self.horizontalHeader().hideSection(
            self._dict_header['preemption_cost'])

        if etm == 'cache':
            self.horizontalHeader().showSection(self._dict_header['base_cpi'])
            self.horizontalHeader().showSection(
                self._dict_header['n_instr'])
            self.horizontalHeader().showSection(self._dict_header['mix'])
            self.horizontalHeader().showSection(self._dict_header['sdp'])
            self.horizontalHeader().showSection(
                self._dict_header['preemption_cost'])
        elif etm == 'acet':
            self.horizontalHeader().showSection(self._dict_header['acet'])
            self.horizontalHeader().showSection(self._dict_header['et_stddev'])

        self.resizeColumnsToContents()

    def refresh_table(self):
        self.setRowCount(0)
        self._manual_change = True

        self._custom_fields = list(self._configuration.task_data_fields.keys())
        self.setColumnCount(len(self._header + self._custom_fields))
        self.setHorizontalHeaderLabels(self._header + self._custom_fields)
        curRow = 0
        for task in self._configuration.task_info_list:
            self.insertRow(curRow)
            self._add_task_to_table(curRow, task)
            curRow += 1

        self._update_followed_by()

    def _add_task_to_table(self, row, task):
        self._ignore_cell_changed = True
        self.setItem(row, self._dict_header['id'],
                     QTableWidgetItem(str(task.identifier)))
        self.item(row, self._dict_header['id']) \
            .setTextAlignment(Qt.AlignCenter)
        self.setItem(row, self._dict_header['name'],
                     QTableWidgetItem(str(task.name)))

        combo = QComboBox()
        items = [task_type for task_type in Task.task_types_names]
        combo.addItems(items)
        # FIXME: only until I get an access to the documentation.
        for i, t in enumerate(Task.task_types_names):
            if t == task.task_type:
                combo.setCurrentIndex(i)
        combo.currentIndexChanged.connect(
            lambda x: self._cell_changed(row, self._dict_header['task_type']))
        self.setCellWidget(row, self._dict_header['task_type'], combo)

        item = QTableWidgetItem(task.abort_on_miss and 'Yes' or 'No')
        item.setFlags(
            Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setCheckState(task.abort_on_miss and Qt.Checked or Qt.Unchecked)
        self.setItem(row, self._dict_header['abort'], item)

        self.setItem(row, self._dict_header['list_activation_dates'],
                     QTableWidgetItem(
                         ', '.join(map(str, task.list_activation_dates))))
        self.item(row, self._dict_header['list_activation_dates']) \
            .setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        for i in ['activation_date', 'period',
                  'deadline', 'wcet', 'base_cpi', 'n_instr', 'mix', 'acet',
                  'et_stddev', 'preemption_cost']:
            self.setItem(row, self._dict_header[i],
                         QTableWidgetItem(str(task.__dict__[i])))
            self.item(row, self._dict_header[i]) \
                .setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        stack_item = QTableWidgetItem(str(task.stack_file))
        stack_item.setFlags(stack_item.flags() ^ (Qt.ItemIsEditable))
        self.setItem(row, self._dict_header['sdp'], stack_item)

        combo = QComboBox()
        combo.currentIndexChanged.connect(
            lambda x: self._cell_changed(row, self._dict_header['followed']))
        self.setCellWidget(row, self._dict_header['followed'], combo)

        for col in range(len(self._custom_fields)):
            key = self._custom_fields[col]
            if key in task.data and task.data[key] is not None:
                item = QTableWidgetItem(str(task.data[key]))
            else:
                item = QTableWidgetItem('')
            item.setBackgroundColor(QColor.fromRgb(200, 255, 200))
            self.setItem(row, col + len(self._header), item)

        self._ignore_cell_changed = False
        self._show_period(task, row)

    def update_path(self):
        row = 0
        for task in self._configuration.task_info_list:
            self._manual_change = False
            self.item(row, self._dict_header['sdp']).setText(task.stack_file)
            row += 1
        self._manual_change = True

    def _cell_activated(self, row, col):
        if col == self._dict_header['sdp']:
            name = QFileDialog.getOpenFileName(self, caption="Open stack file")
            if name:
                task = self._configuration.task_info_list[row]
                task.set_stack_file(str(name), self._configuration.cur_dir)
                self.item(row, col).setText(str(task.stack_file))

    def _show_period(self, task, row):
        self._ignore_cell_changed = True

        fields = Task.task_types[task.task_type].fields
        for field in ['activation_date', 'list_activation_dates', 'period',
                      'deadline', 'wcet']:
            flags = self.item(row, self._dict_header[field]).flags()
            if field in fields:
                flags |= Qt.ItemIsEnabled
                if field == 'list_activation_dates':
                    self.item(row, self._dict_header[field]).setText(
                        str(', '.join(
                            map(str, task.list_activation_dates))))
                else:
                    self.item(row, self._dict_header[field]).setText(
                        str(task.__dict__[field]))
            else:
                flags &= ~(Qt.ItemIsEnabled)
                self.item(row, self._dict_header[field]).setText('-')
            self.item(row, self._dict_header[field]).setFlags(flags)

        self._ignore_cell_changed = False

    def _update_followed_by(self):
        self._ignore_cell_changed = True
        for row, task in enumerate(self._configuration.task_info_list):
            combo = self.cellWidget(row, self._dict_header['followed'])
            combo.clear()
            items = [''] + ['{} ({})'.format(t.name, t.identifier)
                            for t in self._configuration.task_info_list
                            if t != task and t.task_type == "APeriodic"]
            combo.addItems(items)
            combo.setCurrentIndex(0)
            if task.followed_by:
                for index, element in enumerate(items):
                    if element.endswith(' (' + str(task.followed_by) + ')'):
                        combo.setCurrentIndex(index)
                        break
        self._ignore_cell_changed = False

    def _cell_changed(self, row, col):
        if self._ignore_cell_changed:
            return

        if not self._manual_change:
            self._manual_change = True
            return
        task = self._configuration.task_info_list[row]
        # Get current value.
        if col == self._dict_header['id']:
            old_value = str(task.identifier)
        elif col == self._dict_header['name']:
            old_value = task.name
        elif col == self._dict_header['activation_date']:
            old_value = str(task.activation_date)
        elif col == self._dict_header['period']:
            old_value = str(task.period)
        elif col == self._dict_header['list_activation_dates']:
            old_value = ', '.join(
                map(str, task.list_activation_dates))
        elif col == self._dict_header['deadline']:
            old_value = str(task.deadline)
        elif col == self._dict_header['wcet']:
            old_value = str(task.wcet)
        elif col == self._dict_header['acet']:
            old_value = str(task.acet)
        elif col == self._dict_header['et_stddev']:
            old_value = str(task.et_stddev)
        elif col == self._dict_header['base_cpi']:
            old_value = str(task.base_cpi)
        elif col == self._dict_header['n_instr']:
            old_value = str(task.n_instr)
        elif col == self._dict_header['mix']:
            old_value = str(task.mix)
        elif col == self._dict_header['preemption_cost']:
            old_value = str(task.preemption_cost)
        elif col >= len(self._header):
            key = self._custom_fields[col - len(self._header)]
            try:
                if task.data[key] is not None:
                    old_value = str(task.data[key])
                else:
                    old_value = ''

            except KeyError:
                old_value = ''

        try:
            if col == self._dict_header['id']:
                identifier = int(self.item(row, col).text())
                task.identifier = identifier
            elif col == self._dict_header['name']:
                name = str(self.item(row, col).text()).strip()
                assert re.match('^[a-zA-Z][a-zA-Z0-9 _-]+$', name)
                task.name = str(self.item(row, col).text())
            elif col == self._dict_header['task_type']:
                task.task_type = str(self.cellWidget(row, col).currentText())
                self._show_period(task, row)
            elif col == self._dict_header['abort']:
                task.abort_on_miss = (self.item(row, col).checkState()
                                      == Qt.Checked)
                self.item(row, col).setText(
                    'Yes' if task.abort_on_miss else 'No')
            elif col == self._dict_header['activation_date']:
                activation_date = float(self.item(row, col).text())
                assert activation_date >= 0
                task.activation_date = activation_date
            elif col == self._dict_header['period']:
                period = float(self.item(row, col).text())
                assert period > 0
                task.period = period
            elif col == self._dict_header['list_activation_dates']:
                dates = sorted(
                    map(float, self.item(row, col).text().split(',')))
                task.list_activation_dates = dates
                self.item(row, col).setText(', '.join(map(str, dates)))
            elif col == self._dict_header['deadline']:
                deadline = float(self.item(row, col).text())
                assert deadline > 0
                task.deadline = deadline
            elif col == self._dict_header['wcet']:
                wcet = float(self.item(row, col).text())
                assert wcet > 0
                task.wcet = wcet
            elif col == self._dict_header['acet']:
                acet = float(self.item(row, col).text())
                assert acet > 0
                task.acet = acet
            elif col == self._dict_header['et_stddev']:
                et_stddev = float(self.item(row, col).text())
                assert et_stddev >= 0
                task.et_stddev = et_stddev
            elif col == self._dict_header['base_cpi']:
                base_cpi = float(self.item(row, col).text())
                assert base_cpi > 0
                task.base_cpi = base_cpi
            elif col == self._dict_header['n_instr']:
                n_instr = int(self.item(row, col).text())
                assert n_instr >= 0
                task.n_instr = n_instr
            elif col == self._dict_header['mix']:
                mix = float(self.item(row, col).text())
                assert 0.0 <= mix <= 1.0
                task.mix = mix
            elif col == self._dict_header['preemption_cost']:
                preemption_cost = int(self.item(row, col).text())
                assert preemption_cost >= 0
                task.preemption_cost = preemption_cost
            elif col == self._dict_header['followed']:
                txt = self.cellWidget(row, col).currentText()
                m = re.match('.+\((.+)\)', txt)
                if m:
                    task.followed_by = int(m.group(1))
                else:
                    task.followed_by = None
            elif col >= len(self._header):
                key = self._custom_fields[col - len(self._header)]
                task.data[key] = convert_function[
                    self._configuration.task_data_fields[key]
                ](str(self.item(row, col).text()))

            self._update_followed_by()
            self._configuration.conf_changed()
        except (ValueError, AssertionError):
            self._manual_change = False
            self.item(row, col).setText(old_value)

    def keyPressEvent(self, event):
        QTableWidget.keyPressEvent(self, event)
        if event.key() == Qt.Key_Delete:
            self.remove_selected_tasks()
        if(event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier):
            indexes = self.selectionModel().selectedIndexes()
            # TODO: mettre dans un format xml.
            print("copy : ", indexes)

    def remove_all_tasks(self):
        while self._configuration.task_info_list:
            del self._configuration.task_info_list[0]
            self.removeRow(0)
        self._configuration.conf_changed()

    def remove_selected_tasks(self):
        to_delete = sorted(set([x.row() for x in self.selectedIndexes()]),
                           key=lambda x: -x)
        for index in to_delete:
            del self._configuration.task_info_list[index]
            self.removeRow(index)
        self._configuration.conf_changed()

    def add_task(self, task=None):
        row = self.rowCount()

        identifier = 1
        while identifier in [x.identifier
                             for x in self._configuration.task_info_list]:
            identifier += 1

        name = "TASK T" + str(identifier)
        if not task:
            task = self._configuration.add_task(name, identifier)
        self.insertRow(row)
        self._add_task_to_table(row, task)

        self._update_followed_by()
        self._configuration.conf_changed()
