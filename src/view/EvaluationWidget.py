from __future__ import annotations
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QFileDialog, QTableView
from PyQt5 import uic

from src.controller.calculation.EvaluationController import EvaluationController
from src.view.DataFrameToTableModel import DataFrameToTableModel
from src.view.CellColoringDelegate import CellColoringDelegate
from src.config import ConfigEvaluationWidget as Cfg


class EvaluationWidget(QWidget):
    """
    This class represents the evaluation widget in the GUI,
    where the user can request to evaluate the functions and export them.
    The user can also set thresholds or optimize the model
    """

    def __init__(self, parent=None):
        """
        Initializes a new evaluation widget.
        It means the graphics will be displayed, the functionalities of the buttons and other
        graphical elements (table) will be defined
        @param parent:
        @type parent:
        """
        super().__init__(parent)

        uic.loadUi(f'{os.path.dirname(__file__)}/ui/evaluation.ui', self)  # load ui file created with Qt Creator

        self.__controller: EvaluationController = EvaluationController()

        self.table = self.findChild(QTableView, "table")

        delegate = CellColoringDelegate()
        self.table.setItemDelegate(delegate)

        self.calculate_button = self.findChild(QPushButton, "button_calculate")
        self.calculate_button.clicked.connect(self.evaluate)
        self.export_button = self.findChild(QPushButton, "export_evaluation_button")
        self.export_button.clicked.connect(self.export)
        self.export_button.setEnabled(False)  # Because at the beginning there are no results to export
        self.optimize_button = self.findChild(QPushButton, "update_model_button")
        self.optimize_button.setEnabled(False)  # by default, the model cannot be optimized at the beginning
        self.optimize_button.clicked.connect(self.optimize)
        self.view_options_button = self.findChild(QToolButton, "view_options_button")
        self.view_options_button.clicked.connect(self.view_threshold_window)

    def update(self):
        """
        refreshes (updates) the evaluation widget
        """
        super().update()

    def set_thresholds(self, thresholds: dict[str, float]):
        """
        This function is called by view_threshold_window() in order to pass the new values to the model
        and apply them on the recent evaluation
        @param thresholds: contains the name of columns and their thresholds
        @type thresholds: a dictionary, where the keys are the columns and their values are the thresholds
        """
        self.__controller.set_thresholds(thresholds)
        evaluation = self.__controller.get_evaluation()
        self.table.setModel(DataFrameToTableModel(evaluation, thresholds))

    def evaluate(self):
        """
        This function sends a request for evaluation to the controller.
        Then it gets the results and displays them to the user
        """
        self.__controller.evaluate()
        # TODO uncomment the following code
        ''' if self.__controller.is_optimizable():
                self.optimize_button.setEnabled(True)'''

        evaluation = self.__controller.get_evaluation()
        thresholds = self.__controller.get_thresholds()
        self.table.setModel(DataFrameToTableModel(evaluation, thresholds=thresholds))
        self.export_button.setEnabled(True)

    def optimize(self):
        """
        This function is used to optimize the model after performing the evaluation
        """
        self.__controller.optimize()
        # TODO: How are the results of the optimization showed?

    def export(self):
        """
        This enables the user to export the results to a path of his/her choice
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        user_input = QFileDialog.getSaveFileName(self, Cfg.EXPORT_DIALOG_TITLE, '',
                                                 Cfg.DIRECTORY_FILE_FORMAT, options=options)
        if user_input:
            self.__controller.export(user_input[0])  # user_input[0] contains the path

    def view_threshold_window(self):
        """
        This function creates  a new threshold window, where the user can enter the new thresholds
        """
        from src.view.ThresholdWindow import ThresholdWindow

        curr_thresholds = self.__controller.get_thresholds()
        dialog = ThresholdWindow(thresholds=curr_thresholds)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.applyClicked.connect(self.set_thresholds)
        dialog.exec_()
