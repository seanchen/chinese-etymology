#!/usr/bin/python
#coding=utf-8
__author__ = 'Ziyuan'

import os
import logging
import itertools
import shutil
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen
from urllib.request import urlretrieve
import workerpool
from lxml.cssselect import CSSSelector
from lxml.html import fromstring
from datetime import datetime


def get_gb2312_characters():
    # equivalent to level 2 of GBK
    higher_range = range(0xb0, 0xf7 + 1)
    lower_range = range(0xa1, 0xfe + 1)
    for higher in higher_range:
        for lower in lower_range:
            encoding = (higher << 8) | lower
            try:
                yield encoding.to_bytes(2, byteorder='big').decode(encoding='gb2312')
            except UnicodeDecodeError:
                pass


def get_gbk_characters():
    # equivalent to the two-byte part of GB18030-2005
    higher_range_level2 = range(0xb0, 0xf7 + 1)
    lower_range_level2 = range(0xa1, 0xfe + 1)
    higher_range_level3 = range(0x81, 0xa0 + 1)
    lower_range_level3 = itertools.chain(range(0x40, 0x7f), range(0x7f + 1, 0xfe + 1))
    higher_range_level4 = range(0xaa, 0xfe + 1)
    lower_range_level4 = itertools.chain(range(0x40, 0x7f), range(0x7f + 1, 0xa0 + 1))

    gbk_ranges = {2: (higher_range_level2, lower_range_level2),
                  3: (higher_range_level3, lower_range_level3),
                  4: (higher_range_level4, lower_range_level4)}

    for level in [2, 3, 4]:
        (higher_range, lower_range) = gbk_ranges[level]
        for higher in higher_range:
            for lower in lower_range:
                encoding = (higher << 8) | lower
                yield encoding.to_bytes(2, byteorder='big').decode(encoding='gbk')


# def get_gb18030_2005_characters():
#     return []


def fetch_img_of_character(char, root_folder, file_logger=None):
    root_char = os.path.join(root_folder, char)
    if not os.path.exists(root_char):
        os.makedirs(root_char)

    url_root = 'http://www.chineseetymology.org'
    url = 'http://www.chineseetymology.org/CharacterEtymology.aspx?characterInput=' \
          + quote(char)

    attempts = 0
    max_attempts = 20
    while attempts < max_attempts:
        try:
            page = urlopen(url).read().decode('utf8')
            break
        except URLError as e:
            attempts += 1
            msg = '\"%s\" occurs when opening page %s. Retrying.' % (e.reason, url)
            if file_logger is not None:
                file_logger.warning(msg)
            else:
                logging.warning(msg)

    if attempts == max_attempts:
        msg = 'Max attempts reached. Fail to open page ' + url
        if file_logger is not None:
            file_logger.error(msg)
        else:
            logging.error(msg)
        return

    page = fromstring(page)

    seal_selector = CSSSelector("span#SealImages img")
    lst_selector = CSSSelector("span#LstImages img")
    bronze_selector = CSSSelector("span#BronzeImages img")
    oracle_selector = CSSSelector("span#OracleImages img")

    seal_img = [img.get('src') for img in seal_selector(page)]
    lst_img = [img.get('src') for img in lst_selector(page)]
    bronze_img = [img.get('src') for img in bronze_selector(page)]
    oracle_img = [img.get('src') for img in oracle_selector(page)]

    all_img = {"seal": seal_img, "lst": lst_img, "bronze": bronze_img, "oracle": oracle_img}

    for folder in all_img.keys():
        folder_full = os.path.join(root_char, folder)
        if not os.path.exists(folder_full):
            os.makedirs(folder_full)
        for img_src in all_img[folder]:
            (_, gif_name) = os.path.split(img_src)
            gif_full_path = os.path.join(folder_full, gif_name)
            if not os.path.exists(gif_full_path):
                img_url = url_root + img_src
                attempts = 0;
                while attempts < max_attempts:
                    try:
                        urlretrieve(img_url, gif_full_path)
                        break
                    except TimeoutError:
                        msg = 'Time out when downloading %s to %s. Retrying.' % (img_url, gif_full_path)
                        if file_logger is not None:
                            file_logger.warning(msg)
                        else:
                            logging.warning(msg)
                    except URLError as e:
                        msg = '\"%s\" occurs when downloading %s to %s. Retrying.' % (
                            e.reason, img_url, gif_full_path)
                        if file_logger is not None:
                            file_logger.warning(msg)
                        else:
                            logging.warning(msg)

                if attempts == max_attempts:
                    msg = 'Max attempts reached. Fail to download image ' + img_url
                    if file_logger is not None:
                        file_logger.error(msg)
                    else:
                        logging.error(msg)


def remove_empty_characters(root_folder, not_analyzed_file_name):
    to_be_deleted = dict()
    for char in os.listdir(root_folder):
        char_path = os.path.join(root_folder, char)

        # from http://stackoverflow.com/a/1392549/688080
        size = sum(os.path.getsize(os.path.join(dir_path, file_name)) for (dir_path, dir_names, file_names) in
                   os.walk(char_path) for file_name in file_names)

        if size == 0:
            to_be_deleted[char_path] = char
    with open(not_analyzed_file_name, "w") as not_analyzed:
        for folder in to_be_deleted.keys():
            not_analyzed.write(to_be_deleted[folder])
            shutil.rmtree(folder)


def fetch_all(save_to_folder, charset="gb2312", count=None, pool_size=5):
    """ Fetch all images of characters in character set GB2312 or GBK from http://www.chineseetymology.org/

    Keyword arguments:
    save_to_folder  --  the folder that you want to store all the images
    charset         --  the character set in used; should be 'GB2312' or 'GBK'
    count           --  number of characters to fetch
    pool_size       --  number of threading for downloading
    """

    not_analyzed_file_name = os.path.join(save_to_folder, "not_analyzed.txt")
    if os.path.exists(not_analyzed_file_name):
        os.remove(not_analyzed_file_name)
    charset = charset.lower()
    if charset == "gb2312":
        characters = get_gb2312_characters()
    elif charset == "gbk":
        characters = get_gbk_characters()
    # elif charset == "gb18030":
    #     characters = get_gb18030_2005_characters()
    else:
        print("Only \"GB2312\" and \"GBK\" are accepted")
        return

    if count is not None:
        characters = itertools.islice(characters, count)

    modified_time = lambda f: os.stat(os.path.join(save_to_folder, f)).st_mtime

    downloaded = sorted(os.listdir(save_to_folder), key=modified_time)
    del downloaded[-(2*pool_size):]
    downloaded = {char: 1 for char in downloaded}
    characters = itertools.filterfalse(lambda char: char in downloaded, characters)

    log_file_name = '{:%Y%m%d%H%M%S}'.format(datetime.now()) + '.log'
    logger = logging.getLogger("fetch")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler(log_file_name, "w"))

    pool = workerpool.WorkerPool(size=pool_size)
    pool.map(fetch_img_of_character, characters, itertools.repeat(save_to_folder), itertools.repeat(logger))
    pool.shutdown()
    pool.wait()

    remove_empty_characters(save_to_folder, not_analyzed_file_name)