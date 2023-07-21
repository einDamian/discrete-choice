from __future__ import annotations

from src.model.Project import Project
from src.controller.ProjectManager import ProjectManager

import threading

class AbstractController:
    """Abstract class that serves as a connection to the ProjectManager. 
    The other controllers that are not responsible for storage or project selection 
    can access the project through the inherited method getProject() from this class.
    Since the controllers do not inherit the attribute projectManager, 
    they cannot modify it or use its functions. 
    It serves as a colleague to the ProjectManager in the 'Mediator' design pattern.
    """

    def __init__(self):
        self.__project_manager: ProjectManager = ProjectManager()
        self.__saving_thread = None

    def get_project(self) -> Project:
        """Method as an interface between the controllers and the Project from the Model package.

        Returns:
            Project: The current project snapshot.
        """
        return self.__project_manager.get_project()

    def save(self):
        """Method used to initiate the saving process in a different thread after every step that changes the model.
        """
        if self.__saving_thread is not None and self.__saving_thread.is_alive():
            return  # skip autosave if autosave thread is still running

        self.__saving_thread = threading.Thread(target=self.__project_manager.save, args=(), daemon=False)
        self.__saving_thread.start()
