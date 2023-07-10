from __future__ import annotations

from PyQt5.QtWidgets import QMenu, QFileDialog

from src.view.UIUtil import UIUtil
from src.view.Menu import Menu
from src.controller.ProjectManager import ProjectManager


class FileMenu(Menu):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.__project_manager: ProjectManager = ProjectManager()

        ui_file_menu = self.parent().findChild(QMenu, "menu_file")

        new_project_button = UIUtil.get_action(ui_file_menu, 'action_new_project')
        new_project_button.triggered.connect(self.open_new_project)
        import_data_button = UIUtil.get_action(ui_file_menu, 'action_import_data')
        import_data_button.triggered.connect(self.import_data)
        open_project_button = UIUtil.get_action(ui_file_menu, 'action_project_open')
        open_project_button.triggered.connect(self.open_project)
        save_project_button = UIUtil.get_action(ui_file_menu, 'action_project_save')
        save_project_button.triggered.connect(self.save_project)
        save_as_button = UIUtil.get_action(ui_file_menu, 'action_project_save_as')
        save_as_button.triggered.connect(self.save_project_as)

        # TODO: connect the functions to their controller

    def open_project(self):
        user_input = QFileDialog().getExistingDirectory(self, 'Open Project', '', options=QFileDialog.ShowDirsOnly)
        self.__project_manager.open(user_input[0])

    def open_new_project(self):
        user_input = QFileDialog.getSaveFileName(self, 'Open New Project', '.dir', 'Directory (*.dir)', )
        self.__project_manager.open(user_input[0])

    def save_project(self):
        self.__project_manager.save('')  # save to project current path not possible!

    def save_project_as(self):
        user_input = QFileDialog.getSaveFileName(self, 'Save File', '', 'Directory (*.dir)', )
        self.__project_manager.save(user_input[0])  # contains the path

    def import_data(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("CSV File (*.csv)")
        dlg.fileSelected.connect(self.__project_manager.import_)
        dlg.exec_()

    # what is this function for???
    def export_data(self):  # How to specify csv or JSON?
        user_input = QFileDialog.getSaveFileName(self, 'Export File', '', 'Directory (*.dir)', )
        name = user_input[0] + '.csv'
        raise NotImplementedError  # TODO: IMPLEMENTIEREN
