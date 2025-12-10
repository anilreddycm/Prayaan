from django import template
from django.conf import settings
import os

register = template.Library()

@register.simple_tag
def car_image_url(car):
    """Return the best URL for a car image.
    Priority:
      1. car.image if set and file exists
      2. media/cars matching registration_number or category (case-insensitive substring)
      3. first matching file in media/cars containing category
      4. static placeholder or remote fallback
    """
    # 1) car.image
    try:
        if getattr(car, 'image') and car.image:
            # car.image.name is relative to MEDIA_ROOT
            path = os.path.join(settings.MEDIA_ROOT, car.image.name)
            if os.path.exists(path):
                return settings.MEDIA_URL + car.image.name
    except Exception:
        pass

    # 2) try match registration_number or category to filenames in media/cars
    media_cars_dir = os.path.join(settings.MEDIA_ROOT, 'cars')
    if os.path.isdir(media_cars_dir):
        candidates = []
        if getattr(car, 'registration_number', None):
            candidates.append(car.registration_number)
        if getattr(car, 'category', None):
            candidates.append(car.category)

        # normalize candidates
        norm_cands = [c.lower().replace(' ', '_') for c in candidates if c]

        try:
            for fname in os.listdir(media_cars_dir):
                lname = fname.lower()
                for cand in norm_cands:
                    if cand and cand in lname:
                        return settings.MEDIA_URL + 'cars/' + fname
            # If none matched, try a looser contains on category words
            for fname in os.listdir(media_cars_dir):
                lname = fname.lower()
                for cat in norm_cands:
                    parts = cat.split('_')
                    for p in parts:
                        if p and p in lname:
                            return settings.MEDIA_URL + 'cars/' + fname
        except Exception:
            pass

    # 3) fallback to static placeholder
    static_placeholder = getattr(settings, 'STATIC_URL', '/static/') + 'app/images/default_car.png'
    return static_placeholder
