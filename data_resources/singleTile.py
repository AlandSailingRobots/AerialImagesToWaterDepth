#!/usr/bin/env python
# coding: utf-8

# In[1]:


from data_resources import fileToObjects, transformObjects
from map_based_resources import point, mapResources

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


configuration = fileToObjects.get_configuration()
standardized_rendering_pixel_size = configuration.standardized_rendering_pixel_size


# ## Calculate the position of the coordinate in WMTS
# By using the Webmap tile matrix we can calculate the position of where the coordinate on the whole map. 
# 
# This is done by the following formula's:
# $height = \frac{\text{matrix top left corner height}\;-\; longitude}{scale \;\times\; pixelsize \;\times\; \text{
# length of matrix}}
# $ and  $width = \frac{lattitude \;-\; \text{matrix top left corner width}}{scale \;\times\; pixelsize
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
    list_of_tilematrixes = list(tileset.tilematrix.keys())
    return tileset.tilematrix[list_of_tilematrixes[level]]


# ## Get the desired level in a layer
# Sometimes the level has a special name and is not in this specific level. So then we change the name to the correct
# setting and perhaps go up a few level's. This makes sure that we get an image which contains the correct point.
# This data is also returned in the end so that levels that are not similar can be filtered out as well. this
# `special_level` option can be set in the `config.json` because this is a layer properties.

# In[6]:


def set_level_normal(tile_matrix_set_name, level):
    return '{0}'.format(level)


def set_level_special(tile_matrix_set_name, level):
    return '{0}:{1}'.format(tile_matrix_set_name, level)


def get_tile_level(wmts, layer):
    if not wmts.special_level:
        set_level = set_level_normal
    else:
        set_level = set_level_special
    tms = wmts.tile_service.contents[layer.layer]
    tile_level = set_level(wmts.set_name, layer.level)
    limits = tms.tilematrixsetlinks[wmts.set_name].tilematrixlimits
    while tile_level not in limits and len(limits) > 0:
        layer.level -= 1
        tile_level = set_level(wmts.set_name, layer.level)
    layer.tile_level = tile_level


# ## Dealing with split up layers
# Sometimes to have a better resolution of the images, the map is split up in the different tilematrix widths. This
# then has an extension of 0 to 9. To execute this function `split` has to be in the `config.json` file for this
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
    if name_layer != None:
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


def add_tile(wmts, layer, row, column):
    tile_image = layer.get_image_tile(layer.level, row, column)
    if tile_image is None:
        tile_image = get_tile_image(column, layer, row, wmts)
    return tile_image


def get_tile_image(column, layer, row, wmts):
    tile = wmts.tile_service.gettile(
        layer=layer.layer,
        tilematrixset=wmts.set_name,
        tilematrix=layer.tile_level,
        row=row,
        column=column,
        format=wmts.tile_service.contents[layer.layer].formats[0])
    tile_image = mapResources.ImageTile(tile, layer.level, row, column)
    layer.add_image_tile(tile_image)
    return tile_image


# In[10]:


def get_tile_for_coordinate(point_, wmts, layer):
    layer.level = point_.level
    get_tile_level(wmts, layer)
    matrix = get_matrix_at_level(wmts, layer.level)
    codes = get_single_height_width(matrix, point_)
    row, column, pos_image_height, pos_image_width, pixel_size = codes
    if layer.split:
        get_specified_map_layer_if_split_up(wmts, layer, row, column)
    layer.pixel_size = pixel_size
    tile_image = add_tile(wmts, layer, row, column)
    return tile_image, pos_image_height, pos_image_width,


# ## Get a image for a specific point
# To get the image and information of a specific point it is necessary to have the information with latitude and
# longitude, level etc.. The given back tile in bytes is then parsed to a image and if wanted it can be shown in a
# graph to verify the correct point. all this information is then returned.

# In[11]:


def get_image_and_information_for_single_point(point_, layer, wmts):
    tile, pos_image_height, pos_image_width = get_tile_for_coordinate(point_, wmts, layer)
    image_point = transformObjects.get_image_point(tile, pos_image_width, pos_image_height, wmts, layer)
    return image_point


# ## Get all the images for a specific point
# Because there are multiple sources for a single point it is necessary to iterate over the multiple sources and
# their respective layers. this results in two inner for loops. The returned list contains the multiple images and
# their respective layers, sources and points.

# In[12]:


def get_image_and_plot(info_dict, config, show=True):
    measured_point = point.MeasurementPoint(info_dict)
    for web_map in config.web_maps:
        if not web_map.ignore:
            for layer in web_map.map_layers:
                measured_point.add_image_point(get_image_and_information_for_single_point(info_dict, layer, web_map))
    if show:
        for image_point in measured_point.image_points:
            image_point.show_image_with_point()
    return measured_point


def get_information_for_tile(info_dict, config, name_layer=None):
    measured_point = point.MeasurementPoint(info_dict)
    web_map, layer = get_specific_layer(config, name_layer)
    measured_point.add_image_point(get_image_and_information_for_single_point(info_dict, layer, web_map))
    return measured_point
