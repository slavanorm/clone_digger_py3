"""doc"""


class MyException(Exception):
    """base exception"""

    msg = "MyException"

    def __str__(self):
        return self.msg


class ChildException1(MyException):
    """child exception 1"""

    def __init__(self, param):
        """
        Args:

            param (str): param
        """
        self.msg = f"{param} for child exception 1"


class ChildException2(MyException):
    """child exception 2"""

    def __init__(self, param):
        """
        Args:

            param (str): param
        """
        self.msg = f"{param} for child exception 2"
