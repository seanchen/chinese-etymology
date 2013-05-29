#!/user/bin/python3
#coding=utf-8


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
    """
    The class for the normalized and structured data of http://www.chineseetymology.org/.
    Here normalization means a sequence of operations to each image including:
        chopping out unnecessary margin,
        resizing to 64x64,
        binarizing,
        vectorizing into a 4096-lengthed vector in row-major order.

    """

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

    def __init__(self, init_folder=None):
        if init_folder is not None:
            self.__IMAGE_WIDTH = 64
            self.__IMAGE_HEIGHT = 64
            bulk = list(ChineseEtymologyData.__get_member_generator(init_folder, self.__IMAGE_WIDTH, self.__IMAGE_HEIGHT))
            sample_count = len(bulk)

            self.__data = np.empty((sample_count,), dtype=[('Characters', '<U1'), ('Categories', '<U6'), ('FeatureMatrix', 'float', self.__IMAGE_WIDTH * self.__IMAGE_HEIGHT)])

            for i in range(sample_count):
                (self.__data['Characters'][i], self.__data['Categories'][i], self.__data['FeatureMatrix'][i,:]) = bulk[i]
        else:
            self.__IMAGE_WIDTH = None
            self.__IMAGE_HEIGHT = None
            self.__data = None

    @property
    def image_width(self):
        """
        Return the width of all images.
        """
        return self.__IMAGE_WIDTH

    @property
    def image_height(self):
        """
        Return the height of all images.
        """
        return self.__IMAGE_HEIGHT

    @property
    def data_frame(self):
        """
        Return the data frame consisting of characters, categories, and feature matrix.
        """
        return self.__data

    @property
    def characters(self):
        """
        Return the vector of characters that the images are corresponding to.
        """
        return self.__data['Characters']

    @property
    def categories(self):
        """
        Return the vector of categories that the images are corresponding to, in which each entry is one of 'bronze', 'lst', 'oracle', and 'seal'.
        """
        return self.__data['Categories']

    @property
    def feature_matrix(self):
        """
        Return the feature matrix, whose rows correspond to samples and columns correspond to pixels.
        """
        return self.__data['FeatureMatrix']

    @staticmethod
    def create_hdf5(gb2312_folder, gbk_folder, hdf5_dst):
        """
        Create a HDF5 file for both GB2312 character set and GBK character set, whose hierarchy is:
        /GB2312
            /Categories
            /Characters
            /FeatureMatrix
                attr: ImageHeight
                attr: ImageWidth
        /GBK
            /Categories
            /Characters
            /FeatureMatrix
                attr: ImageHeight
                attr: ImageWidth

        Keyword arguments:
        gb2312_folder   --  the folder that keeps images of GB2312 character set, which should be created from utils_fetch.fetch_all
        gbk_folder      --  the folder that keeps images of GBK character set, which should be created from utils_fetch.fetch_all
        hdf5_dst        --  the name/path of the output HDF5 file
        """
        with h5py.File(hdf5_dst, 'w') as hdf5_file:
            gb2312_group = hdf5_file.create_group("GB2312")
            gb2312 = ChineseEtymologyData(gb2312_folder)
            gb2312_characters = gb2312_group.create_dataset("Characters", gb2312.characters.shape, '|S2')
            gb2312_characters[...] = [char.encode('gb2312') for char in gb2312.characters]
            gb2312_categories = gb2312_group.create_dataset("Categories", gb2312.categories.shape, '|S6')
            gb2312_categories[...] = [cate.encode('utf8') for cate in gb2312.categories]
            gb2312_feature_matrix = gb2312_group.create_dataset("FeatureMatrix", gb2312.feature_matrix.shape, 'float')
            gb2312_feature_matrix[...] = gb2312.feature_matrix
            gb2312_feature_matrix.attrs["ImageWidth"] = gb2312.image_width
            gb2312_feature_matrix.attrs["ImageHeight"] = gb2312.image_height

            gbk_group = hdf5_file.create_group("GBK")
            gbk = ChineseEtymologyData(gbk_folder)
            gbk_characters = gbk_group.create_dataset("Characters", gbk.characters.shape, '|S2')
            gbk_characters[...] = [char.encode('gbk') for char in gbk.characters]
            gbk_categories = gbk_group.create_dataset("Categories", gbk.categories.shape, '|S6')
            gbk_categories[...] = [cate.encode('utf8') for cate in gbk.categories]
            gbk_feature_matrix = gbk_group.create_dataset("FeatureMatrix", gbk.feature_matrix.shape, 'float')
            gbk_feature_matrix[...] = gbk.feature_matrix
            gbk_feature_matrix.attrs["ImageWidth"] = gbk.image_width
            gbk_feature_matrix.attrs["ImageHeight"] = gbk.image_height

    @staticmethod
    def load_hdf5(hdf5_src, charset):
        """
        Create an ChineseEtymologyData object from an HDF5 file that is previously created by create_hdf5

        Keyword arguments:
        hdf5_src    --  the name/path of the input HDF5 file
        charset     --  the name of the group/character set from which one wants to load, should be either 'GB2312' or 'GBK' (case insensitive)
        """
        charset = charset.upper()
        if not (charset == 'GB2312' or charset == "GBK"):
            print('Unsupported character set.')
            return
        with h5py.File(hdf5_src, 'r') as hdf5_file:
            group = hdf5_file[charset]
            characters = group['Characters']
            categories = group['Categories']
            feature_matrix = group['FeatureMatrix']
            (sample_count, dimension) = feature_matrix.shape
            chinese_etymology_data = ChineseEtymologyData()
            chinese_etymology_data.__IMAGE_WIDTH = feature_matrix.attrs['ImageWidth']
            chinese_etymology_data.__IMAGE_HEIGHT = feature_matrix.attrs['ImageHeight']

            chinese_etymology_data.__data = np.empty((sample_count,), dtype=[('Characters', '<U1'),
                                                                             ('Categories', '<U6'),
                                                                             ('FeatureMatrix', 'float', chinese_etymology_data.__IMAGE_WIDTH * chinese_etymology_data.__IMAGE_HEIGHT)])

            chinese_etymology_data.__data['Characters'] = [char.decode(charset) for char in characters]
            chinese_etymology_data.__data['Categories'] = [cate.decode('utf8') for cate in categories]
            chinese_etymology_data.__data['FeatureMatrix'] = feature_matrix

            return chinese_etymology_data


