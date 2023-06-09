from __future__ import annotations
import json

from src.model.data.functions.FunctionalExpression import FunctionalExpression
from src.controller.functions.FunctionController import FunctionController
from src.config import ConfigErrorMessages, ConfigFiles


class DerivativeController(FunctionController):
    """Controller used to control all changes regarding the derivatives"""

    def get_derivatives(self) -> dict[str, FunctionalExpression]:
        """ Accessor method for the derivatives in the model.

        Returns:
            dict[str, FunctionalExpression]: all derivatives, with their respective label as key 
            and their functional expression object as value.
        """
        return self.get_project().get_derivatives()

    def get_variables(self) -> list[(str, str, str)]:
        """ Accessor method for the raw data in the model.

        Returns:
            list[(str, str, str)]: List of tuples containing 
        """
        variables = []
        path = "-"
        #path = self.get_project.get_path()
        data = self.get_project().get_raw_data()
        for row in data.itertuples():
            variables.append((row.Index, row.dtype, path))
        return variables

    def add(self, label: str, function: str):
        """ Addition of a new derivative to the model. Before Addition a safety validation is done.

        Args:
            label (str): label of derivative to be added.
            function (str): user input for the function of the derivative.
        """
        safe_label = self.validate(label)
        if safe_label:
            self.get_project().set_derivative(label, function)
        else:
            raise ValueError(
                ConfigErrorMessages.ERROR_MSG_FUNCTION_LABEL_INVALID)

    def remove(self, label: str):
        """ Method to remove a derivative specified by its label from the model.

        Args:
            label (str): the label of the derivative to be removed.
        """
        self.get_project().remove_derivative(label)

    def change(self, label: str, function: str):
        """ The changing of the function of a derivative in the model. 
        The function to be changed is defined through its label. 
        Before the function is changed in the model a safety validation happens.

        Args:
            label (str): The label of the function to be changed.
            function (str): The user input for the new function.
        """
        safe_function = self.validate(function)
        if safe_function is not None:
            self.get_project().set_derivative(label, function)

    def get_error_report(self, label: str):
        """ Accessor method for the errors generated by the derivative of the given label.

        Args:
            label (str): label of the derivative.

        Returns:
            ErrorReport: the error report of the specified derivative. 
        """
        return self.get_project().get_derivative_error_report(label)

    def export(self, path: str, label: list[str] = None) -> bool:
        """Function to export a derivative as a json file.

        Args:
            path (str): Path to where the File is exported.

        Returns:
            bool: True if export was successful. Else False.
        """
        derivatives = self.get_project().get_derivatives()
        for l in label:
            try:
                derivative = derivatives[l]
                json_file = json.dumps(
                    {
                        "label": l,
                        "functional_expression": derivative.__dict__
                    }
                )
                super().export(ConfigFiles.PATH_JSON_FILE %
                               (path, label), file_content=json_file)
            except KeyError as error:
                return error

    def import_(self, path: str) -> bool:
        """Function to import a derivative.

        Args:
            path (str): Path to the File.

        Returns:
            bool: True if import was successful. Else False.
        """
        try:
            derivative = super().import_(path)
            self.add(derivative['label'],
                     derivative['functional_expression']['expression'])
            return True
        except OSError as os_error:
            raise OSError(
                ConfigErrorMessages.ERROR_MSG_IMPORT_PATH) from os_error
        except KeyError as key_error:
            raise KeyError(
                ConfigErrorMessages.ERROR_MSG_FILE_FORMAT_IMPORT_JSON) from key_error
