# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 16:21:13 2018

@author: thomas
"""

schema={
        	"type":"object",
        	"properties": {
        		"id": {
        			"type":"string"
        		},
           "option": {
        			"type":"string"
        		},
           "option_journey": {
        			"type":"boolean"
        		},
           "option_isolines": {
        			"type":"boolean"
        		},
        		"how": {
        			"type":"string"
        		},
        		"region_id": {
        			"type":"string"
        		},
        		"date": {
        			"type":"string"
        		},
        		"adresses": {
        			"type":"array",
        			"items": {
        				"type":"string"
        			}
        		},
        		"time": {
        			"type":"string"
        		},
        		"durations": {
        			"type":"array",
        			"items": {
        				"type":"integer"
        			}
        		},
        		"tolerance": {
        			"type":"number"
        		},
        		"preserve_topology": {
        			"type":"boolean"
        		},
        		"excluded_modes": {
        			"type":"array",
        			"items": {
        				"type":"string"
        			}
        		},
        		"inProj": {
        			"type":"string"
        		},
        		"outProj": {
        			"type":"string"
        		},
            "path": {
        			"type":"string"
        		},
            "edges_path": {
        			"type":"string"
        		},
            "nodes_path": {
        			"type":"string"
        		}
            
        	}
        }