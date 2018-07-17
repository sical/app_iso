# Explanations of parameters for automation of isochrone's calculation

| Name                      |  Details                                                            | Type                 |Example                 |
|:--------------------------|:--------------------------------------------------------------------|:------------------------| :------------------------|
| **id**                    | name_iso + "location_" + nb_adresses + id_location, automatic build | str |*iso_type_1-location_2_1* |
| **name_tech**             | name of the technique to use, used to name the results files | str | *Intersection_AlphaBlending_Uncalculated* |
| **name_iso**              | name of the iso type used, linked to the used technique | str | *iso_type_1* |
| **how**                   | overlay technique (*intersection, difference, symmetric_difference, union*) | str | *intersection* |
| **colors_iso**            | list of hex colors for isochrone, number must be equal to number of addresses | list of str | *["#ff0000","#0000ff"]* |
| **colors_intersection**   | hex color for intersection | str | *ffffff* |
| **opacity_isos**          | opacity level for isochrone (range between 0.0 and 1.0) | float | *0.3* |
| **opacity_intersection**  | opacity level for intersection (range between 0.0 and 1.0) | float | *0.3* |
| **shape**                 | type of shape (poly, line, ...) | str | *poly* |
| **region_id**             | region to specify coverage for API request | str | *fr-idf* |
| **date**                  | date for the request (format YYYY-MM-DD) | str | *2018-06-02* |
| **adresses**              | list of addresses | list of str | *["Gare Part-Dieu - Vivier Merle 69003 Lyon", "La Doua - Gaston Berger 69100 Villeurbanne"]* |
| **nb_adresses**           | number of adresses in list (used for id) | int | *2* |
| **id_location**           | id for location (group of addresses, used for id) | int | *1* |
| **time**                  | time for the request (format HH:MM:SS) | str | *08:00:00* |
| **duration**              | duration for isochrone request (minutes) | int | *20* |
| **step**                  | step value (1 for a duration of 20 mns will make 20 isochrones: 1mn, 2 mn, 3 mn, ...). 0 for no step | int | *1* |
| **symplify**							|	method to add simplified isochrone (simplify, convex or envelope), default None | str | *convex*  
| **buffer_radar**         	|	determine if a buffer radar is added to the figure (0 => No, 1 => Yes, default 0) | int | 0 |
| **around**         	      |	determine if a buffer is used to get points around origin to search for differences if points is moved from *x* meters ([distance in meters, precision]) | list of int | *[100, 3]* |
