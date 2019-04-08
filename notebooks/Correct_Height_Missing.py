from data_resources import fileToObjects as fetcher
import pandas as pd
from pyproj import Proj, Transformer

used_coordinate_system = 'epsg:3067'


def transform_row(df_, source):
    inProj = Proj(init=source['coordinate_system'])
    outProj = Proj(init=used_coordinate_system)
    transformer = Transformer.from_proj(inProj, outProj)
    longitude, latitude = transformer.transform(list(df_.longitude), list(df_.latitude))
    df_.longitude = longitude
    df_.latitude = latitude


def get_single_df_from_sources(sources, correct_df=False, save=False):
    df = pd.DataFrame()
    for item in sources:
        temp_df = fetcher.open_xyz_file_as_panda(item)
        if correct_df and item['coordinate_system'] != used_coordinate_system:
            transform_row(temp_df, item)
            if save:
                fetcher.save_panda_as_file(temp_df.round(2), item['name'])
        temp_df['name'] = '' + item['name']
        df = df.append(temp_df)
    return df


def get_height_difference_in_location_points(df_, uncorrected_name):
    columns = ['longitude', 'latitude']
    df_[columns] = df_[columns].round()
    duplicated = df_[df_.longitude.isin(df_[df_.name == uncorrected_name].longitude) &
                     df_.latitude.isin(df_[df_.name == uncorrected_name].latitude) &
                     df_.duplicated(columns, keep=False)]
    print('percentage',
          len(duplicated[duplicated.name == uncorrected_name]) / len(df_[df_.name == uncorrected_name]) * 100.00)
    difference = duplicated[duplicated.name == uncorrected_name].height.mean() - duplicated[
        duplicated.name != uncorrected_name].height.mean()
    return difference


def change_height_and_save(df_, name, difference):
    df_ = df_[df_.name == name].copy()
    df_['height'] = df_['height'].apply(lambda x: round(x - difference, 2))
    fetcher.save_panda_as_file(df_.drop('name', axis=1), name)


sources = fetcher.get_data('private')
df = get_single_df_from_sources(sources, correct_df=True, save=True)
dif = get_height_difference_in_location_points(df.copy(), 'LIDAR_WMA_malli_2m')
change_height_and_save(df, 'LIDAR_WMA_malli_2m', dif)
print('height difference is:', dif, round(dif, 2))
