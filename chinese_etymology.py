__author__ = 'Ziyuan'

import _retrieve_images
import _prepare_feature_matrix


def fetch_character_images_from_website(charset, character_count=None, thread_count=5):
    _retrieve_images.fetch_all(charset, character_count, thread_count)
fetch_character_images_from_website.__doc__ = _retrieve_images.__doc__


def create_data_object_from_folder(init_folder):
    return _prepare_feature_matrix.ChineseEtymologyData(init_folder)

def load_data_object_from_file(src):
    return _prepare_feature_matrix.ChineseEtymologyData.load(src)
