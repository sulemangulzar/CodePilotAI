from fastapi import HTTPException, status


class UserAlreadyExists(HTTPException):
    def __init__(self, detail="User with this email already exists!"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)
