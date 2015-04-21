# coding=utf-8

from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QComboBox

from .Tab import Tab
from simso.core.etm import execution_time_model_names


class GeneralTab(Tab):
    def __init__(self, parent, configuration):
        Tab.__init__(self, parent, configuration)
        self._general_table = GeneralTable(self, configuration)
        self._add_widget(self._general_table)

    def etm_changed(self, etm):
        self._general_table.etm_changed(etm)


class GeneralTable(QTableWidget):
    def __init__(self, parent, configuration):
        QTableWidget.__init__(self, 5, 1, parent)
        self._configuration = configuration
        self._manual_change = True
        self.setVerticalHeaderLabels(
            ["Duration (cycles)", "Duration (ms)", "Cycles / ms",
             'RAM access time', 'Execution Time Model'])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().hide()
        self.setItem(0, 0, QTableWidgetItem(str(configuration.duration)))
        self.setItem(1, 0, QTableWidgetItem(str(
            float(configuration.duration) / configuration.cycles_per_ms)))
        self.setItem(2, 0, QTableWidgetItem(str(configuration.cycles_per_ms)))
        self.setItem(
            3, 0, QTableWidgetItem(str(configuration.memory_access_time)))

        item = QComboBox(self)
        selected = 0
        for i, (etm_name, etm_code) in \
                enumerate(execution_time_model_names.items()):
            item.addItem(etm_name)
            if etm_code == configuration.etm:
                selected = i
        item.setCurrentIndex(selected)
        self.setCellWidget(4, 0, item)

        def activation_handler(x):
            configuration.etm = execution_time_model_names[str(x)]
            configuration.conf_changed()
        item.activated['QString'].connect(activation_handler)

#        self._update_observe_window()

        self.cellChanged.connect(self._cell_changed)
#        self.cellActivated.connect(self._cell_activated)

#    def _update_observe_window(self):
#        if self._configuration.observe_window:
#            item = QTableWidgetItem('{} to {}'.format(
#                self._configuration.observe_window[0],
#                self._configuration.observe_window[1]))
#        else:
#            item = QTableWidgetItem('Entire duration')
#        item.setFlags(item.flags() ^ (Qt.ItemIsEditable))
#        self.setItem(5, 0, item)

    def etm_changed(self, etm):
        if etm == 'cache':
            self.verticalHeader().showSection(3)
        else:
            self.verticalHeader().hideSection(3)

#    def _cell_activated(self, row, col):
#        if row == 5:
#            dialog = ObservationWindowConfigure(self._configuration)
#            if dialog.exec_():
#                self._configuration.observe_window = \
#                    dialog.getObservationWindow()
#
#                self._configuration.conf_changed()
#                self._update_observe_window()

    def _cell_changed(self, row, col):
        if not self._manual_change:
            self._manual_change = True
            return

        configuration = self._configuration

        if row == 0:
            old_value = str(configuration.duration)
        elif row == 1:
            old_value = str(float(configuration.duration) /
                            configuration.cycles_per_ms)
        elif row == 2:
            old_value = str(configuration.cycles_per_ms)
        elif row == 3:
            old_value = str(configuration.memory_access_time)

        try:
            if row == 0:
                duration = int(self.item(row, col).text())
                assert duration >= 0
                configuration.duration = duration
                self._manual_change = False
                self.item(1, 0).setText(
                    str(float(duration) / configuration.cycles_per_ms))
            elif row == 1:
                duration = int(float(self.item(1, 0).text()) *
                               configuration.cycles_per_ms)
                assert duration >= 0
                configuration.duration = duration
                self._manual_change = False
                self.item(0, 0).setText(str(duration))
            elif row == 2:
                cycles_per_ms = int(self.item(2, 0).text())
                assert cycles_per_ms >= 0
                configuration.duration = int(
                    configuration.duration * cycles_per_ms
                    / configuration.cycles_per_ms)
                configuration.cycles_per_ms = cycles_per_ms
                self._manual_change = False
                self.item(0, 0).setText(str(configuration.duration))
            elif row == 3:
                memory_access_time = int(self.item(row, col).text())
                assert memory_access_time >= 0
                configuration.memory_access_time = memory_access_time
                configuration.calc_penalty_cache()

            configuration.conf_changed()
        except (ValueError, AssertionError):
            self._manual_change = False
            self.item(row, col).setText(old_value)
