# TODO Add beginning docstring + Sphinx ready
import datetime
import os
import random
import sys
from datetime import timedelta

import sprecal.settings as settings
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPainter, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QCalendarWidget, QMenu
from PyQt5.QtWidgets import QSystemTrayIcon

from sprecal.database import DbInterface


# TODO Write docstring
class MainWindow(QMainWindow):
    def __init__(self, db):
        super(MainWindow, self).__init__()

        self.date_selected = datetime.datetime.now().date()
        self.db = db
        self.exitOnClose = False
        self.delta_time = [timedelta(days=1), timedelta(days=2), timedelta(days=7), timedelta(days=30),
                           timedelta(days=90), timedelta(days=180), timedelta(days=380)]

        self.icon = QIcon(os.path.join(os.path.curdir, "icon.png"))

        # QTimer for reminders
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.display_message)
        self.start_timer()

        self.setup_ui()
        self.setup_table()
        self.system_tray()
        self.show()

    def start_timer(self):
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(60000 * 10)  # QTimer takes milliseconds by default

    # TODO Clean up auto-generated code
    def setup_ui(self):
        self.setWindowTitle("Sprecal")
        self.setFixedSize(320, 520)
        self.setMouseTracking(False)
        self.setWindowIcon(self.icon)
        self.setFocusPolicy(QtCore.Qt.TabFocus)
        self.setAutoFillBackground(False)

        self.centralwidget = QtWidgets.QWidget(self)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)

        self.gridLayout = QtWidgets.QGridLayout()

        self.add_task = QtWidgets.QPushButton(self.centralwidget)
        self.add_task.setText("Add task")
        self.add_task.clicked.connect(self.make_task_dialog)
        self.gridLayout.addWidget(self.add_task, 0, 0, 1, 1)

        self.delete_task = QtWidgets.QPushButton(self.centralwidget)
        self.delete_task.setText("Delete task")
        self.gridLayout.addWidget(self.delete_task, 0, 1, 1, 1)
        self.delete_task.clicked.connect(self.delete_selected_task)

        self.calendar = QCalendarWidget(self.centralwidget)
        self.calendar.setGridVisible(True)
        self.gridLayout.addWidget(self.calendar, 1, 0, 1, 2)
        self.calendar.clicked.connect(self.change_date)

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setText("The tasks for {}".format(self.calendar.selectedDate().toPyDate()))
        self.gridLayout.addWidget(self.label, 2, 0, 1, 2)

        self.table = QtWidgets.QTableWidget(self.centralwidget)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.gridLayout.addWidget(self.table, 3, 0, 1, 2)

        self.mark_complete = QtWidgets.QPushButton(self.centralwidget)
        self.mark_complete.setText("Mark complete")
        self.gridLayout.addWidget(self.mark_complete, 4, 1, 1, 1)
        self.mark_complete.clicked.connect(self.mark_task_complete)

        self.horizontalLayout.addLayout(self.gridLayout)
        self.setCentralWidget(self.centralwidget)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.setToolTip("Here to make sure you do your work!")

    @QtCore.pyqtSlot()
    def setup_table(self, date=datetime.datetime.now().date()):
        self.table.clearContents()

        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        header = self.db.get_columns()
        data = self.db.get_data(date)

        self.table.setColumnCount(len(header))
        self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(header)

        self.table.setColumnHidden(header.index("id"), True)
        self.table.setColumnHidden(3, True)

        if len(data) > 0:
            for row in range(len(data)):
                for column in range(len(header)):
                    self.table.setItem(row, column, QtWidgets.QTableWidgetItem(str(data[row][column])))
        else:
            self.label.setText("This day has no tasks!")

    def system_tray(self):
        self.systray = QSystemTrayIcon(QIcon())
        self.systray.setIcon(self.icon)

        self.menu = QMenu()
        open_window = self.menu.addAction("Open window")
        exit_entry = self.menu.addAction("Exit")
        self.systray.setContextMenu(self.menu)

        open_window.triggered.connect(self.show_main)
        exit_entry.triggered.connect(QApplication.quit)
        self.systray.show()

    @QtCore.pyqtSlot()
    def display_message(self):
        number = len(self.db.get_data(datetime.datetime.now().date()))
        if number > 0:
            self.systray.showMessage("Reminder", "{} task{}left to go!".format(number, (number > 1) * "s" + " "))
        else:
            self.systray.showMessage("Congratulations", "You're done for the day!")

    @QtCore.pyqtSlot()
    def change_date(self):
        self.date_selected = self.calendar.selectedDate().toPyDate()
        self.label.setText("The tasks for {}".format(self.calendar.selectedDate().toPyDate()))
        self.setup_table(date=self.calendar.selectedDate().toPyDate())

    @QtCore.pyqtSlot()
    def make_task_dialog(self):
        data = TaskDialog(self.db, self.date_selected)
        result = data.exec_()
        if result == 0:
            self.statusbar.showMessage("No new task added!")
        else:
            self.statusbar.showMessage("Added task {}".format(self.db.get_last()))
            self.change_date()

    @QtCore.pyqtSlot()
    def delete_selected_task(self):
        row_num = self.table.currentItem().row()
        if row_num is not None:
            item = self.table.item(row_num, 0).text()
            self.db.delete_task(item)
            self.setup_table()
        else:
            self.label.setText("No Task selected! Please try again.")

    @QtCore.pyqtSlot()
    def mark_task_complete(self):
        try:
            row_num = self.table.currentItem().row()
            id = self.table.item(row_num, 0).text()
            counter = int(self.table.item(row_num, 4).text())
            if counter <= len(self.delta_time):
                new_date = self.date_selected + self.delta_time[counter]
            else:
                new_date = self.date_selected + datetime.timedelta(days=(round(random.random()) * 1000))
            self.db.change_task(id, new_date, counter + 1)
            self.setup_table()
        except TypeError:
            self.label.setText("No Task selected! Please try again.")

    @QtCore.pyqtSlot()
    def show_main(self):
        self.show()

    def closeEvent(self, event):
        if self.exitOnClose:
            super().closeEvent(event)
        else:
            self.hide()


# TODO Add docstring
# TODO Arrange auto-generated code nicely
class TaskDialog(QtWidgets.QDialog):
    def __init__(self, db, date_selected, parent=None):
        super(TaskDialog, self).__init__(parent)
        self.date_selected = date_selected
        self.db = db
        self.setWindowTitle("Add task")
        self.setFixedSize(220, 100)
        self.widget = QtWidgets.QWidget(self)
        self.widget.setGeometry(QtCore.QRect(9, 11, 194, 77))
        self.gridLayout = QtWidgets.QGridLayout(self.widget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.titleLabel = QtWidgets.QLabel(self)
        self.gridLayout.addWidget(self.titleLabel, 0, 0, 1, 1)

        self.titleLineEdit = QtWidgets.QLineEdit(self.widget)
        self.gridLayout.addWidget(self.titleLineEdit, 0, 1, 1, 1)


        self.descriptionLabel = QtWidgets.QLabel(self.widget)
        self.gridLayout.addWidget(self.descriptionLabel, 1, 0, 1, 1)

        self.descriptionLineEdit = QtWidgets.QLineEdit(self.widget)
        self.gridLayout.addWidget(self.descriptionLineEdit, 1, 1, 1, 1)

        self.pushButton = QtWidgets.QPushButton(self.widget)
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 2)
        self.titleLabel.setText("Name")
        self.descriptionLabel.setText("Description")
        self.pushButton.setText("Save")
        self.pushButton.clicked.connect(self.add_task)

        self.show()

    @QtCore.pyqtSlot()
    def add_task(self):
        data = (None, self.titleLineEdit.text(), self.descriptionLineEdit.text(), self.date_selected, 0)
        self.db.make_task(data)
        self.accept()


def main():
    db = DbInterface(settings.load_setting("db options", "name") + ".db")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ex = MainWindow(db)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
