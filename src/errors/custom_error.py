class CustomError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.message

    def res(self):
        data = {"success": False,
                "error": {
                    "message": self.message,
                }}
        return data, self.status_code
