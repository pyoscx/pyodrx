""" This is a collection of ready to use functions, to generate standard road snipets, like:
    - Simple straight road
    - Spiral-Arc-Spiral type of turns
    - Simple junctions, including the connecting roads 
        limited to 3/4-way crossings with 90degree turns (3-way can be 120 deg aswell)
    - 
"""
import numpy as np

from .lane import Lane, RoadMark, LaneSection, Lanes
from .enumerations import RoadMarkType, MarkRule, ContactPoint, ElementType

from .geometry import Line, Arc, Spiral, EulerSpiral, PlanView
from .opendrive import Road, OpenDrive
from .links import Junction, Connection, _get_related_lanesection




STD_ROADMARK = RoadMark(RoadMarkType.solid,0.2,rule=MarkRule.no_passing)
STD_START_CLOTH = 1/1000000000
def standard_lane(offset=3,rm = STD_ROADMARK):
    """ standard_lane creates a simple lane with an offset an a roadmark
        
        Parameters
        ----------
            offset (int): width of the lane
                default: 3

            rm (RoadMark): road mark used for the standard lane
                default:  RoadMark(RoadMarkType.solid,0.2,rule=MarkRule.no_passing)
        Returns
        -------
            lane (Lane): the lane

    """
    lc = Lane(a=offset)
    lc.add_roadmark(rm)
    return lc


def create_straight_road(road_id,length=100,junction = -1, n_lanes=1, lane_offset=3):
    """ creates a standard straight road with two lanes

        Parameters
        ----------
            road_id (int): id of the road to create

            length (float): length of the road
                default: 100

            junction (int): if the road belongs to a junction or not
                default: -1
        Returns
        -------
            road (Road): a straight road
    """
    # create geometry
    line1 = Line(length)

    # create planviews
    planview1 = PlanView()
    planview1.add_geometry(line1)

    # create lanesections
    lanesec1 = LaneSection(0,standard_lane())
    for i in range(1, n_lanes+1, 1):
        lanesec1.add_right_lane(standard_lane(lane_offset))
        lanesec1.add_left_lane(standard_lane(lane_offset))

    # create lanes
    lanes1 = Lanes()
    lanes1.add_lanesection(lanesec1)

    # finally create the roads 
    return Road(road_id,planview1,lanes1,road_type=junction)


def create_arc_road(road_id,R, arc_angle ,junction = -1, n_lanes=1, lane_offset=3):
    """ creates a standard straight road with two lanes

        Parameters
        ----------
            road_id (int): id of the road to create

            length (float): length of the road
                default: 100

            junction (int): if the road belongs to a junction or not
                default: -1
        Returns
        -------
            road (Road): a straight road
    """
    # adjust sign if angle is negative
    if arc_angle < 0:
        R=-R 

    # create geometry
    curvature = 1/R
    arc1 = Arc(curvature,angle=arc_angle)

    # create planviews
    planview1 = PlanView()
    planview1.add_geometry(arc1)

    # create lanesections
    lanesec1 = LaneSection(0,standard_lane())
    for i in range(1, n_lanes+1, 1):
        lanesec1.add_right_lane(standard_lane(lane_offset))
        lanesec1.add_left_lane(standard_lane(lane_offset))

    # create lanes
    lanes1 = Lanes()
    lanes1.add_lanesection(lanesec1)

    # finally create the roads 
    return Road(road_id,planview1,lanes1,road_type=junction)


def create_cloth_arc_cloth(arc_curv, arc_angle, cloth_angle, r_id, junction = 1,cloth_start = STD_START_CLOTH, n_lanes=1, lane_offset=3):
    """ creates a curved Road  with a Spiral - Arc - Spiral, and two lanes

        Parameters
        ----------
            arc_curv (float): curvature of the arc (and max clothoid of clothoids)

            arc_angle (float): how much of the curv should be the arc

            cloth_angle (float): how much of the curv should be the clothoid (will be doubled since there are two clothoids)
            
            r_id (int): the id of the road

            junction (int): if the Road belongs to a junction
                default: 1

            cloth_start (float): staring curvature of clothoids

        Returns
        -------
            road (Road): a road built up of a Spiral-Arc-Spiral
    """
    
    pv = PlanView()
    # adjust sign if angle is negative
    if cloth_angle < 0 and  arc_curv > 0:

        cloth_angle = -cloth_angle
        arc_curv = -arc_curv
        cloth_start = -cloth_start
        arc_angle = -arc_angle 
    
    # create geometries
    spiral1 = Spiral(cloth_start, arc_curv, angle=cloth_angle)
    arc = Arc(arc_curv, angle=arc_angle )
    spiral2 = Spiral(arc_curv, cloth_start, angle=cloth_angle)

    pv.add_geometry(spiral1)
    pv.add_geometry(arc)
    pv.add_geometry(spiral2)

    # create lanes
    lsec = LaneSection(0,standard_lane())
    for i in range(1, n_lanes+1, 1):
        lsec.add_right_lane(standard_lane(lane_offset))
        lsec.add_left_lane(standard_lane(lane_offset))
    lanes = Lanes()
    lanes.add_lanesection(lsec)

    # create road
    return Road(r_id,pv,lanes,road_type=junction)

def get_lanes_offset(road1, road2, contactpoint):
    """ returns number of lanes (hp #left lanes = # right lanes) and their offset (hp offset is constant)


        Parameters
        ----------
            road1 (Road): first road 

            road2 (Road): second road 

        Returns
        -------
            n_lanes (int): 

            lane_offset (int):
    """
    #now we always look at lanesection[0] to take the number of lanes 
    #TO DO - understand if the roads are connect through end or start and then take the relative lane section 
    if contactpoint == ContactPoint.end: 
        n_lanesection = 0 
    else:
        n_lanesection = -1
    if len(road1.lanes.lanesections[n_lanesection].leftlanes) == len(road2.lanes.lanesections[0].leftlanes) and len(road1.lanes.lanesections[n_lanesection].rightlanes) == len(road2.lanes.lanesections[0].rightlanes):
        n_lanes = len(road1.lanes.lanesections[n_lanesection].leftlanes) 
        lane_offset = road1.lanes.lanesections[n_lanesection].leftlanes[0].a     
    else:
        raise NotSameAmountOfLanesError('Incoming oad ',road1.id, ' and outcoming road ', road2.id, 'do not have the same number of left lanes.')
        
    return n_lanes, lane_offset 



def create_junction_roads_R2(roads,angles,R,junction=1,startnum=100):
    """ creates all needed roads for some simple junctions
        - 3way crossings (either a T junction, or 120 deg junction)
        - 4way crossing (all 90 degree turns)

        Parameters
        ----------
            roads (list of Road): all roads that should go into the junction

            angles (list of float): the angles which the roads should be going out (see description for what is supported), 
                                    should be defined mathimatically positive (incoming road 0)

            r (float): the radius of the arcs in the junction (will determine the size of the junction)
            
            junction (int): the id of the junction
                default: 1

            spiral_part (float): the part of the curve that should be spirals (two of these) spiral_part*2 + arcpart = angle of the turn
                default: (1/3)

            arc_part (float): the part of the curve that should be an arc:  spiral_part*2 + arcpart = angle of the turn
                default: (1/3)

            startnum (int): start number of the roads in the junctions (will increase with 1 for each road)

        Returns
        -------
            junction_roads (list of Road): a list of all roads needed for all traffic connecting the roads
    """

    # if a straight line is used, calculate the length of it. Some Spiral Magic going on...
    # http://www.jerrymahun.com/index.php/home/open-access/viii-curves/76-chapter-e-spirals?showall=1

    spiral_part = 1/3
    arc_part = 1/3

    junction_roads = []

    # loop over the roads to get all possible combinations of connecting roads
    for i in range(len(roads)-1):
        # for now the first road is place as base, 
        if i == 0:
            cp = ContactPoint.end
            roads[i].add_successor(ElementType.junction,junction)
            
        else:
            cp = ContactPoint.start
            roads[i].add_predecessor(ElementType.junction,junction)
        
        for j in range(1+i,len(roads)):
            
            # check angle needed for junction
            print("angle of road  ", roads[i].id)
            print("is  ", angles[i])
            print("angle of road  ", roads[j].id)
            print("is  ", angles[j])

            an1 = angles[j]-angles[i] -np.pi   # [-pi, pi]   this is for the heading from the "front"   
            abs_an1 = abs(an1)

            
            print("an1 in between angle an1 is ", an1*180/np.pi) 
            
            if angles[j] > angles[i]:
                angle_for_r =  abs(angles[j]-angles[i]) 
                if angle_for_r < np.pi: 
                    print("case1")
                    angle_for_r = -angle_for_r
                else: 
                    print("case2")
                    angle_for_r = np.pi - (angle_for_r - np.pi) 
            else: 
                angle_for_r =  abs(angles[i]-angles[j]) 
                if angle_for_r > np.pi: 
                    print("case3")
                    angle_for_r = -(np.pi - angle_for_r)
                
            abs_angle_for_r = abs(angle_for_r)

            print("angle_for_r real angle between roads is ", angle_for_r*180/np.pi)

            # create road, either straight or curved
            n_lanes, lanes_offset = get_lanes_offset(roads[i], roads[j], cp )
            if angles[i]==angles[j] or ( angles[j]-angles[i] )% np.pi == 0 :
                # linelength = 0
                # for k in range(i+1, j+1, 1): 
                #     print("k is ", k)
                #     an1 = angles[k]-angles[k-1] -np.pi         
            
                #     angle_arc = an1*arc_part
                #     angle_cloth = an1*spiral_part
                    
                #     print("in between angle an1 is ", an1)
                #     if i == 0: 
                #         if an1 > 0: 
                #             angle_for_r = np.pi - an1
                #         else: 
                #             angle_for_r = np.pi - (-an1)
                #     else: 
                #         angle_for_r = angles[k]-angles[k-1] 
                    

                #     angle_cloth = an1*spiral_part 
                #     # spiral_length = 2*abs(angle_cloth*r)

                #     denom = (2/3)*abs(an1) - (abs(an1)/3)*(np.sin(an1/9))**2 -np.sin(an1/3) + (2/3)*abs(an1)*np.sin(an1/9)*np.tan((np.pi-an1)/2) + np.cos(an1/3)*np.tan((np.pi-an1)/2)
                #     r = R / denom
                #     print("straight line radius is ", r)

                #     spiral_length = 2*abs(angle_cloth*r)

                #     spiral = EulerSpiral.createFromLengthAndCurvature(spiral_length, STD_START_CLOTH, 1/r)
                #     (X, Y, _) = spiral.calc(spiral_length, 0, 0, STD_START_CLOTH, 0)

                #     X0 = X-r*np.sin(angle_cloth)
                #     Y0 = Y-r*(1-np.cos(angle_cloth))
                #     linelength += X0 + (r + Y0)*np.tan((np.pi-an1)/2)
                linelength = 2*R #+ R*0.2
                tmp_junc = create_straight_road(startnum,length= linelength,junction=junction, n_lanes=n_lanes, lane_offset=lanes_offset)
            else: 
                # an1 = angle_for_r
                
                angle_cloth = an1 * spiral_part
                angle_arc = an1 * arc_part

                an1 = abs(an1)
                angle_cloth = abs(angle_cloth)
                
                denom = 2*abs(angle_cloth) - abs(angle_cloth)*(np.sin(angle_cloth/3)**2) - np.sin(angle_cloth) + np.tan(an1/2) * (2*abs(angle_cloth) * np.sin(angle_cloth/3) + np.cos(angle_cloth))
                # since R = r*denom 
                r = R / denom
                print("denom is ", denom)  
                
                
                print("radius is ", r)    

                tmp_junc = create_cloth_arc_cloth(  1/r , angle_arc , angle_cloth , startnum , junction, n_lanes=n_lanes, lane_offset=lanes_offset )

            # add predecessor and successor
            tmp_junc.add_predecessor(ElementType.road,roads[i].id,cp)
            tmp_junc.add_successor(ElementType.road,roads[j].id,ContactPoint.start)
            startnum += 1
            junction_roads.append(tmp_junc)

    # add junction to the last road aswell since it's not part of the loop
    roads[-1].add_predecessor(ElementType.junction,junction)

    return junction_roads


def create_junction_roads(roads,angles,r,junction=1,spiral_part = 1/3, arc_part = 1/3,startnum=100):
    """ creates all needed roads for some simple junctions
        - 3way crossings (either a T junction, or 120 deg junction)
        - 4way crossing (all 90 degree turns)

        Parameters
        ----------
            roads (list of Road): all roads that should go into the junction

            angles (list of float): the angles which the roads should be going out (see description for what is supported), 
                                    should be defined mathimatically positive (incoming road 0)

            r (float): the radius of the arcs in the junction (will determine the size of the junction)
            
            junction (int): the id of the junction
                default: 1

            spiral_part (float): the part of the curve that should be spirals (two of these) spiral_part*2 + arcpart = angle of the turn
                default: (1/3)

            arc_part (float): the part of the curve that should be an arc:  spiral_part*2 + arcpart = angle of the turn
                default: (1/3)

            startnum (int): start number of the roads in the junctions (will increase with 1 for each road)

        Returns
        -------
            junction_roads (list of Road): a list of all roads needed for all traffic connecting the roads
    """

    # if a straight line is used, calculate the length of it. Some Spiral Magic going on...
    # http://www.jerrymahun.com/index.php/home/open-access/viii-curves/76-chapter-e-spirals?showall=1

    angle = np.pi/2
    angle_cloth = angle*spiral_part 
    spiral_length = 2*abs(angle_cloth*r)

    spiral = EulerSpiral.createFromLengthAndCurvature(spiral_length, STD_START_CLOTH, 1/r)
    (X, Y, _) = spiral.calc(spiral_length, 0, 0, STD_START_CLOTH, 0)

    X0 = X-r*np.sin(angle_cloth)
    Y0 = Y-r*(1-np.cos(angle_cloth))
    linelength = 2*(X0 + r + Y0)

    junction_roads = []
    R=r

    # loop over the roads to get all possible combinations of connecting roads
    for i in range(len(roads)-1):
        # for now the first road is place as base, 
        if i == 0:
            cp = ContactPoint.end
            roads[i].add_successor(ElementType.junction,junction)
        else:
            cp = ContactPoint.start
            roads[i].add_predecessor(ElementType.junction,junction)
        
        for j in range(1+i,len(roads)):
            # check angle needed for junction
            an = np.sign(angles[j]-angles[i]-np.pi)
            an1 = angles[j]-angles[i] -np.pi
            

            #adjust angle if multiple of pi
            if an1 > np.pi: 
                an1 = -(2*np.pi - an1)

            angle_arc = an1*arc_part
            angle_cloth = an1*spiral_part

            # create road, either straight or curved
            n_lanes, lanes_offset = get_lanes_offset(roads[i], roads[j], cp )
            if an == 0:
                # print('n_lanes is ', n_lanes)
                # print('lane offset is ', lanes_offset )
                tmp_junc = create_straight_road(startnum,length= linelength,junction=junction, n_lanes=n_lanes, lane_offset=lanes_offset)
            else: 
                tmp_junc = create_cloth_arc_cloth(  1/r , angle_arc , angle_cloth , startnum , junction, n_lanes=n_lanes, lane_offset=lanes_offset )               

            # add predecessor and successor
            tmp_junc.add_predecessor(ElementType.road,roads[i].id,cp)
            tmp_junc.add_successor(ElementType.road,roads[j].id,ContactPoint.start)
            startnum += 1
            junction_roads.append(tmp_junc)

    # add junction to the last road aswell since it's not part of the loop
    roads[-1].add_predecessor(ElementType.junction,junction)

    return junction_roads


def create_junction(junction_roads, id, roads):
    """ create_junction creates the junction struct for a set of roads


        Parameters
        ----------
            junction_roads (list of Road): all connecting roads in the junction

            id (int): the id of the junction
            
            roads (list of Road): all incomming roads to the junction

        Returns
        -------
            junction (Junction): the junction struct ready to use

    """
    junc = Junction('my junction',id)
    
    for jr in junction_roads:

        conne1 = Connection(jr.successor.element_id,jr.id,ContactPoint.end) 
        _, sign, _ =  _get_related_lanesection(jr, roads[jr.successor.element_id] ) 
        n_lanes = len(jr.lanes.lanesections[-1].leftlanes) 
        for i in range(1, n_lanes+1, 1):
            conne1.add_lanelink( 1*i, 1*sign*i)
            conne1.add_lanelink(-1*i,-1*sign*i)
            junc.add_connection(conne1)

        conne2 = Connection(jr.predecessor.element_id,jr.id,ContactPoint.start)
        _, sign, _ =  _get_related_lanesection(jr, roads[jr.predecessor.element_id]) 
        n_lanes = len(jr.lanes.lanesections[0].leftlanes) 
        for i in range(1, n_lanes+1, 1):
            conne2.add_lanelink( 1*i, 1*sign*i)
            conne2.add_lanelink(-1*i,-1*sign*i)
            junc.add_connection(conne2)

 

    return junc