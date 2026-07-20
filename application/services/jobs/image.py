from PIL import Image, ImageOps
import urllib.request
from io import BytesIO

import boto3
from configs import settings
from application.cel import celery


def _get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


@celery.task
def upload(space, path, image=None, url=None, is_async=True, make_thumbnails=True):

    s3 = _get_s3_client()
    bucket_name = space

    def make_thumb(image):
        im = Image.open(image)
        for size in [(400, 400), (150, 150)]:
            output = BytesIO()
            im2 = ImageOps.fit(im, size, Image.LANCZOS)
            im2.save(output, "JPEG")
            s3.put_object(
                Bucket=bucket_name,
                Key="thumbnails/%sx%s/%s" % (size[0], size[1], path),
                Body=output.getvalue(),
                ACL='public-read',
            )
            output.close()

    # save original img
    if image is None and url:
        fd = urllib.request.urlopen(url)
        image = BytesIO(fd.read())

    else:
        image = BytesIO(image)

    s3.put_object(
        Bucket=bucket_name,
        Key=path,
        Body=image.getvalue(),
        ACL='public-read',
    )

    # make thumbnails
    if make_thumbnails:
        make_thumb(image)

    image.close()
    orig_url = "http://assets.maybi.cn/%s" % path
    return orig_url


@celery.task
def make_thumbnails(space, path, url, is_async=True):

    s3 = _get_s3_client()
    bucket_name = space

    # save original img
    fd = urllib.request.urlopen(url)
    image = BytesIO(fd.read())

    im = Image.open(image)
    for size in [(480, 480), (180, 180)]:
        output = BytesIO()
        im2 = ImageOps.fit(im, size, Image.LANCZOS)
        im2.save(output, "JPEG")

        s3.put_object(
            Bucket=bucket_name,
            Key="post_thumbs/%sx%s/%s" % (size[0], size[1], path),
            Body=output.getvalue(),
            ACL='public-read',
        )
        output.close()


@celery.task
def save_avatar(space, path, url, save_original=False, is_async=True):

    s3 = _get_s3_client()
    bucket_name = space

    fd = urllib.request.urlopen(url)
    image = BytesIO(fd.read())

    # save original img
    if save_original:
        s3.put_object(
            Bucket=bucket_name,
            Key=path,
            Body=image.getvalue(),
            ACL='public-read',
        )

    im = Image.open(image)
    for size in [(200, 200), (80, 80)]:
        output = BytesIO()
        im2 = ImageOps.fit(im, size, Image.LANCZOS)
        im2.save(output, "JPEG")

        s3.put_object(
            Bucket=bucket_name,
            Key="avatar_thumbs/%sx%s/%s" % (size[0], size[1], path),
            Body=output.getvalue(),
            ACL='public-read',
        )
        output.close()
