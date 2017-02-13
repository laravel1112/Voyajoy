import cloudinary
import cloudinary.uploader

NAME_CLOUDINARY = 'djrymcpim'
API_KEY = '593932199765412'
API_SECRET_SECRET = 'sLeeU6TolxkDn3gdKbTE7foye90'


def init(name=NAME_CLOUDINARY, key=API_KEY, secret=API_SECRET_SECRET):
    cloudinary.config(
        cloud_name=name,
        api_key=key,
        api_secret=secret
    )


init()


def delete_all():
    response = cloudinary.api.delete_all_resources()
    print response


def upload_image(image_link):
    response = cloudinary.uploader.upload(image_link)
    public_id = response['public_id']
    format = response['format']
    version = response['version']

    url = response['url']
    # cloudinary.uploader.destroy(public_id)

    return url


def upload_images(images_list):
    image_urls = list()
    for each in images_list:
        image_urls.append(upload_image(each))
    return image_urls
