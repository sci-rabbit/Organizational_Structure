from exceptions.base import BaseAppException


class DepartmentAlreadyExists(BaseAppException):
    status_code = 409
    detail = "Department with same parent_id already exists"


class DepartmentParentConflict(BaseAppException):
    status_code = 400
    detail = "Department can't be his own parent."


class DepartmentNotFound(BaseAppException):
    status_code = 404
    detail = "Department doesn't exist."


class DepartmentReassignConflict(BaseAppException):
    status_code = 400
    detail = "Cannot reassign employees to the department being deleted."