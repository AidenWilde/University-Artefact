
class Error(Exception):
    def __init__(self, errorMessage):
        self.errorMessage = errorMessage

    def GetErrorMessage(self):
        return self.errorMessage
