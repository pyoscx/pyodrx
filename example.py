import pyodrx 
import numpy as np

line1 = pyodrx.Line(50)

arc1 = pyodrx.Arc(1,length=np.pi/2)
line2 = pyodrx.Line(10)
arc2 = pyodrx.Arc(-1,length=np.pi/2)

parampoly = pyodrx.ParamPoly3(0,1,1,1,0,1,0,0,'normalized')

planview = pyodrx.PlanView()

planview.add_geometry(parampoly)
planview.add_geometry(line1)
planview.add_geometry(arc1)
planview.add_geometry(line2)
planview.add_geometry(arc2)

rm = pyodrx.RoadMark(pyodrx.RoadMarkType.solid,0.2)
pyodrx.prettyprint(rm.get_element())
lane1 = pyodrx.Lane(a=2)
lane1.add_roadmark(rm)
lanesec = pyodrx.LaneSection(0,lane1)

lane2 = pyodrx.Lane(a=3)
lane2.add_roadmark(rm)
lane3 = pyodrx.Lane(a=3)
lane3.add_roadmark(rm)
lane4 = pyodrx.Lane(a=3)
lane4.add_roadmark(rm)
lane5 = pyodrx.Lane(a=3)
lane5.add_roadmark(rm),

lanesec.add_left_lane(lane2)
lanesec.add_left_lane(lane3)
lanesec.add_right_lane(lane4)
lanesec.add_right_lane(lane5)

lanes = pyodrx.Lanes()
lanes.add_lanesection(lanesec)

pyodrx.prettyprint(lanesec.get_element())
road = pyodrx.Road(1,planview,lanes)

odr = pyodrx.OpenDrive('myroad')

odr.add_road(road)

pyodrx.prettyprint(odr.get_element())
odr.write_xml()