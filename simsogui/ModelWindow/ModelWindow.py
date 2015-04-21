#!/usr/bin/python
# coding=utf-8

from PyQt4.QtGui import QTabWidget, QStyle, QIcon

from .GeneralTab import GeneralTab
from .SchedulerTab import SchedulerTab
from .ProcessorsTab import ProcessorsTab
from .TasksTab import TasksTab
from .CachesTab import CachesTab


class ModelWindow(QTabWidget):
    def __init__(self, configuration, simulation_tab):
        QTabWidget.__init__(self)

        self._configuration = configuration
        self.setWindowTitle("Model data")
        self._general_tab = GeneralTab(self, configuration)
        self.addTab(self._general_tab, "General")
        self._scheduler_tab = SchedulerTab(self, configuration, simulation_tab)
        self.addTab(self._scheduler_tab, "Scheduler")
        self._processors_tab = ProcessorsTab(self, configuration)
        self.addTab(self._processors_tab, "Processors")
        self._tasks_tab = TasksTab(self, configuration)
        self.addTab(self._tasks_tab, "Tasks")
        self._caches_tab = CachesTab(self, configuration)
        self.addTab(self._caches_tab, "Caches")

        self._prev_etm = None
        self.configuration_changed()

        self.currentChanged.connect(self.current_changed)
        configuration.configurationChanged.connect(self.configuration_changed)
        configuration.configurationSaved.connect(self.configuration_saved)

    def set_scheduler(self, name):
        self._scheduler_tab.set_name(name)

    def configuration_changed(self):
        self.etm_changed(self._configuration.etm)
        self.check_whole_config()

    def configuration_saved(self):
        self._scheduler_tab.update_path()
        self._tasks_tab.update_path()

    def closeEvent(self, event):
        self.parent().hide()
        event.ignore()

    def check_whole_config(self):
        for index in range(5):
            self.check_config(index)

    def check_config(self, index):
        try:
            if index == 0:
                self._configuration.check_general()
            elif index == 1:
                self._configuration.check_scheduler()
            elif index == 2:
                self._configuration.check_processors()
            elif index == 3:
                self._configuration.check_tasks()
            elif index == 4 and self._configuration.etm == 'cache':
                self._configuration.check_caches()
            else:
                return

            self.widget(index).set_error_message("")
            self.setTabIcon(index, QIcon())
        except Exception as msg:
            self.widget(index).set_error_message(str(msg))
            self.setTabIcon(index, self.style().standardIcon(
                QStyle.SP_MessageBoxCritical))

    def etm_changed(self, etm):
        if self._prev_etm != etm:
            if etm == 'cache':
                self.addTab(self._caches_tab, "Caches")
            else:
                self.removeTab(4)
            self._prev_etm = etm

        self._general_tab.etm_changed(etm)
        self._tasks_tab.etm_changed(etm)
        self._processors_tab.etm_changed(etm)

    def current_changed(self, index):
        if index == 2:
            self._processors_tab.update()
        elif index == 4:
            self._caches_tab.update_penalties()
