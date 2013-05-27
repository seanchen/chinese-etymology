__author__ = 'Ziyuan'

import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imresize
import os
import pickle
import logging

_logger = logging.getLogger('data')
_logger.setLevel(logging.WARNING)

def _rgb2binary(rgb):
    (r, g, b) = np.rollaxis(rgb[...,:3], axis = -1)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _remove_margin(img):
    if img.ndim > 2:
        img =  _rgb2binary(img)
    is_white = np.array(img == 255)
    (n_row,n_col) = is_white.shape
    for i in range(n_row):
        row = is_white[i,:]
        if not all(row):
            top = i
            break
    for i in reversed(range(n_row)):
        row = is_white[i,:]
        if not all(row):
            bottom = i + 1
            break
    for j in range(n_col):
        col = is_white[:,j]
        if not all(col):
            left = j
            break
    for j in reversed(range(n_col)):
        col = is_white[:,j]
        if not all(col):
            right = j + 1
            break
    return img[top:bottom, left:right]


def _resize_image(img, width=64, height=64):
    return imresize(img,(width,height))


class ChineseEtymologyData:

    @staticmethod
    def __get_member_generator(init_folder, img_width, img_height):
        for character in os.listdir(init_folder):
            folder_lv1 = os.path.join(init_folder, character)
            if os.path.isdir(folder_lv1):
                for category in os.listdir(folder_lv1):
                    folder_lv2 = os.path.join(folder_lv1, category)
                    for img_file in os.listdir(folder_lv2):
                        img_path = os.path.join(folder_lv2, img_file)
                        # print('Reading ' + img_path)
                        try:
                            img = plt.imread(img_path)
                        except OSError as e:
                            _logger.error('%s (%s), removed.' % (str(e),img_path) )
                            os.remove(img_path)
                            continue
                        img = _resize_image(_remove_margin(_rgb2binary(img)), img_width, img_height)
                        img[np.where(img <= 127)] = 0
                        img[np.where(img > 127)] = 1
                        feature = np.reshape(img, np.size(img))
                        yield (character, category, feature)

    def __init__(self, init_folder):
        img_width = 64
        img_height = 64
        bulk = list(ChineseEtymologyData.__get_member_generator(init_folder, img_width, img_height))
        sample_count = len(bulk)

        self.characters = [None] * sample_count
        self.categories = [None] * sample_count
        self.feature_matrix = np.empty((sample_count, img_width * img_height))

        for i in range(sample_count):
            (self.characters[i], self.categories[i], self.feature_matrix[i,:]) = bulk[i]

    def save(self, dst):
        with open(dst, "wb") as dump_dst:
            pickle.dump(self, dump_dst)

    @staticmethod
    def load(src):
        with open(src, "rb") as dump_src:
            return pickle.load(dump_src)