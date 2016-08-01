# TODO Add beginning docstring + Sphinx ready
import datetime
from datetime import timedelta
import sys
import random

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QMainWindow, QCalendarWidget


import settings
from database import DbInterface


class SpacedCal(QCalendarWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.painter = QPainter()

    def highlight_dates(self):
        pass


# TODO Write docstring
class MainWindow(QMainWindow):
    def __init__(self, db):
        super(MainWindow, self).__init__()

        self.date_selected = datetime.datetime.now().date()
        self.delta_time = [timedelta(days=1), timedelta(days=2), timedelta(days=7), timedelta(days=30),
                           timedelta(days=90), timedelta(days=180), timedelta(days=380)]
        self.db = db
        self.setup_ui()
        self.setup_table()
        self.show()

    # TODO Clean up auto-generated code
    def setup_ui(self):
        self.setWindowTitle("SpReCal")
        self.setFixedSize(316, 519)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMouseTracking(False)
        self.setFocusPolicy(QtCore.Qt.TabFocus)
        self.setAutoFillBackground(False)

        self.centralwidget = QtWidgets.QWidget(self)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)

        self.gridLayout = QtWidgets.QGridLayout()

        self.add_task = QtWidgets.QPushButton(self.centralwidget)
        self.add_task.setText("Add task")
        self.add_task.setAutoDefault(False)
        self.add_task.setDefault(False)
        self.add_task.setFlat(False)
        self.add_task.setObjectName("addTask")
        self.add_task.clicked.connect(self.make_task_dialog)
        self.gridLayout.addWidget(self.add_task, 0, 0, 1, 1)

        self.delete_task = QtWidgets.QPushButton(self.centralwidget)
        self.delete_task.setText("Delete task")
        self.gridLayout.addWidget(self.delete_task, 0, 1, 1, 1)
        self.delete_task.clicked.connect(self.delete_selected_task)

        self.calendar = SpacedCal(self.centralwidget)
        self.calendar.setObjectName("calendar")
        self.calendar.clicked.connect(self.change_date)
        self.gridLayout.addWidget(self.calendar, 1, 0, 1, 2)

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setText("The tasks for {}".format(self.calendar.selectedDate().toPyDate()))
        self.gridLayout.addWidget(self.label, 2, 0, 1, 2)

        self.table_view = QtWidgets.QTableWidget(self.centralwidget)
        self.gridLayout.addWidget(self.table_view, 3, 0, 1, 2)

        self.mark_complete = QtWidgets.QPushButton(self.centralwidget)
        self.mark_complete.setText("Mark complete")
        self.mark_complete.clicked.connect(self.mark_task_complete)
        self.gridLayout.addWidget(self.mark_complete, 4, 1, 1, 1)

        self.horizontalLayout.addLayout(self.gridLayout)
        self.setCentralWidget(self.centralwidget)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.setTabOrder(self.calendar, self.delete_task)
        self.setTabOrder(self.delete_task, self.table_view)
        self.setTabOrder(self.table_view, self.add_task)
        self.setTabOrder(self.add_task, self.mark_complete)

    @QtCore.pyqtSlot()
    def setup_table(self, date=datetime.datetime.now().date()):
        self.table_view.clearContents()

        self.table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        header = self.db.get_columns()
        data = self.db.get_data(date)

        self.table_view.setColumnCount(len(header))
        self.table_view.setRowCount(len(data))
        self.table_view.setHorizontalHeaderLabels(header)

        self.table_view.setColumnHidden(0, True)
        self.table_view.setColumnHidden(3, True)

        if len(data) > 0:
            for row in range(len(data)):
                for column in range(len(header)):
                    self.table_view.setItem(row, column, QtWidgets.QTableWidgetItem(str(data[row][column])))
        else:
            self.label.setText("This day has no tasks!")

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
        row_num = self.table_view.currentItem().row()
        if row_num is not None:
            item = self.table_view.item(row_num, 0).text()
            print(item)
            self.db.delete_task(item)
            self.setup_table()
        else:
            self.label.setText("No Task selected! Please try again.")

    @QtCore.pyqtSlot()
    def mark_task_complete(self):
        try:
            row_num = self.table_view.currentItem().row()
            id = self.table_view.item(row_num, 0).text()
            counter = int(self.table_view.item(row_num, 4).text())
            if counter <= len(self.delta_time):
                new_date = self.date_selected + self.delta_time[counter]
                print(new_date)
            else:
                new_date = self.date_selected + datetime.timedelta(days=(round(random.random()) * 1000))
            counter += 1
            self.db.change_task(id, new_date, counter)
            self.setup_table()
        except TypeError:
            self.label.setText("No Task selected! Please try again.")


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
        self.titleLineEdit.setObjectName("titleLineEdit")
        self.gridLayout.addWidget(self.titleLineEdit, 0, 1, 1, 1)
        self.descriptionLabel = QtWidgets.QLabel(self.widget)
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.gridLayout.addWidget(self.descriptionLabel, 1, 0, 1, 1)
        self.descriptionLineEdit = QtWidgets.QLineEdit(self.widget)
        self.descriptionLineEdit.setObjectName("descriptionLineEdit")
        self.gridLayout.addWidget(self.descriptionLineEdit, 1, 1, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.widget)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 2)
        self.setWindowTitle("Dialog")
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
    db = DbInterface(settings.load_setting("db options", "name") + '.db')
    app = QApplication(sys.argv)
    ex = MainWindow(db)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
