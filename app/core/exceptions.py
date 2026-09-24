class AppException(Exception):
    pass


class EmailAlreadyExists(AppException):
    def __init__(self, email: str):
        self.email = email


class UsernameAlreadyExists(AppException):
    def __init__(self, username: str):
        self.username = username