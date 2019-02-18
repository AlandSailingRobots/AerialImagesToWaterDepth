# Aerial ImagesTo Water Depth

The goal of this research is to calculate(as the title describes) the water depth out of Aerial images. 

To result in this a few steps first need to be done.
1. Getting images from aerial photo's with their correlated data, It should consist of:
    * The photo itself.
    * The boundingbox of the photo. e.g : the topleft and bottom right coordinate.
1. Decide if the picture contains any relevant data or that is just a blank
1. Decide if the picture is a land or water picture or if it is a combination of those.
1. Calculate the amount of water in the picture.
1. Based on given depth data train the model to recognize depth.

Progress:
- [ ] Get the images.
    - [X] [Write a notebook which can get a single image for a random point](WMTS_Single_Tile_Based.ipynb).
    - [ ] T.B.A
- [ ] Algorithm to check if contains relevant data.
- [ ] Algorithm to check land, sea or combination.
- [ ] T.B.A
