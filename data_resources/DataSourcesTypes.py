import json
from enum import Enum

data_settings = json.load(open("../data_resources/data_settings.json"))


class DataSourceEnum(Enum):
    source_types = data_settings["datasource_types"]
    open_source = source_types["open_source"]
    private = source_types["private"]
    corrected = source_types["corrected"]
    height_corrected = source_types["height_corrected"]
    csv = source_types["csv"]
    combined = open_source + private
    combined_corrected = open_source + corrected
