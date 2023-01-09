from rest_framework import status
from rest_framework.exceptions import APIException

class NotAllowedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You are not allowed to perform this operation."
    default_code = None

class ExistsError(APIException):
    status_code  = status.HTTP_409_CONFLICT
    message      = "This data already exists."
    def __init__(self, detail=message):
        ExistsError.message = detail

class NotExistsError(APIException):
    status_code  = status.HTTP_404_NOT_FOUND
    message      = "This data does not exist."
    def __init__(self, detail=message):
        NotExistsError.message = detail

class UnauthorizedError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "You are not allowed to perform this operation."
    default_code = None
