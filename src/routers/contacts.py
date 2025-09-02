from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.database import get_db
from src import crud
from src.schemas import ContactCreate, ContactRead, ContactUpdate
from src.auth import get_current_user
from src.models import User
from src.limiter import limiter

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post("/", response_model=ContactRead, status_code=201)
@limiter.limit("5/minute")
async def create_contact(
    request: Request,
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """

    :param request:
    :param contact:
    :param db:
    :param user:
    :return:
    """
    return await crud.create_contact(db, contact, user.id)


@router.get("/", response_model=List[ContactRead])
async def get_contacts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """

    :param db:
    :param user:
    :return:
    """
    return await crud.get_contacts(db, user.id)


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """

    :param contact_id:
    :param db:
    :param user:
    :return:
    """
    contact = await crud.get_contact(db, contact_id, user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """

    :param contact_id:
    :param contact_data:
    :param db:
    :param user:
    :return:
    """
    contact = await crud.update_contact(db, contact_id, contact_data, user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """

    :param contact_id:
    :param db:
    :param user:
    :return:
    """
    contact = await crud.delete_contact(db, contact_id, user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return None


@router.get("/search/", response_model=List[ContactRead])
async def search_contacts(
    query: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """

    :param query:
    :param db:
    :param user:
    :return:
    """
    return await crud.search_contacts(db, query or "", user.id)


@router.get("/birthdays/", response_model=List[ContactRead])
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """

    :param db:
    :param user:
    :return:
    """
    return await crud.get_upcoming_birthdays(db, user.id)
