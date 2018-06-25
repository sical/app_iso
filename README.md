# app_iso
# Development of an isochrones visualisation app
This is an experimental application using [Python Bokeh](https://bokeh.pydata.org/en/latest/) to visualize transit Isochrones (*measured using [Navitia API](http://doc.navitia.io/#isochrones), based on [GTFS](https://en.wikipedia.org/wiki/General_Transit_Feed_Specification)*) and their intersections. It is used to test various designs (*shapes, colors, contours, backgrounds, ...*) in order to determine the most accessible designs for isochronic shapes's intersections.  

> ***WARNING:*** this application is a work in progress.

## Installation steps
### Clone the repo
- Clone the Github repository and use the iso_design branch

### Python packages
- Install required Python packages using requirements.txt file
- This command should work (*if not conda or pip install the 11 packages*)
```
while read requirement; do conda install --yes $requirement; done < requirements.txt
```

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

## Running the Bokeh app
- Then open a Anaconda command prompt (*or a system command prompt but with access to the right anaconda python environment*) and write:
```
cd [path/to/app_iso/directory]
bokeh serve code
```
- Bokeh server will start running and you should see something like this in the command prompt:
```
2018-05-24 14:13:56,529 Starting Bokeh server version 0.12.14 (running on Tornado 4.5.3)
2018-05-24 14:13:56,532 Bokeh app running at: http://localhost:5006/code
2018-05-24 14:13:56,539 Starting Bokeh server with process id: 50804
```
- Then in your browser, go to http://localhost:5006/code
- You should see this:

<img src="./screenshots/app.png" width="60%">

- You should see this in command prompt:
```
2018-05-24 15:12:11,345 200 GET /code (::1) 1114.46ms
2018-05-24 15:12:11,650 101 GET /code/ws?bokeh-protocol-version=1.0&bokeh-session-id=D4EU0HRjtcutsalbFuqdZ6GpubyO60UWGzmlXkJeJjvh (::1) 0.99ms
2018-05-24 15:12:11,651 WebSocket connection opened
2018-05-24 15:12:11,653 ServerConnection created
```
- If there are errors please report them (*error messages should appear in the command prompt*)

## Usage / controls
![app_usage](./screenshots/app_usage.png)
### <img src="./screenshots/usage/I_map.png" width="10%">
1. Pan tool: pan on the map
2. Zoom tool: use the mouse wheel to zoom on map
3. Node tool: use this to add point, as departure (*instead of adress*), on map. Use it with the Point button (*see IV.1.*)

### <img src="./screenshots/usage/II_api.png" width="18%">
1. Selection of region (*Navitia coverage*)
2. Enter a date for the request
3. Enter an adress. Use it with the Adress button (*see IV.2.*)
4. Enter a time constraint for the request
5. Enter a duration for the request

### <img src="./screenshots/usage/III_shape.png" width="10%">
1. Use Points button if you want shape with points contours (*MultiPoints*)
2. Use Lines button if you want only contours MultiPolygons
3. Use Polygons button if you want MultiPolygons

### <img src="./screenshots/usage/IV_Point.png" width="10%">
1. Use Point button with Node tools to add point on map (*see I.3.*)
2. Use Adress button if you want to use adress methode (*see II.3.*)

### <img src="./screenshots/usage/V_Color.png" width="18%">
1. Tab to choose between color sliders or Viridis colors. In Viridis tab, you can choose between 5 colorblindness accessible colors
2. RGB Red slider to set red value
3. RGB Green slider to set green value
4. RGB Blue slider to set blue value
5. Opacity slider to set the opacity value

### <img src="./screenshots/usage/VI_Tiles.png" width="18%">
1. This slider could be used to change tiles opacity

### <img src="./screenshots/usage/VII_Types.png" width="19%">
1. Intersection button: measure the intersection between 2 or more isochrone shapes
2. Union button: join 2 or more isochrones to get one unique isochrone
3. Difference button: make a symmetric difference between 2 or more isochrones

### <img src="./screenshots/usage/VIII_Aspect.png" width="20%">
> ***This settings will only be applied to the last generetad overlay.***

1. Tab to switch between colors settings and contour size setting
2. Overlay_contour button: use to change contour color with COLOR CHOICE tools
3. Overlay_background button: use to change background color with COLOR CHOICE tools

### <img src="./screenshots/usage/IX_Run.png" width="20%">
1. RUN button: run the app after set all the parameters (*MultiPoints*)
2. EXPORT button: export the map to PNG or SVG (*no tiles*)
3. RESET button: reset the map (*NOT WORKING FOR NOW, use a refresh instead*)

### LEGEND
* You can hide/show a layer by clicking on it in the control panel:

<img src="./screenshots/legend.png" width="30%">

## PARAMS folder
> ***WARNING:*** The parameters files need to be cleaned, possible useless parameter settings.

In the ```./code/params/``` folder, there is a JSON file named ```params.json```. This file is used to set projections and some of default design parameters.

```JSON
{
	"proj": {
		"inProj": "epsg:4326",
		"outProj": "epsg:3857"
	},
	"fig_params": {
		"width": 800,
		"height": 800,
		"alpha_tile": 0.5,
		"alpha_surf": 0.5,
		"alpha_cont": 0.85,
		"alpha_building": 0.0,
		"alpha_network": 0.6,
		"color_network": "black",
		"line_width_surf": 0.5,
		"line_width_cont": 4,
		"line_width_building": 1,
		"field": "time"
	}
}
```

There is also a default parameters file named ```default.json``` in the same folder. This file is used to set the default app's parameters.

```JSON
{
	"from_place":"2.349900;48.842021",
	"adress":"79 Rue Mouffetard, 75005 Paris",
	"time_":"08:00",
	"modes":"TRANSIT,WALK",
	"max_dist":"800",
	"step":1200,
	"nb_iter":"3",
	"year_min":2018,
	"month_min":5,
	"day_min":17,
	"year_max":2019,
	"month_max":5,
	"day_max":31
}
```

## Running the automate script
It is also possible to use a script ```./code/automate.py``` that generates PNG files from a JSON input parameters file.
This json file must be in ```./code/params/``` folder and named ```params_auto.json```. This file must look like this:
```JSON
[{
		"name": "Intersection_AlphaBlending_Uncalculated",
		"how": "intersection",
		"colors_iso": ["#ff0000", "#0000ff", "#00ff00"],
		"colors_intersection": "#ffffff",
		"opacity_isos": 0.3,
		"opacity_intersection": 0.0,
		"shape": "poly",
		"region_id": "fr-idf",
		"date": "2018-06-21",
		"adresses": ["79 Rue Mouffetard, 75005 Paris", "1 rue de vaugirard, 75005 Paris", "10 boulevard voltaire, 75005 Paris"],
		"time": "08:00",
		"duration": 20
	}, {
		"name": "Intersection_AlphaBlending_Calculated",
		"how": "intersection",
		"colors_iso": ["#ff0000", "#0000ff", "#00ff00"],
		"colors_intersection": "None",
		"opacity_isos": 0.3,
		"opacity_intersection": 0.3,
		"shape": "poly",
		"region_id": "fr-idf",
		"date": "2018-06-21",
		"adresses": ["79 Rue Mouffetard, 75005 Paris", "1 rue de vaugirard, 75005 Paris", "10 boulevard voltaire, 75005 Paris"],
		"time": "08:00",
		"duration": 20
	}
]
```

You can use the ```csv_to_jon.py``` to transform CSV files (or TSV) to JSON file if you prefer to use spreadsheets (*Google Sheet, Microsoft Excel, LibreOfficeCalc, ...*) and export sheets as CSV or CSV-like file.
All the generated images will be exported as PNG files into ```./code/output_png/``` folder with a name corresponding to the name in the parameters' file.

## Known issues
- Impossible geolocation with some adresses (*no error message for now, only empty map*)
- Reset button make the side controls panel to disappear (*bug: currently work on it*)
- Export button/function needs to be debugged (*known Bokeh problems with svg/png exports when using map tiles*)
- Code needs a serious cleaning
- Bokeh doesn't support MultiPolygons with holes (*need to find a workaround*)
