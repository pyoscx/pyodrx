import pyodrx 
import numpy as np
import os


planview = pyodrx.PlanView()
""" TODO:
    here we can add and modify the geometries on the road 
"""
geoms = []
geoms.append(pyodrx.Line(3000))
# geoms.append( pyodrx.Arc(0.05,angle=np.pi/2))
# geoms.append(pyodrx.Line(100))
# geoms.append(pyodrx.Spiral(0.05,-0.1,30))
# geoms.append(pyodrx.Line(100))


for geom in geoms: 
    planview.add_geometry(geom)


# create a solid roadmark
rm_s = pyodrx.RoadMark(pyodrx.RoadMarkType.solid,0.2,rule=pyodrx.MarkRule.no_passing)
rm_b = pyodrx.RoadMark(pyodrx.RoadMarkType.broken,0.2,rule=pyodrx.MarkRule.none)

# create centerlane
centerlane = pyodrx.Lane(a=2)
centerlane.add_roadmark(rm_s)
lanesec = pyodrx.LaneSection(0,centerlane)


# add a driving lane
for i in range(3): 
    lane = pyodrx.Lane(a=3)
    if i == 2: 
    	lane.add_roadmark(rm_s)
    else: 	
    	lane.add_roadmark(rm_b)
    lanesec.add_left_lane(lane)
    
    r_lane = pyodrx.Lane(a=3)
    if i == 2: 
    	r_lane.add_roadmark(rm_s)
    else: 	
    	r_lane.add_roadmark(rm_b)
    lanesec.add_right_lane(r_lane)

## finalize the road
lanes = pyodrx.Lanes()
lanes.add_lanesection(lanesec)
## here we specify the road id 
road = pyodrx.Road(0,planview,lanes)

odr = pyodrx.OpenDrive('myroad')
odr.add_road(road)
odr.adjust_roads_and_lanes()

pyodrx.prettyprint(odr.get_element())

pyodrx.run_road(odr,os.path.join('..','pyoscx','esmini'))
