from sqlalchemy.future import select
from sqlalchemy import or_
from src.models import Contact
from src.schemas import ContactCreate, ContactUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta


async def create_contact(db: AsyncSession, contact: ContactCreate, user_id: int):
    """

    :param db:
    :param contact:
    :param user_id:
    :return:
    """
    db_contact = Contact(**contact.model_dump(), user_id=user_id)
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


async def get_contacts(db: AsyncSession, user_id: int):
    """

    :param db:
    :param user_id:
    :return:
    """
    result = await db.execute(select(Contact).where(Contact.user_id == user_id))
    return result.scalars().all()


async def get_contact(db: AsyncSession, contact_id: int, user_id: int):
    """

    :param db:
    :param contact_id:
    :param user_id:
    :return:
    """
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_contact(db: AsyncSession, contact_id: int, contact_data: ContactUpdate, user_id: int):
    """

    :param db:
    :param contact_id:
    :param contact_data:
    :param user_id:
    :return:
    """
    db_contact = await get_contact(db, contact_id, user_id)
    if db_contact:
        for key, value in contact_data.dict(exclude_unset=True).items():
            setattr(db_contact, key, value)
        await db.commit()
        await db.refresh(db_contact)
    return db_contact


async def delete_contact(db: AsyncSession, contact_id: int, user_id: int):
    """

    :param db:
    :param contact_id:
    :param user_id:
    :return:
    """
    db_contact = await get_contact(db, contact_id, user_id)
    if db_contact:
        await db.delete(db_contact)
        await db.commit()
    return db_contact


async def search_contacts(db: AsyncSession, query: str, user_id: int):
    """

    :param db:
    :param query:
    :param user_id:
    :return:
    """
    result = await db.execute(
        select(Contact).where(
            Contact.user_id == user_id,
            or_(
                Contact.first_name.ilike(f"%{query}%"),
                Contact.last_name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%"),
            )
        )
    )
    return result.scalars().all()


async def get_upcoming_birthdays(db: AsyncSession, user_id: int):
    """

    :param db:
    :param user_id:
    :return:
    """
    today = date.today()
    next_week = today + timedelta(days=7)

    result = await db.execute(select(Contact).where(Contact.user_id == user_id))
    contacts = result.scalars().all()

    upcoming = []
    for contact in contacts:
        if not contact.birthday:
            continue
        birthday_this_year = contact.birthday.replace(year=today.year)
        if birthday_this_year < today:
            birthday_this_year = contact.birthday.replace(year=today.year + 1)
        if today <= birthday_this_year <= next_week:
            upcoming.append(contact)
    return upcoming
