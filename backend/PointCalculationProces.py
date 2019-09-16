from time import sleep

from backend import PostGisHandler, GeoJsonHandler

postgis = PostGisHandler.PostGisHandler()
geojson = GeoJsonHandler.GeoJsonHandler()


def calculatePoints():
    data = postgis.select_from_table(postgis.calculation_table, where="calculated is FALSE",panda=True)
    if len(data) is 0:
        sleep(30)
    for index,item in data.iterrows():
        print(item)
        geojson.calculateDepthPointsProces(item.payload)
        postgis.update_calculation(int(item.index_key))
while True:
    calculatePoints()