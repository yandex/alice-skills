GEOLOCATION_ALLOWED = 'Geolocation.Allowed'
GEOLOCATION_REJECTED = 'Geolocation.Rejected'


def image_gallery(image_ids): 
    items = [{'image_id': image_id} for image_id in image_ids]
    return {
        'type': 'ImageGallery',
        'items': items,
    }


def button(title, payload=None, url=None, hide=False):
    button = {
        'title': title,
        'hide': hide,
    }
    if payload is not None:
        button['payload'] = payload
    if url is not None:
        button['url'] = url
    return button


def has_location(event):
    return event['session'].get('location') is not None
