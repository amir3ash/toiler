import sys
import uuid
from io import BytesIO

from PIL import Image
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import InMemoryUploadedFile

MAX_SIZE = 5 * 1024 * 1024  # max uploaded image size in MiB
EXPECTED_CONTENT_TYPE = ['jpeg', 'png']
CONTENT_TYPE_ERROR = 'Please use a JPEG or PNG image.'


class ImageValidationError(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def validate_image(image_file: InMemoryUploadedFile, max_img_size=MAX_SIZE, max_width=9000, max_height=9000) -> None:
    """
    Validates img parameters of image and raise `ImageValidationError`.

    :param max_height: maximum image height in pixels
    :param max_width: maximum image width in pixels
    :param image_file:
    :param max_img_size: maximum file size in Byte:
    :raise: ImageValidationError
    """
    try:
        # validate content type
        main, sub = image_file.content_type.split('/')
        if not (main == 'image' and sub in EXPECTED_CONTENT_TYPE):
            raise ImageValidationError(CONTENT_TYPE_ERROR)

        w, h = get_image_dimensions(image_file)

        # validate dimensions
        if w > max_width or h > max_height:
            raise ImageValidationError(
                'Please use an image that is {} x {} pixels or smaller.'.format(max_width, max_height))

        # validate file size
        if len(image_file) > max_img_size:
            raise ImageValidationError(
                'Avatar file size may not exceed {} Bytes ({} MiB).'.format(max_img_size, max_img_size / (2 << 20)))

    except AttributeError:
        """
        Handles case when we are updating the user profile
        and do not supply a new avatar
        """
        pass


def optimize_image(img_file):
    """
    Changes img format to **webp** and resize it.
    Returns new img with new random name.
    """
    image = Image.open(img_file)

    w = image.width
    h = image.height

    width_height = min(h, w)

    left = (w - width_height) // 2
    top = (h - width_height) // 2
    right = (w + width_height) // 2
    bottom = (h + width_height) // 2

    image = image.crop((left, top, right, bottom))

    if width_height > 360:
        image = image.resize((360, 360), Image.ANTIALIAS)

    output = BytesIO()

    image.save(output, 'WEBP', quality=50, optimize=True)
    output.seek(0)

    name = f'{uuid.uuid4().hex}.webp'

    return InMemoryUploadedFile(output, 'avatar', name, 'image/webp', sys.getsizeof(output), None)
