# Research question:

What kind of research already has been done to water depth out of images and how can we benefit from those?

## Search terms:

* bathymetry
* shallow water
* Machine Learning
* depth
* remote sensing

Ignored search terms:

* fish

Since 2010

Results in on 19 march 2019:

* [Google Scholar](https://scholar.google.com/scholar?as_q=bathymetry+shallow+water+Machine+Learning+depth+remote+sensing&as_epq=&as_oq=&as_eq=fish&as_occt=any&as_sauthors=&as_publication=&as_ylo=2010&as_yhi=&hl=en&as_sdt=0%2C5) 191 Results.
* [Research Utwente](https://research.utwente.nl/)
    * [Only shallow water](https://research.utwente.nl/en/publications/?originalSearch=Shallow+Water&pageSize=50&ordering=publicationYearThenTitle&descending=true&showAdvanced=false&orConceptIds=7175c85a-fd67-4a2c-bbb5-c38a23754a43&orConceptIds=c658cd7e-2691-400d-a938-15b176cb06b3&orConceptIds=8c08e583-5613-4cd9-a2f1-0ac8f5a4fec7&orConceptIds=b8eb9457-64ed-4df0-baba-14f3036c925e&allConcepts=false&inferConcepts=false&checkedConcepts=7175c85a-fd67-4a2c-bbb5-c38a23754a43%2Cc658cd7e-2691-400d-a938-15b176cb06b3%2C8c08e583-5613-4cd9-a2f1-0ac8f5a4fec7%2Cb8eb9457-64ed-4df0-baba-14f3036c925e&searchBy=RelatedConcepts): 18 Results
    * [Only Bathymetry](https://research.utwente.nl/en/publications/?originalSearch=Bathymetry&pageSize=50&ordering=publicationYearThenTitle&descending=true&showAdvanced=false&orConceptIds=430df1d6-46e8-413f-8d02-e69527afd133&orConceptIds=e4519a58-40c2-4b54-9dfc-f21a3232d2fa&orConceptIds=1e31fd7f-7406-45e4-992d-4355a366bcf0&orConceptIds=17034e5b-35f1-431d-9b3d-7462af267115&allConcepts=false&inferConcepts=false&checkedConcepts=430df1d6-46e8-413f-8d02-e69527afd133%2Ce4519a58-40c2-4b54-9dfc-f21a3232d2fa%2C1e31fd7f-7406-45e4-992d-4355a366bcf0%2C17034e5b-35f1-431d-9b3d-7462af267115&searchBy=RelatedConcepts): 16 Results
* [Microsoft Academic](https://preview.academic.microsoft.com/search?q=%22bathymetry%22%20%22shallow%20water%22%20%22Machine%20Learning%22%20%22depth%22%20%22remote%20sensing%22&f=&orderBy=0&skip=0&take=10):  434 Results but no limit on year.
* [Base-search](https://www.base-search.net/Search/Results?type=all&lookfor=%22bathymetry%22+%22shallow+water%22+%22Machine+Learning%22+%22depth%22+%22remote+sensing%22+year%3A%5B2010+TO+*%5D&ling=0&oaboost=1&name=&thes=&refid=dcresen&newsearch=1): 4 Results
* [Science.gov](https://www.science.gov/scigov/desktop/en/results.html): 25 Results

# Found information

## [Retrieval Using a Stereo and Radiative Transfer-Based Hybrid Method](https://www.mdpi.com/2072-4292/10/8/1247)

Keywords:

* satellite derived bathymetry
* radiometric attenuation
* photogrammetry
* stereo

### Short thoughts:

To wide, not related to machine learning. It does say that multiple sources have a higher impact for accuracy.

## [Remotely sensed empirical modeling of bathymetry in the southeastern Caspian Sea](https://research.utwente.nl/en/publications/remotely-sensed-empirical-modeling-of-bathymetry-in-the-southeast)

Keywords:

* Bathymetry
* Shallow Water
* Modeling
* Coastal Zone
* Principal Component Analysis
* Back Propagation
* Landsat
* Reflectance
* Water Depth
* Imagery
* Method
* Caspian Sea
* Aerosol

### Short thoughts:

Good information, relative to own research. gives good examples and accuracy numbers. It uses Backpropegation and Principal component Analysis.

## [Assessment of proposed approaches for bathymetry calculations using multispectral satellite images in shallow coastal/lake areas: a comparison of five models](https://link.springer.com/article/10.1007/s12517-016-2803-1)

Keywords:

* Bagging
* Boosting
* Bathymetry
* Landsat 8
* Spot 6
* Support vector regression

### Short thoughts:

Good example of a comparison of different systems. It gives insight into the usage of 5 models:

* ensemble regression tree-fitting algorithm using bagging(BAG)
* ensemble regression tree-fitting algorithm of least squares boosting (LSB)
* support vector regression algorithm (SVR)

 two conventional empirical methods

* the neural network (NN)
* Lyzenga generalised linear model (GLM)

Resulting in: *Compared with echosounder data, BAG, LSB, and SVR results demonstrate higher accuracy ranges from 0.04 to 0.35 m more than Lyzenga GLM. The BAG algorithm, producing the most accurate results, proved to be the preferable algorithm for bathymetry calculation.*
This gives hope for the own system and using it as an example.

## [Extracting shallow bathymetry from very high resolution satellite spectral bands and a machine learning algorithm](http://www.ices.dk/sites/pub/ASCExtendedAbstracts/Shared%20Documents/N%20-%20Seafloor%20habitat%20mapping%20from%20observation%20to%20management/N2415.pdf)
Keywords:

* bathymetry
* tropical
* pléiades-1
* neural network

### Short thoughts:

Short insight into the validation of created models by using a Neural Network(NN) model or Ratio Transform (RT) these are applied to 3 multispectral visible datasets. Giving result as r=0.89, R2=0.8 and RMSE=2.44

## [Assessment of machine learning approaches for bathymetry mapping in shallow water environments using multispectral satellite images](https://www.researchgate.net/publication/318066655_Assessment_of_machine_learning_approaches_for_bathymetry_mapping_in_shallow_water_environments_using_multispectral_satellite_images)

### Short thoughts:

This research uses 2 empirical models:

* random forest (RF)
* multi-adaptive regression spline (MARS)

and uses 2 conventional empirical methods:

* the neural network (NN) model
* the Lyzenga generalized linear model (GLM)

It says that the best result is : *When compared with echo sounder data, the RF and MASS results outperformed Lyzenga GLM results. Moreover, the RF method produced more accurate results with average 0.25 m RMSE improvements range than the NN model. The RF algorithm produced the most accurate results proved to be a preferable algorithm for bathymetry mapping in the shallow water context*

## [Shallow water bathymetry mapping using Support Vector Machine (SVM) technique and multispectral imagery](https://www.tandfonline.com/doi/abs/10.1080/01431161.2017.1421796)

Keywords:

* Bathymetry
* Shallow Water
* Imagery
* Support Vector Machine
* Evaluation
* Detection

### Short thoughts:

The research uses the SVM model and has a 80/20 dataset for training and testing. It uses multiple locations. It uses echo sounding and 3 bands in mages. From their testing it says that SVM is a valid method. 

## [A machine learning approach for estimation of shallow water depths from optical satellite images and sonar measurements](https://iwaponline.com/jh/article/15/4/1408/3487/A-machine-learning-approach-for-estimation-of)

Keywords:

* bathymetry
* machine learning
* remote sensing
* satellite images
* sonar measurements
* support vector machine

 ### Short thoughts:

 An research using Sonar, Lidar and Satelite images. the input is the images and the output is the sonar data. This is a very overlapping item. The findings where promising with using SVM.

## [A simple method for extracting water depth from multispectral satellite imagery in regions of variable bottom type](https://www.princeton.edu/geosciences/people/maloof/publications/Geyman_et_al-2019-Earth_and_Space_Science.pdf)

* remote sensing
* bathymetry
* classification
* machine learning
* Bahamas

### Short thoughts:

Claims to have a better method. Uses a physics based method. More robust to different types of bottoms which could be benificient for the baltic sea. Has a 0.2 meter accuracy.

## [High resolution topobathymetry using a Pleiades-1 triplet: Moorea Island in 3D](http://people.duke.edu/~jlh82/pubs/Collin_et_al_2018_RSE.pdf)

Keywords:

* Topobathymetry
* Satellite
* Optical
* Photogrammetry
* Light/water interactions
* LiDAR

### Short thoughts:
Uses a lot of lidar data(3.9 Million Points). Has wide range of depth(-20m until 1207 m). So more land points then really seapoints. Uses Pleiades-1 triplet imagery. Not really using machine learning.

## [Approaching bathymetry estimation from high resolution multispectral satellite imagesusing a neuro-fuzzy technique](https://www.researchgate.net/publication/235742655_Approaching_bathymetry_estimation_from_high_resolution_multispectral_satellite_images_using_a_neuro-fuzzy_technique)

Through reading in [the previous research](Research%20Documents.md#a-machine-learning-approach-for-estimation-of-shallow-water-depths-from-optical-satellite-images-and-sonar-measurementshttpsiwaponlinecomjharticle15414083487a-machine-learning-approach-for-estimation-of)
### Short thoughts:
Shows good usage of neural networks. Also shows promising results in the detailed level of accuracy.

## [Satellite-Derived Bathymetry Using Random Forest Algorithm and Worldview-2 Imagery](https://www.researchgate.net/profile/Masita_Manessa/publication/309587071_SATELLITE-DERIVED_BATHYMETRY_USING_RANDOM_FOREST_ALGORITHM_AND_WORLDVIEW-2_IMAGERY/links/581c087708ae40da2ca92c4b.pdf)
Keywords:

* Satellite-derived bathymetry
* Worldview-2
* random forest
* multiple linear regression

    
 ### Short thoughts:
 Good information about the difference in the color points resulting in different results. Also nice to see random forest in here. Very shallow depth (from 0.14 until 1.27 meters deep) and a very low RMSE. An RMSE of 0.16 and 0.47

## [Generation of the bathymetry of a eutrophic shallow lake using WorldView-2 imagery](https://www.researchgate.net/profile/Onur_Yuzugullu/publication/258256471_Generation_of_the_bathymetry_of_a_eutrophic_shallow_lake_using_WorldView-2_imagery/links/57502ce308ae5c7e547a8c11.pdf)

Found by similarity of [the previous thesis](Research%20Documents.md#generation-of-the-bathymetry-of-a-eutrophic-shallow-lake-using-worldview-2-imageryhttpswwwresearchgatenetprofileonur_yuzugullupublication258256471_generation_of_the_bathymetry_of_a_eutrophic_shallow_lake_using_worldview-2_imagerylinks57502ce308ae5c7e547a8c11pdf)

### Short thoughts:
Very few measurement points(59 Points) over an 1.25 km<sup>2</sup>.

## [Estimation of Water Depths and Turbidity From Hyperspectral Imagery Using Support Vector Regression](https://ieeexplore.ieee.org/abstract/document/7169523)

Found by similarity and keywords both:

### short thoughts.

Using both clear and turbulent water. SVR performs better then the band ratio method. Also showing good examples of RMSE related to calibration sample size, Water depth and different locations.