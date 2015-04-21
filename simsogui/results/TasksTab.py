# coding=utf-8

from PyQt4.QtGui import QTabWidget, QTableWidget, QTableWidgetItem, QWidget,\
    QVBoxLayout, QScrollArea, QAbstractItemView, QToolBox, QColor
import numpy
from ..QCopyTableWidget import QCopyTableWidget


class JobsList(QCopyTableWidget):
    def __init__(self, parent, result, task):
        self.result = result
        self.task = task
        jobs = result.tasks[task].jobs
        QTableWidget.__init__(self, len(jobs), 9, parent)
        self.setHorizontalHeaderLabels(["Activation", "Start", "End",
                                        "Deadline", "Comp. time",
                                        "Resp. time", "CPI", "Preemptions",
                                        "Migrations"])
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().hide()

        self.update()

    def update(self):
        jobs = self.result.tasks[self.task].jobs
        cycles_per_ms = float(self.result.model.cycles_per_ms)
        self.setVerticalHeaderLabels([job.name for job in jobs])
        self.setRowCount(len(jobs))
        for curRow, job in enumerate(jobs):
            self.setItem(
                curRow, 0,
                QTableWidgetItem(
                    "%.4f" % (job.activation_date / cycles_per_ms)))

            if job.start_date is not None:
                start_date = float(job.start_date) / cycles_per_ms
                self.setItem(curRow, 1, QTableWidgetItem("%.4f" % start_date))

            if job.end_date:
                end_date = float(job.end_date) / cycles_per_ms
                self.setItem(curRow, 2, QTableWidgetItem("%.4f" % end_date))
                if job.exceeded_deadline:
                    self.item(curRow, 2).setBackgroundColor(
                        QColor(220, 180, 180))

            self.setItem(curRow, 3,
                         QTableWidgetItem(
                             "%.4f" %
                             (job.absolute_deadline / cycles_per_ms)))
            if job.computation_time and job.end_date:
                self.setItem(curRow, 4,
                             QTableWidgetItem(
                                 "%.4f" %
                                 (job.computation_time / cycles_per_ms)))
                self.setItem(curRow, 5,
                             QTableWidgetItem(
                                 "%.4f" %
                                 (job.response_time / cycles_per_ms)))
                if job.task.n_instr:
                    self.setItem(curRow, 6, QTableWidgetItem(
                        "%.4f" % (
                            float(job.computation_time) / job.task.n_instr)))
            self.setItem(curRow, 7,
                         QTableWidgetItem(str(job.preemption_count)))
            self.setItem(curRow, 8,
                         QTableWidgetItem(str(job.migration_count)))
        self.resizeColumnsToContents()


class ComputationTimeTable(QCopyTableWidget):
    def __init__(self, result, parent=None):
        QTableWidget.__init__(self, len(result.model.task_list), 6, parent)
        self.result = result
        self.setHorizontalHeaderLabels(['Task', 'min', 'avg', 'max',
                                        'std dev', 'occupancy'])

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().hide()
        self.update()

    def update(self):
        result = self.result
        for curRow, task in enumerate(result.model.task_list):
            jobs = result.tasks[task].jobs
            computationTimes = [job.computation_time for job in jobs if
                                job.computation_time and job.end_date
                                and not job.aborted]
            if len(computationTimes) == 0:
                for i in range(6):
                    self.setItem(curRow, i, QTableWidgetItem(""))
                continue
            cycles_per_ms = float(result.model.cycles_per_ms)
            computationMin = min(computationTimes) / cycles_per_ms
            computationMax = max(computationTimes) / cycles_per_ms
            computationAvg = numpy.average(computationTimes) / cycles_per_ms
            computationStdDev = numpy.std(computationTimes) / cycles_per_ms
            computationOccupancy = sum(
                [job.computation_time for job in jobs
                 if job.computation_time],
                0.0) / result.observation_window_duration

            self.setItem(curRow, 0, QTableWidgetItem(task.name))
            self.setItem(curRow, 1, QTableWidgetItem("%.3f" % computationMin))
            self.setItem(curRow, 2, QTableWidgetItem("%.3f" % computationAvg))
            self.setItem(curRow, 3, QTableWidgetItem("%.3f" % computationMax))
            self.setItem(curRow, 4,
                         QTableWidgetItem("%.3f" % computationStdDev))
            self.setItem(curRow, 5,
                         QTableWidgetItem("%.3f" % computationOccupancy))
        self.resizeColumnsToContents()


class TaskMigrationTable(QCopyTableWidget):
    def __init__(self, result, parent=None):
        QTableWidget.__init__(self, len(result.model.task_list) + 1, 2, parent)
        self.result = result
        self.setHorizontalHeaderLabels(['Task', 'Task migrations'])
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().hide()

    def update(self):
        sum_ = 0
        model = self.result.model
        for curRow, task in enumerate(model.task_list):
            rtask = self.result.tasks[task]
            self.setItem(curRow, 0, QTableWidgetItem(task.name))
            self.setItem(curRow, 1,
                         QTableWidgetItem(str(len(rtask.task_migrations))))
            sum_ += len(rtask.task_migrations)
        self.setItem(len(model.task_list), 0, QTableWidgetItem('sum'))
        self.setItem(len(model.task_list), 1,
                     QTableWidgetItem(str(sum_)))
        self.resizeColumnsToContents()


class InformationTable(QCopyTableWidget):
    def __init__(self, result, field, metrics=('min', 'avg', 'max', 'sum'),
                 parent=None, map_=lambda x: x):
        QTableWidget.__init__(self, len(result.model.task_list),
                              1 + len(metrics), parent)
        self.result = result
        self.field = field
        self.metrics = metrics
        self.map_ = map_

        self.setHorizontalHeaderLabels(['Task'] + metrics)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().hide()

        self.update()

    def update(self):
        functions = {'min': lambda l: min(l),
                     'avg': lambda l: numpy.average(l),
                     'max': lambda l: max(l),
                     'sum': lambda l: sum(l),
                     'std dev': lambda l: numpy.std(l)}
        result = self.result
        field = self.field
        metrics = self.metrics
        map_ = self.map_
        for curRow, task in enumerate(result.model.task_list):
            jobs = result.tasks[task].jobs
            self.setItem(curRow, 0, QTableWidgetItem(task.name))
            l = [map_(getattr(job, field)) for job in jobs
                 if getattr(job, field) is not None and not job.aborted]
            if l:
                for col, m in enumerate(metrics):
                    self.setItem(curRow, col + 1,
                                 QTableWidgetItem("%.3f" % functions[m](l)))
            else:
                for col, m in enumerate(metrics):
                    self.setItem(curRow, col + 1, QTableWidgetItem(""))

        self.resizeColumnsToContents()


class GeneralTab(QWidget):
    def __init__(self, parent, model, result):
        QWidget.__init__(self, parent)
        self.setLayout(QVBoxLayout())

        scrollArea = QScrollArea(self)
        self.layout().addWidget(scrollArea)
        scrollArea.setWidgetResizable(True)

        viewport = QToolBox()
        scrollArea.setWidget(viewport)

        self.computationTimeGroup = ComputationTimeTable(result)
        self.preemptionsGroup = InformationTable(
            result, 'preemption_count', ['min', 'avg', 'max', 'sum'])
        self.migrationsGroup = InformationTable(
            result, 'migration_count', ['min', 'avg', 'max', 'sum'])
        self.taskMigrationsGroup = TaskMigrationTable(result)
        self.responseTimeGroup = InformationTable(
            result, 'response_time', ['min', 'avg', 'max', 'std dev'],
            map_=lambda x: x / float(model.cycles_per_ms))

        viewport.addItem(self.computationTimeGroup, "Computation time:")
        viewport.addItem(self.preemptionsGroup, "Preemptions:")
        viewport.addItem(self.migrationsGroup, "Migrations:")
        viewport.addItem(self.taskMigrationsGroup, "Task migrations:")
        viewport.addItem(self.responseTimeGroup, "Response time:")

    def update(self):
        self.computationTimeGroup.update()
        self.preemptionsGroup.update()
        self.migrationsGroup.update()
        self.taskMigrationsGroup.update()
        self.responseTimeGroup.update()


class TasksTab(QTabWidget):
    def __init__(self, parent, result):
        QTabWidget.__init__(self)
        self.general_tab = GeneralTab(self, result.model, result)
        self.addTab(self.general_tab, "General")
        self.tabs = []
        for task in result.model.task_list:
            tab = JobsList(self, result, task)
            self.addTab(tab, task.name)
            self.tabs.append(tab)

    def update(self):
        self.general_tab.update()
        for tab in self.tabs:
            tab.update()
