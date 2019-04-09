# Aerial ImagesTo Water Depth

The goal of this research is to calculate(as the title describes) the water depth out of Aerial images. 

To result in this a few steps first need to be done.
1. Getting images from aerial photo's with their correlated data, It should consist of:
    * The photo itself.
    * ~~The bounding box of the photo. e.g : the top left and bottom right coordinate.~~
    * location of the coordinate point in the image. which pixel etc.
1. Decide if the picture contains any relevant data or that is just a blank
1. Decide if the picture is a land or water picture or if it is a combination of those.
1. Calculate the amount of water in the picture.
1. Based on given depth data train the model to recognize depth.
1. Improve the model by at least 5 percent.
1. Integrate the model into the SailingRobots website. 

Progress:
- [ ] Get the images.
    - [X] [Write a notebook which can get an image for a random point](notebooks/WMTS_Single_Tile_Based.ipynb).
    - [X] [Configuration file which gives possible WMTS Urls and their layers](resources/config.json)
    - [X] Have a background image to check if the current coordinate is land or sea.
    - [X] Have selected location in image
        - [x] in code.
        - [x] visualized
    - [X] Ability to use different coordinate systems.
    - [X] Read coordinates in from files:
        - [X] [JSON](resources/coordinates.json)
        - [X] [XYZ](/data_resources/fileToObjects.py) with different gps systems.
- [ ] Cleaning and normalizing data
- [ ] Algorithm to check land, sea or combination.
- [ ] Estimator for water depth
- [ ] Integration for website
