import unittest
from unittest.mock import AsyncMock, MagicMock
from datetime import date

from src import crud
from src.models import Contact
from src.schemas import ContactCreate, ContactUpdate


class TestRepositoryContacts(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = AsyncMock()
        self.user_id = 1

    async def test_create_contact(self):
        contact_data = ContactCreate(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="987654321",
            birthday=date(1995, 5, 5),
            extra_info="Colleague"
        )
        result = await crud.create_contact(self.session, contact_data, self.user_id)
        self.assertEqual(result.first_name, "Alice")
        self.session.add.assert_called_once()

    async def test_get_contacts(self):
        mock_contact = Contact(id=1, first_name="John", last_name="Doe", user_id=self.user_id)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_contact]
        self.session.execute.return_value = mock_result

        result = await crud.get_contacts(self.session, self.user_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    async def test_update_contact(self):
        mock_contact = Contact(id=1, first_name="Old", user_id=self.user_id)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_contact
        self.session.execute.return_value = mock_result

        update_data = ContactUpdate(first_name="New")

        result = await crud.update_contact(self.session, 1, update_data, self.user_id)

        self.assertEqual(result.first_name, "New")

    async def test_delete_contact(self):
        mock_contact = Contact(id=1, first_name="Delete", user_id=self.user_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_contact
        self.session.execute.return_value = mock_result

        result = await crud.delete_contact(self.session, 1, self.user_id)

        self.assertEqual(result.first_name, "Delete")
        self.session.delete.assert_called_once_with(mock_contact)


if __name__ == "__main__":
    unittest.main()
