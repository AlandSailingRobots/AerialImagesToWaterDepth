from data_resources import fileToObjects, transformObjects, singleTile
from PIL import Image
from bokeh.plotting import figure, show, output_file
import time
import progressbar

widgets = [
    ' [', progressbar.Timer(), '] ',
    progressbar.Bar(),
    ' (', progressbar.AdaptiveETA(), ') ',
]
configuration = fileToObjects.get_configuration()


def get_datapoints(sample, data_source, level, name_set):
    data_points = list()
    for index, row in sample.iterrows():
        point_dict = transformObjects.create_info_object_from_panda_row(row, data_source['coordinate_system'], level)
        images_and_info = singleTile.get_information_for_tile(point_dict, configuration, name_set)
        images_and_info.depth = row['height']
        data_points.append(images_and_info)
    return data_points


def get_set_from_datapoints(data_source, sample_size, max_depth=None, latitude_range=None,
                            longitude_range=None,
                            no_sample=False):
    df = fileToObjects.open_xyz_file_as_panda(data_source)
    if latitude_range is not None and longitude_range is not None:
        df = df[(latitude_range[0] <= df.latitude)
                & (df.latitude <= latitude_range[1])
                & (longitude_range[0] <= df.longitude)
                & (df.longitude <= longitude_range[1])]
    if max_depth is not None:
        df = df[df.height >= max_depth]
    if df.shape[0] < sample_size:
        sample_size = df.shape[0]
    if no_sample:
        return df
    else:
        return df.sample(sample_size)


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
    progress_ = progressbar.ProgressBar(widgets=['Missing Images'] + widgets)
    for r, c in progress_(missing_set):
        singleTile.add_tile(wmt, layer, r, c)


def compare(normal):
    return normal.level, normal.row, normal.column


def plot_data_points(data_dict, points, im, x_offset, y_offset, color, name):
    for point_ in points:
        image_tile = point_.image_points[0].image_tile
        if im.level == image_tile.level and im.row == image_tile.row and im.column == image_tile.column:
            image_location = point_.image_points[-1].data_point_in_image
            data_point = point_.data_point
            temp_dict = dict(
                width=image_location.width,
                height=image_location.height,
                x=image_location.width + x_offset,
                y=image_location.height + y_offset,
                lat=data_point.latitude,
                lon=data_point.longitude,
                name=name,
                color=color,
                depth=point_.depth,
                row=image_tile.row,
                column=image_tile.column
            )
            for item in temp_dict:
                data_dict[item].append(temp_dict[item])


def get_dataset_from_sources(sources, amount, level, name_set, max_depth=None, latitude_range=None,
                             longitude_range=None, no_sample=False):
    data = list()
    progress = progressbar.ProgressBar(widgets=['Getting Images'] + widgets)
    for item in progress(sources):
        sample = get_set_from_datapoints(item, amount, max_depth, latitude_range, longitude_range, no_sample)
        sample_set = get_datapoints(sample, item, level, name_set)
        if sample_set is not None:
            data.append({"items": sample_set, "color": item["color"], "name": item["name"]})
    return data


def create_image_and_points(sorted_images, datasets):
    widths = len(set(i.column for i in sorted_images))
    heights = len(set(i.row for i in sorted_images))
    image_sizes = sorted_images[0].get_image_from_tile().size
    new_im = Image.new('RGB', (widths * image_sizes[0], heights * image_sizes[1]))
    x_offset = 0
    y_offset = 0
    data_dict = dict(x=list(), y=list(), name=list(), color=list(), lat=list(), lon=list(), depth=list(), width=list(),
                     height=list(), row=list(), column=list())
    previous_im = None
    progress_ = progressbar.ProgressBar(widgets=['Creating images'] + widgets)
    for im in progress_(sorted_images):
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
    return new_im, data_dict


def plot_from_dict(data_dict, image):
    bokeh_tools = "pan,hover,box_zoom,zoom_in,zoom_out,reset"
    p = figure(x_range=(0, image.width), y_range=(image.height, 0), match_aspect=True, tools=bokeh_tools,
               tooltips=[("Source", "@name"),
                         ("Lat", "@lat{0,0.000}"),
                         ("Long", "@lon{0,0.000}"),
                         ("Depth", "@depth"),
                         ("Width", "@width{0,0.0000}"),
                         ("Height", "@height{0,0.0000}"),
                         ("Row", "@row"),
                         ("Column", "@column")]
               )
    p.image_url(url=['image.jpg'], x=0, y=0, w=image.width, h=image.height, anchor="top_left")
    p.circle('x', 'y', source=data_dict, color='color')
    output_file("pointsplot.html", title="Divided Points")
    show(p)


level = 12
name_set = ['ava_norm_split', 'ava_norm', 'ava_infrared', 'background_map'][2]
sources = fileToObjects.get_data()
datasets = get_dataset_from_sources(sources, 100, level, name_set, max_depth=-2, no_sample=False)
web_map, layer = singleTile.get_specific_layer(configuration, name_set)
get_missing_tiles(layer.image_tiles, web_map, layer)
sorted_images = sorted(layer.image_tiles, key=compare)
image, data_dict = create_image_and_points(sorted_images, datasets)
image.save('image.jpg')
time.sleep(1)
plot_from_dict(data_dict, image)
