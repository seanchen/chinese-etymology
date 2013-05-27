__author__ = 'Ziyuan'

import _retrieve_images



def fetch_character_images_from_website(charset, character_count=None, thread_count=5):
    _retrieve_images._fetch_all(charset, character_count, thread_count)

fetch_character_images_from_website.__doc__ = _retrieve_images.__doc__