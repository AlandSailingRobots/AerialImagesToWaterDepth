# How to Train a Convolutional Model.

The implementation of the model training is done in the [keras](CNN_KERAS.py) file.
This requires that first the [install guide](../README.md#Install) is followed. 
# Settings

## Models
A trainable configuration model is set from [the corresponding json](train_models.json) which holds the following keys:

| key | value type | description |
| --- | --- | --- |
|webmap_name|string|The webmap service name to use from the [wmts configuration](../resources/wmts_config.json)|
|layer_name|string|The webmap's layer name to use from the [wmts configuration](../resources/wmts_config.json)|
|size_in_meters| integer |The size in meters to use in the image. |
|level|integer|The zoom level to use. |
|pixels_per_meter| integer | the pixel size in meters which for 15 is 4 and 14 is 8 etc. |
|steps_per_epoch | integer | the amount of steps per epoch|
|epochs | integer| the amount of epochs|
|max_queue_size | integer | the amount of steps to have in the queue|
|limit_depth| negative integer| if set the datasets will only have a depth up to this|
|limit_dataset| [integer,integer]| if set the only the datasets in the specific range will be used.

from this configuration a model can be trained.
Selecting a model is done in the [keras setup](keras_setup.json) 
## Selecting the training data
Now the model is selected the training is also needed.
This is done from a Enum Type. These are set in [datasource types](../data_resources/data_settings.json) some of these are not available due to privacy restrictions. 

The open source files are always available from an online source. 

If not downloaded the open source files be will be downloaded.