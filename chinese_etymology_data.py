__author__ = 'Ziyuan'

import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imresize
import h5py
import os
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
                        try:
                            img = plt.imread(img_path)
                        except OSError as e:
                            _logger.error('%s (%s), removed.' % (str(e),img_path) )
                            os.remove(img_path)
                            continue
                        img = imresize(_remove_margin(_rgb2binary(img)), (img_width, img_height))
                        img[np.where(img <= 127)] = 0
                        img[np.where(img > 127)] = 1
                        feature = np.reshape(img, np.size(img))
                        yield (character, category, feature)

    def __init__(self, init_folder):
        self.__IMAGE_WIDTH = 64
        self.__IMAGE_HEIGHT = 64
        bulk = list(ChineseEtymologyData.__get_member_generator(init_folder, self.__IMAGE_WIDTH, self.__IMAGE_HEIGHT))
        sample_count = len(bulk)

        self.__data = np.empty((sample_count,), dtype=[('Characters', '<U1'), ('Categories', '<U6'), ('FeatureMatrix', 'float', self.__IMAGE_WIDTH * self.__IMAGE_HEIGHT)])

        for i in range(sample_count):
            (self.__data['Characters'][i], self.__data['Categories'][i], self.__data['FeatureMatrix'][i,:]) = bulk[i]

    @property
    def image_width(self):
        return self.__IMAGE_WIDTH

    @property
    def image_height(self):
        return self.__IMAGE_HEIGHT

    @property
    def data_frame(self):
        return self.__data

    @property
    def characters(self):
        return self.__data['Characters']

    @property
    def categories(self):
        return self.__data['Categories']

    @property
    def feature_matrix(self):
        return self.__data['FeatureMatrix']

    @staticmethod
    def create_hdf5(gb2312_folder, gbk_folder, dst):
        with h5py.File(dst, 'w') as hdf5_file:
            gb2312_group = hdf5_file.create_group("GB2312")
            gb2312 = ChineseEtymologyData(gb2312_folder)
            gb2312_group.create_dataset("ImageWidth", data=gb2312.image_width)
            gb2312_group.create_dataset("ImageHeight", data=gb2312.image_height)
            gb2312_characters = gb2312_group.create_dataset("Characters", gb2312.characters.shape, '|S2')
            gb2312_characters[...] = [char.encode('gb2312') for char in gb2312.characters]
            gb2312_categories = gb2312_group.create_dataset("Categories", gb2312.categories.shape, '|S6')
            gb2312_categories[...] = [cate.encode('utf8') for cate in gb2312.categories]
            gb2312_feature_matrix = gb2312_group.create_dataset("FeatureMatrix", gb2312.feature_matrix.shape, 'float')
            gb2312_feature_matrix[...] = gb2312.feature_matrix

            gbk_group = hdf5_file.create_group("GBK")
            gbk = ChineseEtymologyData(gbk_folder)
            gbk_group.create_dataset("ImageWidth", data=gbk.image_width)
            gbk_group.create_dataset("ImageHeight", data=gbk.image_height)
            gbk_characters = gbk_group.create_dataset("Characters", gbk.characters.shape, '|S2')
            gbk_characters[...] = [char.encode('gbk') for char in gbk.characters]
            gbk_categories = gbk_group.create_dataset("Categories", gbk.categories.shape, '|S6')
            gbk_categories[...] = [cate.encode('utf8') for cate in gbk.categories]
            gbk_feature_matrix = gbk_group.create_dataset("FeatureMatrix", gbk.feature_matrix.shape, 'float')
            gbk_feature_matrix[...] = gbk.feature_matrix

    @staticmethod
    def load_hdf5(src):
        pass