# app_iso
### Development of an isochrones visualisation app
 	 
# Installation steps
## OpenTripPlanner server installation
- Clone the Github repository (uses git-lfs)
- Verify that you have java8 (not compatible java9)

- Then open a console and write (*otp directory is the directory where the jar file is: [...]\app_iso\otp*):
```
cd [path/to/otp/directory]
java -Xmx6G -jar otp-1.2.0-shaded.jar --router Paris --graphs graphs --server
```
- Then wait until you see "*Grizzly server running*" (can take a couple of minutes depending of you computer specs)
- You can check if OTP is ready here: http://localhost:8080 (*you must see a map and the possibility to measure accessibility from a point to another stop*)

## Running the Bokeh app
- Python libraries needed: => ***See requirements.txt file***
- If you want to install all this libraries without difficulties, we recommend to donwload and install [Anaconda](https://www.anaconda.com/download/) but you can also install these via pip (*not recommended*)
- Once done, go in the root directory and open a console and run:
```
bokeh serve code
```
- Your console should show something like:

```
018-04-20 19:11:59,045 Starting Bokeh server version 0.12.13 (running on Tornado 4.5.3)
2018-04-20 19:11:59,048 Bokeh app running at: http://localhost:5006/code
2018-04-20 19:11:59,049 Starting Bokeh server with process id: 70796
```
- Then open http://localhost:5006/code in your browser. Wait a minute (*this app is not really optimized for the moment and could take time for the first run*)

- That's it. 

## macOS/conda installation notes

```
conda create -n isochrones
source activate isochrones
conda config --add channels conda-forge
conda install -n isochrones geopandas ipython bokeh requests osmnx jsonschema pandas pyproj geojson geopy Shapely numpy
```
