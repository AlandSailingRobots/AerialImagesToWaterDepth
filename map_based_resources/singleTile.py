#!/usr/bin/env python
# coding: utf-8

# In[1]:


from data_resources import fileToObjects
from map_based_resources import point, mapResources, transformObjects
import time

# ## Experimental Testing for getting photo's out of multiple WMTS servers.
# This Notebook experiments with a way  to get photo's as a datasource to later integrate it into the SailingRobots
# Website.
# 
# To have the webmap tile services as an object we first get configuration from the json file. In this is the url of
# the webmap and the name etc. This variable is then initiated so that we can continue using it further the in the
# code and reduce unnecessary objects.
# 
# The static variables like the standardized rendering pixel size is also available in the json and set globally.

# In[2]:

standardized_rendering_pixel_size = None
only_save = False
count = 0


# ## Calculate the position of the coordinate in WMTS
# By using the Webmap tile matrix we can calculate the position of where the coordinate on the whole map. 
# 
# This is done by the following formula's:
# $height = \frac{\text{matrix top left corner height}\;-\; longitude}{scale \;\times\; pixel_size \;\times\; \text{
# length of matrix}}
# $ and  $width = \frac{latitude \;-\; \text{matrix top left corner width}}{scale \;\times\; pixel_size
# \;\times\;\text{width of matrix}}$
# 
# The result is decimal number and the rows and columns are only whole numbers. the integer part of the results are
# used for the columns and the fractional parts are used to calculate the position on the image itself. the formula
# for that is $position = image size \;\times\; \text{fractional parts of height or width}$

# In[3]:


def calculated_width(coordinates, matrix):
    return (coordinates[0] - matrix.topleftcorner[0]) / (
            matrix.tilewidth * standardized_rendering_pixel_size * matrix.scaledenominator)


def calculated_height(coordinates, matrix):
    return (matrix.topleftcorner[1] - coordinates[1]) / (
            matrix.tileheight * standardized_rendering_pixel_size * matrix.scaledenominator)


def position_in_image(matrix_tile_size, value_part):
    return matrix_tile_size * value_part


# ## Transform coordinate systems
# Because there are different coordinates systems used it is necessary to convert them to the correct format. If
# convert has a value it will convert it from that value to the Finnish System(ETRS-TM35FIN) als know as EPSG:3067.
# The given input can be done from the `data_sources.json` or from `coordinates.json` and then will be parsed to the
# correct system if an other EPSG code is given.

# In[4]:


def get_value_and_value_image(matrix, point_, width=False):
    finnish_coordinates = point_.convert_coordinate_systems()
    if width:
        calculated = calculated_width
        matrix_tile_size = matrix.tilewidth
    else:
        calculated = calculated_height
        matrix_tile_size = matrix.tileheight

    value, value_part = transformObjects.split_part_and_whole(calculated(finnish_coordinates, matrix))
    return value, position_in_image(matrix_tile_size, value_part)


def get_single_height_width(matrix, point_):
    height, height_in_image = get_value_and_value_image(matrix, point_)
    width, width_in_image = get_value_and_value_image(matrix, point_, width=True)
    pixel_size = matrix.scaledenominator * standardized_rendering_pixel_size
    return height, width, height_in_image, width_in_image, pixel_size


# ## Get the matrix at a specific level
# The tileset contains multiple levels and has a matrix on each level. This function returns the matrix at a certain
# level.

# In[5]:


def get_matrix_at_level(wmts, level):
    tileset = wmts.tile_service.tilematrixsets[wmts.set_name]
    tile_matrix_keys = list(tileset.tilematrix.keys())
    return tileset.tilematrix[tile_matrix_keys[level]]


# ## Get the desired level in a layer
# Sometimes the level has a special name and is not in this specific level. So then we change the name to the correct
# setting and perhaps go up a few level's. This makes sure that we get an image which contains the correct point.
# This data is also returned in the end so that levels that are not similar can be filtered out as well. this
# `special_level` option can be set in the `wmts_config.json` because this is a layer properties.

# In[6]:


def set_level(tile_matrix_set_name, level, special_level):
    if special_level:
        return '{0}:{1}'.format(tile_matrix_set_name, level)
    else:
        return '{0}'.format(level)


def get_tile_level(wmts, layer):
    tms = wmts.tile_service.contents[layer.layer]
    tile_level = set_level(wmts.set_name, layer.level, wmts.special_level)
    limits = tms.tilematrixsetlinks[wmts.set_name].tilematrixlimits
    while tile_level not in limits and len(limits) > 0:
        layer.level -= 1
        tile_level = set_level(wmts.set_name, layer.level, wmts.special_level)
    layer.tile_level = tile_level


# ## Dealing with split up layers
# Sometimes to have a better resolution of the images, the map is split up in the different tile matrix widths. This
# then has an extension of 0 to 9. To execute this function `split` has to be in the `wmts_config.json` file for this
# specific layer. the generator function first looks for layers that are similar to the base layer but not the
# original layer.

# In[7]:


def check_fit(wmts, specified_map_layer_split, tile_level, row, column):
    tms = wmts.tile_service.contents[specified_map_layer_split]
    limits = tms.tilematrixsetlinks[wmts.set_name].tilematrixlimits[tile_level]
    return (limits.mintilerow <= row <= limits.maxtilerow) and (limits.mintilecol <= column <= limits.maxtilecol)


def get_specified_map_layer_if_split_up(wmts, layer_obj, row, column):
    wmts_ = wmts.tile_service
    specified_map_layer = layer_obj.layer

    if layer_obj.already_splitted and check_fit(wmts, specified_map_layer, layer_obj.tile_level, row, column):
        return
    splitted_map_layers = (layer for layer in wmts_.contents if
                           layer_obj.original_layer in layer and layer_obj.original_layer != layer)
    for specified_map_layer_split in splitted_map_layers:
        if check_fit(wmts, specified_map_layer_split, layer_obj.tile_level, row, column):
            layer_obj.layer = specified_map_layer_split
            layer_obj.already_splitted = True
            return
    else:
        print(specified_map_layer)
        print(layer_obj.original_layer)
        print(row, column)
        raise ValueError('No splitted layer found')


# In[8]:


def get_specific_layer(config, name_layer):
    if name_layer is not None:
        for web_map_ in config.web_maps:
            if not web_map_.ignore:
                for layer_ in web_map_.map_layers:
                    if name_layer in layer_.name:
                        return web_map_, layer_
    web_map = config.web_maps[1]
    layer = web_map.map_layers[0]
    return web_map, layer


# ## Get a tile for a specific coordinate
# To get the exact tile for a coordinate there are a few steps that need to be done.
# 1. it is necessary to see if the the desired levels exists.
# 1. get the correct tile matrix.
# 1. get the corresponding row, column, height in image and width in image.
# 1. get the specific layer when it is is split up into multiple files.
# 1. get the corresponding tile for the layer, the set and level.
# 
# Then the tile is returned with the corresponding point on the image and the level. 

# In[9]:

def get_pillow_image_from_tile(wmts, layer, row, column, lock=None):
    return add_tile(wmts, layer, row, column).get_image_from_tile(lock)


def add_tile(wmts, layer, row, column, lock=None):
    if layer.split:
        get_specified_map_layer_if_split_up(wmts, layer, row, column)
    image_exists = fileToObjects.check_image(layer.name, layer.level, row, column)
    if only_save and image_exists:
        return None
    tile_image = layer.get_image_tile(layer.level, row, column)
    if tile_image is None:
        tile_image = get_tile_image(column, layer, row, wmts, lock)
    return tile_image


def get_tile_image(column, layer, row, wmts, lock):
    global count
    image_exists = fileToObjects.check_image(layer.name, layer.level, row, column)
    if only_save and image_exists:
        return None
    tile = None
    image = None
    if image_exists is False:
        # print('Getting', layer.name, layer.level, row, column)
        # count += 1
        # print('Amount of images gotten is ', count)
        for attempt_number in range(3):
            try:
                tile = wmts.tile_service.gettile(
                    layer=layer.layer,
                    tilematrixset=wmts.set_name,
                    tilematrix=layer.tile_level,
                    row=row,
                    column=column,
                    format=wmts.tile_service.contents[layer.layer].formats[0])
                image = None
                break
            except (TimeoutError, ConnectionResetError, ConnectionError) as e:
                print('Timeout error', layer.name, 'Trying again in 60 seconds')
                time.sleep(60)

                if attempt_number == 2:
                    print(e)
                    raise TimeoutError(layer.name, layer.layer)
                print('Trying again', layer.name)
    else:
        image = fileToObjects.get_image(layer.name, layer.level, row, column)
        tile = None
    if tile is None and image is None:
        raise AttributeError("Tile and Image are both none")
    tile_image = mapResources.ImageTile(tile, layer.name, layer.level, row, column, image)
    if only_save:
        layer.add_image_gotten(tile_image)
        tile_image.save_image(lock)
        del tile_image
        return None
    else:
        layer.add_image_tile(tile_image)

    return tile_image


# In[10]:


def get_tile_for_coordinate(point_, wmts, layer, lock):
    layer.level = point_.level
    get_tile_level(wmts, layer)
    matrix = get_matrix_at_level(wmts, layer.level)
    codes = get_single_height_width(matrix, point_)
    row, column, pos_image_height, pos_image_width, pixel_size = codes
    tile_image = add_tile(wmts, layer, row, column, lock)
    layer.pixel_size = pixel_size
    return tile_image, pos_image_height, pos_image_width


# ## Get a image for a specific point
# To get the image and information of a specific point it is necessary to have the information with latitude and
# longitude, level etc.. The given back tile in bytes is then parsed to a image and if wanted it can be shown in a
# graph to verify the correct point. all this information is then returned.

# In[11]:


def get_image_and_information_for_single_point(point_, layer, wmts, lock=None):
    tile, pos_image_height, pos_image_width = get_tile_for_coordinate(point_, wmts, layer, lock)
    if tile is not None:
        return transformObjects.get_image_point(tile, pos_image_width, pos_image_height, wmts, layer)
    return None


# ## Get all the images for a specific point
# Because there are multiple sources for a single point it is necessary to iterate over the multiple sources and
# their respective layers. this results in two inner for loops. The returned list contains the multiple images and
# their respective layers, sources and points.

# In[12]:


def get_image_and_plot(info_dict, config, show=True, specific=None):
    global standardized_rendering_pixel_size
    standardized_rendering_pixel_size = config.standardized_rendering_pixel_size
    measured_point = point.MeasurementPoint(info_dict)
    items_run_off = {}
    for web_map in config.web_maps:
        if not web_map.ignore:
            if web_map.name not in items_run_off:
                items_run_off[web_map.name] = {"webmap": web_map, "items": {}}
            for layer in web_map.map_layers:
                items_run_off[web_map.name]["items"][layer.name] = layer
    if specific is not None:
        web_map = items_run_off[specific["webmap_name"]]["webmap"]
        layer = items_run_off[specific["webmap_name"]]["items"][specific["layer_name"]]

        measured_point.add_image_point(
            get_image_and_information_for_single_point(info_dict, layer,
                                                       web_map))
    else:
        for web_map_name in items_run_off.keys():
            web_map_ = items_run_off[web_map_name]["webmap"]
            for layer_name in items_run_off[web_map_name]["items"]:
                layer = items_run_off[web_map_name]["items"][layer_name]
                measured_point.add_image_point(
                    get_image_and_information_for_single_point(info_dict, layer,
                                                               web_map_))

    if show:
        for image_point in measured_point.image_points:
            image_point.show_image_with_point()
    return measured_point


def get_image_and_save(info_dict, config, lock):
    global standardized_rendering_pixel_size
    standardized_rendering_pixel_size = config.standardized_rendering_pixel_size
    for web_map in config.web_maps:
        if web_map.ignore:
            continue
        for layer in web_map.map_layers:
            get_image_and_information_for_single_point(info_dict, layer,
                                                       web_map, lock)


def get_information_for_tile(info_dict, config, name_layer=None):
    global standardized_rendering_pixel_size
    standardized_rendering_pixel_size = config.standardized_rendering_pixel_size
    measured_point = point.MeasurementPoint(info_dict)
    web_map, layer = get_specific_layer(config, name_layer)
    measured_point.add_image_point(get_image_and_information_for_single_point(info_dict, layer, web_map))
    return measured_point
