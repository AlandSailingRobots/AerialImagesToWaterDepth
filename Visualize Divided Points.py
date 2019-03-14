#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import WMTS_Single_Tile_Based as single_tile
from data_resources import fileToObjects as fetcher, transformObjects as transformer
from PIL import Image
from bokeh.plotting import figure, show, output_file
from datetime import datetime
import time

configuration = fetcher.get_configuration()


# In[ ]:


def get_datapoints(sample, data_source, level, name_set):
    data_points = list()

    for index, row in sample.iterrows():
        point_dict = transformer.create_info_object_from_panda_row(row, data_source['coordinate_system'], level)
        images_and_info = single_tile.get_information_for_tile(point_dict, configuration, name_set)
        images_and_info.depth = row['height']
        data_points.append(images_and_info)
    return data_points


def get_set_from_datapoints(data_source, sample_size, level, name_set, latitude_range=None, longitude_range=None,
                            no_sample=False):
    df = fetcher.open_xyz_file_as_panda(data_source)
    if latitude_range != None and longitude_range != None:
        df = df[(latitude_range[0] <= df.latitude)
                & (df.latitude <= latitude_range[1])
                & (longitude_range[0] <= df.longitude)
                & (df.longitude <= longitude_range[1])]
        if df.shape[0] == 0:
            return None
    if no_sample:
        sample = df
    else:
        sample = df.sample(sample_size)

    return get_datapoints(sample, data_source, level, name_set)


# In[ ]:


def get_range(value, tiles):
    min_value = min(i.__dict__[value] for i in tiles)
    max_value = max(i.__dict__[value] for i in tiles)
    ranged = list(range(min_value, max_value + 1))
    if len(ranged) == 0:
        return [min_value]
    else:
        return ranged


def get_missing_tiles(tiles, wmt, layer):
    rows_ = get_range('row', tiles)
    columns_ = get_range('column', tiles)
    levels_ = get_range('level', tiles)
    checked_set = set((i.level, i.row, i.column) for i in tiles)
    missing_set = set()
    for level in levels_:
        for row in rows_:
            for column in columns_:
                if (level, row, column) not in checked_set:
                    missing_set.add((row, column))

    print('missing', len(missing_set))
    start = datetime.now()
    count = 0
    for r, c in missing_set:
        single_tile.get_tile_image(c, layer, row, wmt)
        if count % 100 == 0:
            print(count)
        count += 1
    duration = datetime.now() - start
    print('Total', duration)
    print('Per item', duration / len(missing_set))


def compare(normal):
    return normal.level, normal.row, normal.column


# In[ ]:


def plot_data_points(data_dict, points, im, x_offset, y_offset, color, name):
    for point_ in points:
        image_tile = point_.image_points[0].image_tile
        if im.level == image_tile.level and im.row == image_tile.row and im.column == image_tile.column:
            image_location = point_.image_points[-1].data_point_in_image
            data_point = point_.data_point
            data_dict['width'].append(image_location.width)
            data_dict['height'].append(image_location.height)
            data_dict['x'].append(image_location.width + x_offset)
            data_dict['y'].append(image_location.height + y_offset)
            data_dict['lat'].append(data_point.latitude)
            data_dict['lon'].append(data_point.longitude)
            data_dict['name'].append(name)
            data_dict['color'].append(color)
            data_dict['depth'].append(point_.depth)
            data_dict['row'].append(image_tile.row)
            data_dict['column'].append(image_tile.column)


# In[ ]:


level = 12
datasets = list()
name_set = 'ortokuva'

# In[ ]:


for source in fetcher.get_open_data_sources():
    sample_set = get_set_from_datapoints(source, 10, level, name_set
                                         #                                          (6850000, 6851548), (628982, 630582)
                                         )
    if sample_set is not None:
        datasets.append({"items": sample_set, "color": source["color"], "name": source["name"]})

# In[ ]:


web_map, layer = single_tile.get_specific_layer(configuration, name_set)

# In[ ]:


print(len(layer.image_tiles))
get_missing_tiles(layer.image_tiles, web_map, layer)
images = layer.image_tiles
sorted_images = sorted(images, key=compare)

# In[ ]:


TOOLS = "pan,hover,box_zoom,zoom_in,zoom_out,reset"

widths = len(set(i.column for i in sorted_images))
heights = len(set(i.row for i in sorted_images))
image_sizes = sorted_images[0].get_image_from_tile().size
new_im = Image.new('RGB', (widths * image_sizes[0], heights * image_sizes[1]))

x_offset = 0
y_offset = 0
previous_im = None
data_dict = dict(x=list(), y=list(), name=list(), color=list(), lat=list(), lon=list(), depth=list(), width=list(),
                 height=list(), row=list(), column=list())
time_start = datetime.now()
amount = 0
p = figure(x_range=(0, new_im.width), y_range=(new_im.height, 0), match_aspect=True, tools=TOOLS,
           tooltips=[("Source", "@name"),
                     ("Lat", "@lat{0,0.000}"),
                     ("Long", "@lon{0,0.000}"),
                     ("Depth", "@depth"),
                     ("Width", "@width{0,0.0000}"),
                     ("Height", "@height{0,0.0000}"),
                     ("Row", "@row"),
                     ("Column", "@column")]
           )

for im in sorted_images:
    image = im.get_image_from_tile()
    if previous_im is not None and previous_im.column != im.column:
        x_offset += image.size[0]
    if previous_im is not None and previous_im.row != im.row:
        y_offset += image.size[1]
        x_offset = 0
    new_im.paste(image, (x_offset, y_offset))
    for dataset in datasets:
        plot_data_points(data_dict, dataset["items"], im, x_offset, y_offset, dataset["color"], dataset["name"])
    previous_im = im
print(datetime.now() - time_start)
new_im.save('image.jpg')
time.sleep(1)
p.image_url(url=['image.jpg'], x=0, y=0, w=new_im.width, h=new_im.height, anchor="top_left")
p.circle('x', 'y', source=data_dict, color='color')
output_file("pointsplot.html", title="Divided Points")

show(p)
