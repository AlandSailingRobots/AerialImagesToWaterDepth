from data_resources import fileToObjects, DataSourcesTypes
from map_based_resources import point, singleTile, mapResources
import pandas as pd
import numpy as np
import cv2
import mahotas
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.image import extract_patches_2d
from PIL import ImageStat, Image
from sklearn.preprocessing import Normalizer, MinMaxScaler, StandardScaler
from sklearn.decomposition import PCA
from sklearn import linear_model
from skimage.feature import greycomatrix, greycoprops, shape_index
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

np.seterr(divide='ignore', invalid='ignore')


def convert_and_correct_images_size(images):
    previous_image_size = None
    resized = []
    for image in images:
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        if previous_image_size is not None and previous_image_size != image.size:
            image = image.resize(previous_image_size)
        previous_image_size = image.size
        resized.append(image)
    return resized


def fd_hu_moment(image):
    image = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
    feature = cv2.HuMoments(cv2.moments(image))
    return feature


def fd_haralick(image):  # convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
    # compute the haralick texture feature vector
    haralick = mahotas.features.haralick(gray).mean(axis=0)
    return haralick


def fd_histogram(image, bins=16, color_convert=cv2.COLOR_RGBA2BGR):
    # convert the image to HSV color-space
    image = cv2.cvtColor(image, color_convert)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # compute the color histogram
    hist = cv2.calcHist([image], [0, 1, 2], None, [bins, bins, bins], [0, 256, 0, 256, 0, 256])
    # normalize the histogram
    cv2.normalize(hist, hist)
    # return the histogram
    return hist


def fd_histograms(images):
    hstacked = []
    for image in images:
        hstacked.append(fd_histogram(np.array(image)))
    return np.array(hstacked)


def fd_hu_moments(images):
    hstacked = []
    for image in images:
        hstacked.append(fd_hu_moment(np.array(image)))
    return np.array(hstacked)


def fd_haralicks(images):
    hstacked = []
    for image in images:
        hstacked.append(fd_haralick(np.array(image)))
    return np.array(hstacked)


def extract_patches(image, patch_size=2):
    return extract_patches_2d(image, (patch_size, patch_size))


def fd_(image):
    fd_histo = fd_histogram(image)
    fd_har = fd_haralick(image)
    fd_hu = fd_hu_moment(image)
    #     print(fd_histo.shape,fd_har.shape,fd_hu.shape)
    return np.hstack([fd_histo.ravel(), fd_har, fd_hu])


def fd_images(images):
    hstacked = []
    for image in images:
        hstacked.append(fd_(np.array(image)))
    return np.array(hstacked)


def equalize_hist(img, return_merge=True):
    img_tuple = cv2.split(img)
    for i in range(len(img_tuple)):
        cv2.equalizeHist(img_tuple[i], img_tuple[i])
    if return_merge:
        return cv2.merge(img_tuple)
    else:
        return img_tuple


def get_shapes_index(images_list):
    shapes = []
    for image in images_list:
        shapes_single = []
        bands = list(image.split())
        for band in bands:
            band = cv2.bilateralFilter(np.array(band), 20, 200, 200)
            shape = shape_index(band)
            np.nan_to_num(shape, copy=False)
            shapes_single.append(shape)
        shapes.append(np.array(shapes_single).ravel())
    return np.array(shapes)


def convert_and_func(func, img, return_image=False, return_merge=True, ccv_1=cv2.COLOR_RGBA2BGRA,
                     ccv_2=cv2.COLOR_BGRA2RGBA):
    img_converted = cv2.cvtColor(np.array(img), ccv_1)
    #     img.close()
    returned = func(img_converted, return_merge)
    if return_image:
        returned = cv2.cvtColor(returned, ccv_2)
        return Image.fromarray(returned), returned
    else:
        return returned


def get_stats(resized, equalize=False, return_images=False):
    method_dict = dict()
    equalized_images = []
    for image in resized:
        if equalize:
            eq, cv_ = convert_and_func(equalize_hist, image, return_image=True)
            stat_ = ImageStat.Stat(eq)
            equalized_images.append(eq)
        else:
            stat_ = ImageStat.Stat(image)
        for method in dir(stat_):
            if not method.startswith('_get'):
                continue
            attribute = method.split('_get')[1]
            result = np.array(getattr(stat_, method)())
            if isinstance(result[0], tuple):
                for i in range(len(result)):
                    result[i] = list(result[i])
            if attribute not in method_dict:
                method_dict[attribute] = np.array(result)
            else:
                nan_arr = np.argwhere(np.isnan(result))
                if (len(nan_arr)) > 0:
                    print(nan_arr)
                method_dict[attribute] = np.vstack((method_dict[attribute], result))

    full = np.empty((0,))
    for key in method_dict.keys():
        full = np.concatenate((method_dict[key].ravel(), full))
    if return_images:
        return full, equalized_images
    return full


def GLCM_textures(images_list, return_np=True):
    GLCM_properties = {'contrast': [],
                       'dissimilarity': [],
                       'homogeneity': [],
                       'energy': [],
                       'correlation': [],
                       'ASM': []}
    index = 0
    for image in images_list:
        for image_band in image.split():
            distance = (image.size[0]) // 8
            glcm = greycomatrix(np.array(image_band), [distance], [0], 256)
            for value in GLCM_properties.keys():
                result = greycoprops(glcm, value).ravel()
                if len(GLCM_properties[value]) <= index:
                    GLCM_properties[value].append(np.array(result))
                else:
                    GLCM_properties[value][index] = np.vstack((GLCM_properties[value][index], result))
        index += 1
    matrix = []
    for key in GLCM_properties.keys():
        array = np.array(GLCM_properties[key])
        GLCM_properties[key] = array
        matrix.append(array)
    if return_np:
        return np.array(matrix)
    else:
        return GLCM_properties


def get_raw_images(resized):
    np_list = []
    for image in resized:
        np_list.append(np.array(image).flatten())
    return np.array(np_list)


def get_features_and_labels(df, source, tile_round=1, level=15, features_to_be_added=[1, 2, 3, 4, 5, 6, 7, 8, 9],
                            specific=None,
                            indexes=None):
    mapresource = mapResources.MapResources()
    labels = list()
    features = list()
    df.reset_index(drop=True, inplace=True)
    count = 0
    for row in df.itertuples():
        labels.append(round(float(row.height), 2))
        coordinate = point.DataPoint(row.latitude,
                                     row.longitude,
                                     source['coordinate_system'],
                                     level)
        coordinate_tile = singleTile.get_image_and_plot(coordinate, mapresource, specific=specific,
                                                        show=False)
        if indexes is None:
            images = coordinate_tile.get_cropped_images(tile_round)
        else:
            images = []
            for index in indexes:
                images.append(coordinate_tile.get_cropped_image_single(tile_round))
        resized = convert_and_correct_images_size(images, indexes)
        stats_eq, eq_images = get_stats(resized, equalize=True, return_images=True)
        result_methods = [fd_haralicks, fd_histograms, fd_hu_moments, get_shapes_index, get_raw_images, GLCM_textures,
                          stats_eq, get_stats, GLCM_textures, get_raw_images, get_shapes_index]
        stack = [
            np.array([row.longitude, row.latitude])
        ]
        for i in features_to_be_added:
            if i <= 5:
                result = result_methods[i](resized).ravel()
            elif i >= 7:
                result = result_methods[i](eq_images).ravel()
            else:
                result = result_methods[i].ravel()
            stack.append(result)
        stacked = np.hstack(stack)
        features.append(stacked)

        for image in images:
            if image is not None:
                image.close()
        if count % 10 == 0:
            mapresource.clear_images()
        count += 1
    n_samples = (len(features))
    features = np.array(features)
    if features.shape != (n_samples, -1):
        features = features.reshape((n_samples, -1))
    #     print(features.shape)
    return features, np.array(labels)


def preprocess(transformers, train_x):
    for transformer in transformers[1:]:
        train_x = transformer.fit_transform(train_x)
    return train_x


def preprocessing(transformers, train_x, test_x):
    for transformer in transformers[1:]:
        transformer.fit(train_x)
        train_x = transformer.transform(train_x)
        test_x = transformer.transform(test_x)
    return train_x, test_x


def get_train_test(features, labels):
    t_t = train_test_split(features, labels)
    return t_t


sources = fileToObjects.get_data(DataSourcesTypes.DataSourceEnum.csv)

highest_score = 0
feature_list = [i for i in range(9)]
index_list = [i for i in range(7)]
clf = linear_model.SGDRegressor(loss='epsilon_insensitive', learning_rate='adaptive', eta0=0.1)
transformers = [PCA(100), MinMaxScaler(), Normalizer(), StandardScaler()]

step = 0
steps = 100

from joblib import dump, load

specific = {"webmap_name": "ava",
            "layer_name": "ava_normal_color"}
level = 15
size = 2
save_string = '{0}{1}.joblib'.format(specific['webmap_name'], specific["layer_name"])
if fileToObjects.check_path(save_string) is None:
    df = fileToObjects.open_xyz_file_as_panda(sources[0])
    for r in range(step, steps):
        print(r)
        sample = df.sample(100)
        df = df.drop(sample.index)
        features, labels = get_features_and_labels(sample, sources[0], size, level=level,
                                                   features_to_be_added=feature_list,
                                                   specific=specific,
                                                   indexes=[6])
        X = preprocess(transformers, features)
        clf.partial_fit(X, labels)

    dump(clf, save_string)
else:
    clf = load(save_string)
df = fileToObjects.open_xyz_file_as_panda(sources[1])

sample = df.sample(int(100 * steps / 4))
df = df.drop(sample.index)
features, labels = get_features_and_labels(sample, sources[0], size, level=level, features_to_be_added=feature_list,
                                           specific=specific,
                                           indexes=[6])
X = preprocess(transformers, features)
Y = clf.predict(X)
r2_ = r2_score(labels, Y)
mae = mean_absolute_error(labels, Y)
rms = mean_squared_error(labels, Y)
# bin_accuracy = accuracy_score(labels, Y)
print(r2_)
print(mae)
print(rms)

data_ = [r2_, mae, rms]
data_.insert(0, specific["webmap_name"])
data_.insert(1, specific["layer_name"])

results = pd.DataFrame(data=[data_],
                       columns=['webmap', 'layer', 'r2', 'mae', 'rms'])
results.to_csv('results.csv', mode='a', header=True, index=False)
