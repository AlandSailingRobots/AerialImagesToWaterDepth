# Aerial Images To Water Depth

## Install

[The guide](INSTALL_MAC_OS.md) on how to install is currently written for Mac OS only. 
The guide is most likely the same for any other unix system but some commands maybe need to be changed.

## Goal
The goal of this research is to calculate(as the title describes) the water depth out of Aerial images. 

To result this a few steps first need to be done.
1. Getting images from aerial photo's with their correlated data, It should consist of:
    * The photo itself.
    * ~~The bounding box of the photo. e.g : the top left and bottom right coordinate.~~
    * location of the coordinate point in the image. which pixel etc.
1. Retrieve depth data from the given resources online.
1. Based on given depth data train the model to recognize depth.
1. Integrate the model into the [SailingRobots](https://github.com/AlandSailingRobots/SailingRobotsWebsite) website. 

## Progress:
- [X] Get the images.
    - [X] [Write a notebook which can get an image for a random point](notebooks/WMTS_Single_Tile_Based.ipynb).
    - [X] [Configuration file which gives possible WMTS Urls and their layers](resources/wmts_config.json)
    - [X] Have selected location in image
        - [X] in code.
        - [X] visualized
    - [X] Ability to use different coordinate systems.
    - [X] Read coordinates in from files:
        - [X] [JSON](resources/coordinates.json)
        - [X] [XYZ](/data_resources/fileToObjects.py) with different gps systems.
- [X] Train Model based on the given depth data:
    - [X] From [different](/data_resources/DataSourcesTypes.py) sources
- [X] Estimator for water depth
- [X] Integration for website
    - [X] Call to calculate areas
    - [X] Call to get areas with a depth lower then specified.
 
 ## Train a Model
 The description of how to train the model can be found at the [train model](machine_learning/readme.md) description.
 
 ## Run the server
 The description of how to run the server with the corresponding machine learning model can be found at the [Install](INSTALL_MAC_OS.md#Starting-services)
 
 ## Example
 An example of the use in the website
 ![alt text](DepthRecognitionExample.gif "Logo Title Text 1")
