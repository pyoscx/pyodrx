import pyodrx 
import numpy as np
import os

line1 = pyodrx.Line(100)

arc1 = pyodrx.Arc(0.05,angle=np.pi/2)
line2 = pyodrx.Line(100)
arc2 = pyodrx.Arc(-0.05,angle=3*np.pi/4)

cloth = pyodrx.Spiral(0.001,0.009,100)

planview = pyodrx.PlanView()


planview.add_geometry(line1)

rm = pyodrx.RoadMark(pyodrx.RoadMarkType.solid,0.2,rule=pyodrx.MarkRule.no_passing)


lane1 = pyodrx.Lane(a=2)
lane1.add_roadmark(rm)
lanesec = pyodrx.LaneSection(0,lane1)

lane2 = pyodrx.Lane(a=4)
lane2.add_roadmark(rm)
lane3 = pyodrx.Lane(a=3)
lane3.add_roadmark(rm)
lane4 = pyodrx.Lane(a=3)
lane4.add_roadmark(rm)
lane5 = pyodrx.Lane(a=3)
lane5.add_roadmark(rm)

lanesec.add_left_lane(lane2)
lanesec.add_left_lane(lane3)
lanesec.add_right_lane(lane4)
lanesec.add_right_lane(lane5)

lanes = pyodrx.Lanes()
lanes.add_lanesection(lanesec)


road = pyodrx.Road(1,planview,lanes)

odr = pyodrx.OpenDrive('myroad')

odr.add_road(road)

odr.adjust_roads_and_lanes()

pyodrx.run_road(odr,os.path.join('..','esmini'))