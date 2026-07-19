import unittest

from app.schemas.auth import RegisterUser
from app.services.auth import AuthService
from app.utils.exceptions import UserAlreadyExists


class FakeRepository:
    def __init__(self):
        self.users = {}

    async def get_by_email(self, email: str):
        return self.users.get(email)

    async def create(self, user):
        self.users[user.email] = user
        return user


class AuthServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_user_hashes_password_and_stores_display_name(self):
        repo = FakeRepository()
        service = AuthService(repo)

        credentials = RegisterUser(
            name="Ada", email="ada@example.com", password="secret123"
        )
        user = await service.create(credentials)

        self.assertEqual(user.email, credentials.email)
        self.assertEqual(user.display_name, credentials.name)
        self.assertNotEqual(user.password_hash, credentials.password)

    async def test_create_raises_when_email_already_exists(self):
        repo = FakeRepository()
        service = AuthService(repo)

        credentials = RegisterUser(
            name="Ada", email="ada@example.com", password="secret123"
        )
        await service.create(credentials)

        with self.assertRaises(UserAlreadyExists):
            await service.create(credentials)


if __name__ == "__main__":
    unittest.main()
