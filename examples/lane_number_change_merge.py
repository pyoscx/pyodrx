import pyodrx
import os

# create the planview and the geometry
planview = pyodrx.PlanView()


planview.add_geometry(pyodrx.Line(500))


# create two different roadmarkings
rm_solid = pyodrx.RoadMark(pyodrx.RoadMarkType.solid,0.2)
rm_dashed = pyodrx.RoadMark(pyodrx.RoadMarkType.broken,0.2)

# create a centerlane (same centerlane can be used since no linking is needed for this)
centerlane = pyodrx.Lane(a=2)
centerlane.add_roadmark(rm_solid)

# create the first lanesection with two lanes
lanesec1 = pyodrx.LaneSection(0,centerlane)
lane1 = pyodrx.Lane(a=3)
lane1.add_roadmark(rm_dashed)

lane2 = pyodrx.Lane(a=3)
lane2.add_roadmark(rm_solid)

lanesec1.add_right_lane(lane1)
lanesec1.add_right_lane(lane2)

# create the second lanesection with one lane merging
lanesec2 = pyodrx.LaneSection(250,centerlane)
lane3 = pyodrx.Lane(a=3)
lane3.add_roadmark(rm_dashed)

lane4 = pyodrx.Lane(a=3,b=-0.1)
lane4.add_roadmark(rm_solid)

lanesec2.add_right_lane(lane3)
lanesec2.add_right_lane(lane4)

# create the last lanesection with one lane
lanesec3 = pyodrx.LaneSection(280,centerlane)

lane5 = pyodrx.Lane(a=3)
lane5.add_roadmark(rm_solid)

lanesec3.add_right_lane(lane5)

# create the lane links
lanelinker = pyodrx.LaneLinker()
lanelinker.add_link(predlane=lane1,succlane=lane3)
lanelinker.add_link(predlane=lane2,succlane=lane4)
lanelinker.add_link(predlane=lane3,succlane=lane5)

# create the lanes with the correct links
lanes = pyodrx.Lanes()
lanes.add_lanesection(lanesec1,lanelinker)
lanes.add_lanesection(lanesec2,lanelinker)
lanes.add_lanesection(lanesec3,lanelinker)

# create the road
road = pyodrx.Road(1,planview,lanes)

# create the opendrive
odr = pyodrx.OpenDrive('myroad')
odr.add_road(road)

# adjust the roads and lanes
odr.adjust_roads_and_lanes()

# write the OpenDRIVE file as xodr using current script name
odr.write_xml(os.path.basename(__file__).replace('.py','.xodr'))

# uncomment the following line to display the road using esmini
# pyodrx.run_road(odr,os.path.join('..','..','esmini'))