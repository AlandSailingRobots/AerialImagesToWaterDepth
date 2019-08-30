# Website on Mac OS Local Host:
_Tested using 10.14.6 with HomeBrew, Python 3.7.4, Gdal 2.4.2, _

* [Clone](INSTALL_MAC_OS.md#Clone-repo)
* [Installation of Services](INSTALL_MAC_OS.md#Installation-of-services)
* [Database Setup](INSTALL_MAC_OS.md#Database-setup)
* [Starting Services](INSTALL_MAC_OS.md#Starting-services)
* [References](INSTALL_MAC_OS.md#References)


## Clone repo
Clone the repository in a directory of choice:
```shell script
#!/usr/bin/env bash
cd /Users/Dummy/SailingRobotsWebsite
git clone https://github.com/AlandSailingRobots/AerialImagesToWaterDepth.git
```

## Installation of services

### 1. Prerequisites
There are multiple services needed.
Check if installed:
* The Sailing Robots website
* Python 3 and Pip
* Gdal
* SpatialIndex
* PostgresSQL
* PostGis
* Proj

or install them via a terminal:

```shell script
#!/usr/bin/env bash
# Optional install of HomeBrew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
# Install python
brew install python
# Install Gdal
brew install gdal
# Install spatialindex
brew install spatialindex
# install PostgresSQL
brew install postgresql
# install PostgresSQL
brew install postgis
# install proj
brew install proj
```
To install the Sailing Robots website use the following guide: [Click here.](https://github.com/AlandSailingRobots/SailingRobotsWebsite/blob/feature/AerialImagesToWaterDepth/INSTALL_MAC_OS.md) 
:warning::exclamation: This guide assumes that you already have this installed.

### 2 Setup
#### 2.1 Python
It is best practice to run all the Python files in a virtual enviroment.
Therefore we first need to create it. In the correct AerialImagesToWaterDepth map run the following command
```shell script
python3 -m venv ENV
```
Where ENV is the name for your virtualenv.

To enter the virtual environment and to install it is necessary to activate it.
```shell script
source ENV/bin/activate
``` 
Then run Pip install.
```shell script
#All the requirements
pip install -r requirements.txt
# The local libraries.
pip install -e .
```
To deactivate the virtual environment simply type `deactivate`

#### 2.2 PostgresSQL 
To be able to use PostgresSQL we need to create a database.
```shell script
su - postgres
#You'll need to enter your root Password:
# This is the name of the database. The same name needs to be found in backend/server_settings.json
createdb testdb
psql testdb
#psql Version(11.5)
# You'll enter the database
#testdb=#
```
To be able to use the postgis library in postgresSQl, this extension needs to be added in your database. Which you just entered.
```postgresql
CREATE EXTENSION postgis;
```


##How To Run

There are multiple executables available.
Based on the required action steps are necessary.

#### Run Server
The python backend server can be run in different ways.

* From script: `sh run_postgres_and_python.sh backend/server.py`
* Manual with postgres script: 
    * `sh run_postgres_and_python.sh`
    * in venv: `python backend/server.py`
* Completely manual:
    * `pg_ctl -D /usr/local/var/postgres start`
    * in venv: `python backend/server.py`
    * `pg_ctl -D /usr/local/var/postgres stop`



