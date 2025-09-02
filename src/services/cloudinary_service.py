import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_avatar(file):
    """

    :param file:
    :return:
    """
    result = cloudinary.uploader.upload(file, folder="avatars")
    return result["secure_url"]
