from fastapi import File, UploadFile
from src.services.cloudinary_service import upload_avatar

@router.post("/avatar")
async def update_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """

    :param file:
    :param db:
    :param user:
    :return:
    """
    url = upload_avatar(file.file)
    user.avatar_url = url
    await db.commit()
    return {"avatar_url": url}
