Chinese Etymology Classifer
=================

A would-be classifier for character images on [Chinese Etymology](http://www.chineseetymology.org/).

Data
-----------------

### Raw data ###


The images fetched from the website can be downloaded at [ChineseEtymologyData.7z](https://dl.dropboxusercontent.com/u/1335302/ChineseEtymologyData.7z) (32.1MB).

See `utils_fetch.py` for further detail.

### Normalized data ###

The normalized and structured data in HDF5 can be downloaded at [NormalizedChineseEtymologyData.7z](https://dl.dropboxusercontent.com/u/1335302/NormalizedChineseEtymologyData.7z) (32.2MB).

Normalization means a sequence of operations to each image including: chopping out unnecessary margin, resizing to 64x64, binarizing, and vectorizing into a 4096-lengthed vector in row-major order.

See `chinese_etymology_data.py` for further detail.

##### HDF5 file hierarchy #####
    
>       /GB2312
>           /Categories
>           /Characters
>           /FeatureMatrix
>               attr: ImageHeight
>               attr: ImageWidth
>       /GBK
>           /Categories
>           /Characters
>           /FeatureMatrix
>               attr: ImageHeight
>               attr: ImageWidth

Special thanks
-----------------

Thanks Uncle Hanzi (汉字叔叔) for hosting the website. Please consider [donation](http://www.chineseetymology.org/)!
