from data_resources import fileToObjects as fetcher
import pandas as pd
from pyproj import Proj, transform

inProj = Proj(init='epsg:2394')
outProj = Proj(init='epsg:3067')


def transform_row(df_):
    x, y = transform(inProj, outProj, df_.longitude, df_.latitude)
    return pd.Series([x, y])


def get_single_df_from_sources(sources, correct_df=False,save=False):
    df = pd.DataFrame()
    for item in sources:
        temp_df = fetcher.open_xyz_file_as_panda(item)
        temp_df['coordinate_system'] = '' + item['coordinate_system']
        if correct_df and item['coordinate_system'] != 'epsg:3067':
            temp_df[['longitude', 'latitude']] = temp_df.apply(transform_row, axis=1)
        if save:
            temp_df.to_csv(temp_df['name']+'-corrected')
        temp_df['name'] = '' + item['name']
        df = df.append(temp_df)
    return df


def get_height_difference_in_location_points(df_, uncorrected_name):
    columns = ['longitude', 'latitude']
    df_[columns] = df_[columns].round()
    duplicated = df_[df_.longitude.isin(df_[df_.name == uncorrected_name].longitude) &
                     df_.latitude.isin(df_[df_.name == uncorrected_name].latitude) &
                     df_.duplicated(columns, keep=False)]
    print(duplicated.name.unique())
    difference = duplicated[duplicated.name == uncorrected_name].height.mean() - duplicated[
        duplicated.name != uncorrected_name].height.mean()
    return difference


sources = fetcher.get_data('private')
df = get_single_df_from_sources(sources)
get_height_difference_in_location_points(df.copy(), 'LIDAR_WMA_malli_2m')
