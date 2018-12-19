# App_iso
> **USE WITH PYTHON 3.6**

# Table of contents

* [Development of an isochrones visualisation app](#devt)
	* [Installation steps](#installation)
		* [Clone the repo](#repo)
		* [Python packages](#packages)
		* [Navitia token](#token)
		* [How to elaborate the parameters file](#parameters_file)
		* [Explanations of parameters for automation of calculation](#explane_params)
		* [Get a graph (*nodes and edges JSON files*)](#get_graph)
		* [Modes](#modes)
		* [How to proceed with Google sheets](#sheets)
	* [Usage](#usage)
		* [Required files](#requ_files)
		* [Required parameters](#requ_params)
		* [Running the core module](#running)
	* [Libraries used (*version, licence, link to licence*)](#libraries)

<a id="devt"></a>
# Development of an isochrones visualisation app
This is an experimental application using [Python Bokeh](https://bokeh.pydata.org/en/latest/) to visualize transit Isochrones (*measured using [Navitia API](http://doc.navitia.io/#isochrones), based on [GTFS](https://en.wikipedia.org/wiki/General_Transit_Feed_Specification)*) and their intersections. It is used to test various designs (*shapes, colors, contours, backgrounds, ...*) in order to determine the most accessible designs for isochronic shapes's intersections.  

> ***WARNING: this application is a work in progress.***

<a id="installation"></a>
## Installation steps

<a id="repo"></a>
### Clone the repo
- Clone:
```
git clone -b iso_design https://github.com/sical/app_iso.git
```
- or download the iso_design branch repository

<a id="packages"></a>
### Python packages
- Install required Python packages using requirements.txt file
- If you want to use conda, you need to add channel ```conda-forge```. In anaconda prompt: ```conda config --append channels conda-forge```
- Then this command should work (*if not conda or pip install the 11 packages*)
```
while read requirement; do conda install --yes $requirement; done < requirements.txt
```
<a id="token"></a>
### Navitia token
- You have to use a token to use Navitia API
- So you need to register [here](https://www.navitia.io/register/) to get a token
- Create a file named "*.env*" in the "*code*" directory ... (*see figure*)

<img src="./screenshots/token.png" width="60%">

- ... with only one line in it (*never push your .env file on Github !*):

```
NAVITIA_TOKEN=""
```
- Put your Navitia token between the quotation marks and save your file

<a id="parameters_file"></a>
### How to elaborate the parameters file
* Elaborate a sheet with all the parameters (*see [here](#explanations-of-parameters-for-automation-of-calculation)*)
* Save it as .csv or .tsv (*see [here](#how-to-proceed-with-google-sheets) how to proceed with Google Sheet*)

<a id="explane_params"></a>
### Explanations of parameters for automation of calculation

| Name                      |  Details                                                            | Type                 |Example                 |
|:--------------------------|:--------------------------------------------------------------------|:------------------------| :------------------------|
| **id**                    | name_iso + "location_" + nb_adresses + id_location, automatic build | str |*iso_type_1-location_2_1* |
| **option**             | type of request (*journeys* or *isochrones*) | str | *jouneys* |
| **name_iso**              | name of the iso type used, linked to the used technique | str | *iso_type_1* |
| **how**                   | overlay technique (*intersection, difference, symmetric_difference, union*) | str | *intersection* |
| **region_id**             | region to specify coverage for API request | str | *fr-idf* |
| **date**                  | date for the request (format YYYY-MM-DD) | str | *2018-06-02* |
| **adresses**              | list of addresses | list of str | *["Gare Part-Dieu - Vivier Merle 69003 Lyon", "La Doua - Gaston Berger 69100 Villeurbanne"]* |
| **nb_adresses**           | number of adresses in list (used for id) | int | *2* |
| **id_location**           | id for location (group of addresses, used for id) | int | *1* |
| **time**                  | time for the request (format HH:MM:SS) | str | *08:00:00* |
| **durations**             | durations for isochrone request (minutes). [] if duration | list of int | *[10,20,30]* |
| **tolerance**							|	tolerance number for simplify method (higher is the number, greater is the simplification), default 50 | int | *100* |
| **preserve_topology**			|	preserve or not the topology (*1 => yes, 0 => no*), default 1 | int | *1* |
| **excluded_modes**				|	list of modes you want to exclude, default [] (*empty list*), (*see [here](#Modes)*) for possibilities | list of str | *["Metro","RapidTransit"]* |
| **inProj**                |	epsg for input coordinates (*from Navitia API*) | str | *epsg:4326* |
| **outProj**               |	epsg for output coordinates (*to be used with Bokeh*) | str | *epsg:3857* |
| **path**                 |	path to write GeoJSON files  | str | *.//outputs//tests_geojson//* |
| **edges_path**                |	path to graph edges JSON file (*see [here](#get_graph) to know how to get a graph*)  | str | *C:\Documents\graphs\Paris_50km_edges.json* |
| **nodes_path**            |	path to graph nodes JSON file  | str | *C:\Documents\graphs\Paris_50km_nodes.json* |

<a id="get_graph"></a>
### Get a graph (*nodes and edges JSON files*)

To get graph files that can be written on your disk (*in order to avoid to get the same network for each request that could take a huge amount of time*), you have to use the `graph_with_time` function from the `osmnx_based_functions` module.
Above there is an example of how to use this function:

```Python
from osmnx_based_functions import graph_with_time

edges_path = os.path.join(add_path, "graphs\Paris_50km_edges.json")
nodes_path = os.path.join(add_path, "graphs\Paris_50km_nodes.json")

point = 2.3467922,48.8621487

distance = 50000
G = graph_with_time(point, distance, edges_path, nodes_path, epsg={"init":"epsg:3857"})
```

You need to enter:
* paths to write nodes and edges JSON files
* point (*latitude, longitude in EPSG 4326*) that will be used as center for the circular bounding box
* a distance (*radius for the circular bbox in* **meters**)

<a id="modes"></a>
#### Modes
> ***API is case sensitive so respect lowercase and uppercase.***
> ***Available modes may vary regarding the region, to check the avalaible physical modes for a specific region, you can use this request:***
```https://[YOUR NAVITIA TOKEN]@api.navitia.io/v1/coverage/[REGION ID]/physical_modes```

Here is the modes you can choose to exclude:
 * Bike
 * BikeSharingService
 * Bus
 * Car
 * Funicular
 * Metro
 * RapidTransit
 * Tramway
 * VAL
 * CheckIn
 * CheckOut
 * Ferry
 * Train
 * Air
 * Coach
 * LocalTrain
 * Shuttle
 * Tram
 * Rail
 * LongDistanceTrain
 * PrivateVehicle
 * Trolleybus

 Some explanations for some modes:
 * RapidTransit refers to heavy transit like Paris RER
 * VAL refers to automatic subway
 * LocalTrain refers to french TER for example
 * LongDistanceTrain refers to high speed train

<a id="sheets"></a>
### How to proceed with Google sheets
* Set your parameters into a new sheet (based on examples and on the [readme](https://github.com/sical/app_iso/tree/iso_design#explanations-of-parameters-for-automation-of-isochrones-calculation))
* Save your sheet to tsv and put the .tsv file to ```./code/params/```
<img src="./export_tsv.png" width="50%">

<a id="usage"></a>
## Usage

<a id="requ_files"></a>
### Required files
* egdes (*JSON file*)
* nodes (*JSON file*)
* parameters (*CSV file*)
* .env (*.env file with Navitia TOKEN*)

<a id=""></a>
#### Required parameters

* *Example:*

|id                |option  |option_journey|option_isolines|how         |region_id|date      |addresses                                     |time |durations|excluded_modes|tolerance|preserve_topology|inProj   |outProj  |path                          |edges_path                                                                  |nodes_path                                                                  |
|------------------|--------|--------------|---------------|------------|---------|----------|----------------------------------------------|-----|---------|--------------|---------|-----------------|---------|---------|------------------------------|----------------------------------------------------------------------------|----------------------------------------------------------------------------|
|all_08h00_Chatelet|journeys|false         |true           |intersection|fr-idf   |2018-12-06|["90, Boulevard Saint-Germain, 75005, France"]|08:00|[20]     |[]            |0        |False            |epsg:4326|epsg:3857|.//output_png//tests_geojson//|C:\graphs\Paris_50km_edges.json|C:\graphs\Paris_50km_nodes.json|

* You need to have this kind of table as a CSV file

<a id="running"></a>
### Running the core module
> ***It is higly recommended to read [this notebook](https://github.com/sical/app_iso/blob/iso_design/code/experiments/Test_nouveau_isochrones_2.ipynb) for more details and explanations. [Here](https://nbviewer.jupyter.org/github/sical/app_iso/blob/iso_design/code/experiments/Test_nouveau_isochrones_2.ipynb) is the executed version of this notebook (*in french for now but soon in english*)***

*Example:*

```Python
import os

add_path = os.getcwd().replace('experiments', '')
sys.path.append(add_path)

from dotenv import load_dotenv
import docopt
from pathlib import Path

from csv_to_json import csv_to_json
from isos_and_intersections import GetIso

param_csv = os.path.join(add_path, "params/test_journeys.csv")
param_json = os.path.join(add_path, "params/test_journeys.json")
places_cache = os.path.join(add_path, "params/places_cache.json")

env_path = Path(add_path) / '.env'
load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv("NAVITIA_TOKEN")

columns_with_array_of_str = [
    "colors_iso",
    "addresses",
    "excluded_modes",
    "durations"
    ]

json_file = csv_to_json(param_csv, param_json, ";", columns_with_array_of_str)

gdf_global = GetIso(param_json, places_cache, api="navitia", token=TOKEN).get_all_isos()

```

You need to:
* Import:
	* 1 Python regular module:
		* *os*
	* 3 Python libraries:
		* *docopt*,
		* *dotenv*,
		* *pathlib*
	* 2 modules (*realised for the project*):
		* *csv_to_json*
		* *isos_and_intersections*
* Specify:
	* path to parameters CSV file
		* ex: `param_csv = os.path.join(add_path, "params/test_journeys.csv")`
	* path to parameters JSON file (*file that will be created from CSV and be used to check inputs with jsonschema*)
		* ex: `param_csv = os.path.join(add_path, "params/test_journeys.json")`
	* path to existing `places_cache` file or future file if not existing (*will be used to get )
		* ex: `places_cache = os.path.join(add_path, "params/places_cache.json")`
	* Columns with arrays in CSV file:
		* ex: `columns_with_array_of_str = [
    "addresses",
    "excluded_modes",
    "durations"
    ]`
* Run the `csv_to_json` with correct parameters
* Run the main module with correct parameters:
	* ex: `GetIso(param_json, places_cache, api="navitia", token=TOKEN).get_all_isos()`

<a id="libraries"></a>
## Libraries used (*version, licence, link to licence*)

| name           | version | licenses | link |
|----------------|:-------:|:--------|:-----|
|ast|Python 3.6.4 module| | |
|bokeh|1.0.2|"BSD 3-Clause ""New"" or ""Revised"" License"| [lien](https://github.com/bokeh/bokeh/blob/master/LICENSE.txt)|
|copy|Python 3.6.4 module| | |
|datetime|Python 3.6.4 module| | |
|functools |Python 3.6.4 module| | |
|geojson|2.3.0|"BSD 3-Clause ""New"" or ""Revised"" License"|[lien](https://github.com/frewsxcv/python-geojson/blob/master/LICENSE.rst)|
|geopandas|0.3.0|"BSD 3-Clause ""New"" or ""Revised"" License"|[lien](https://github.com/geopandas/geopandas/blob/master/LICENSE.txt)|
|geopy|1.12.0|MIT|[lien](https://github.com/geopy/geopy/blob/master/LICENSE)|
|itertools|Python 3.6.4 module| | |
|json|Python 3.6.4 module| | |
|jsonschema|2.6.0|MIT|[lien](https://pypi.org/project/jsonschema/)|
|math|Python 3.6.4 module| | |
|multiprocessing|Python 3.6.4 module| | |
|networkx|2.1|"BSD 3-Clause ""New"" or ""Revised"" License"|[lien](https://github.com/networkx/networkx/blob/master/LICENSE.txt)|
|numpy|1.14.2| specific |[lien](https://github.com/numpy/numpy/blob/master/LICENSE.txt)|
|osmnx|0.8.2|MIT|[lien](https://github.com/gboeing/osmnx/blob/master/LICENSE.txt)|
|overpass|0.6.1|Apache License 2.0|[lien](https://github.com/mvexel/overpass-api-python-wrapper/blob/master/LICENSE.txt)|
|pandas|0.23.4|"BSD 3-Clause ""New"" or ""Revised"" License"|[lien](https://github.com/pandas-dev/pandas/blob/master/LICENSE)|
|pyproj|1.9.5.1|(licence for proj4 : [lien](https://github.com/jswhit/pyproj/blob/master/LICENSE_proj4), licence for pyproj : [lien](https://github.com/jswhit/pyproj/blob/master/LICENSE))|
|python-dotenv|0.8.2|specific|[lien](https://github.com/theskumar/python-dotenv/blob/master/LICENSE)|
|requests|2.20.0|Apache License 2.0|[lien](https://github.com/requests/requests/blob/master/LICENSE)|
|shapely|1.6.4.post1| specific | [lien](https://github.com/Toblerity/Shapely/blob/master/LICENSE.txt)|
|threading|Python 3.6.4 module| | |
