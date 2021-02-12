import xml.etree.ElementTree as ET

from .helpers import printToFile
from .links import _Link, _Links, create_lane_links
from .enumerations import ElementType, ContactPoint, RoadSide
from .exceptions import UndefinedRoadNetwork, RoadsAndLanesNotAdjusted

import datetime as dt
import warnings
from itertools import combinations
import numpy as np
import copy as cpy

class _Header():
    """ Header creates the header of the OpenDrive file
        
        Parameters
        ----------
            name (str): name of the road 

        Attributes
        ----------
            name (str): name of the scenario 

        Methods
        -------
            get_element()
                Returns the full ElementTree of FileHeader

            get_attributes()
                Returns a dictionary of all attributes of FileHeader

    """
    def __init__(self,name):
        """ Initalize the Header

         Parameters
        ----------
            name (str): name of the road 
        """
        self.name = name

        

    def get_attributes(self):
        """ returns the attributes as a dict of the FileHeader

        """
        retdict = {}
        retdict['name'] = self.name
        retdict['revMajor'] ='1'
        retdict['revMinor'] ='5'
        retdict['date'] = str(dt.datetime.now())
        retdict['north'] = '0.0'
        retdict['south'] = '0.0'
        retdict['east'] = '0.0'
        retdict['west'] = '0.0'
        return retdict

    def get_element(self):
        """ returns the elementTree of the FileHeader

        """
        element = ET.Element('header',attrib=self.get_attributes())

        return element


class Road():
    """ Road defines the road element of OpenDrive
        
        Parameters
        ----------
            road_id (int): identifier of the road

            planview (PlanView): the planview of the road

            lanes (Lanes): the lanes of the road

            road_type (int): type of road (junction)
                Default: -1

            name (str): name of the road (optional)

            rule (TrafficRule): traffic rule (optional)

            signals (Signals): Contains a list of signal objects (optional)

        Attributes
        ----------
            id (int): identifier of the road

            planview (PlanView): the planview of the road

            lanes (Lanes): the lanes of the road

            road_type (int): type of road (junction)
                Default: -1

            name (str): name of the road (optional)

            rule (TrafficRule): traffic rule (optional)

            signals (Signal): Contains a list of Signal objects (optional)
            
            objects (Object): Contains a list of Object objects (optional)

        Methods
        -------
            get_element()
                Returns the full ElementTree of the class

            get_attributes()
                Returns a dictionary of all attributes of the class

            write_xml(filename)
                write a open scenario xml
                
    """
    def __init__(self,road_id,planview,lanes, road_type = -1,name=None, rule=None):
        """ initalize the Road

            Parameters
            ----------
                road_id (int): identifier of the road

                planview (PlanView): the planview of the road

                lanes (Lanes): the lanes of the road

                road_type (int): type of road (junction)
                    Default: -1

                name (str): name of the road (optional)

                rule (TrafficRule): traffic rule (optional)

        """
        self.id = road_id
        self.planview = planview
        self.lanes = lanes
        self.road_type = road_type
        self.name = name
        self.rule = rule
        self.links = _Links()
        self._neighbor_added = 0
        self.successor = None
        self.predecessor = None
        self.lane_offset_suc = 0
        self.lane_offset_pred = 0
        self.adjusted = False
        self.objects = []
        self.signals = []

    def add_successor(self,element_type,element_id,contact_point=None,lane_offset=0):
        """ add_successor adds a successor link to the road
        
        Parameters
        ----------
            element_type (ElementType): type of element the linked road

            element_id (str/int): name of the linked road

            contact_point (ContactPoint): the contact point of the link

        """
        if self.successor:
            raise ValueError('only one successor is allowed')
        self.successor = _Link('successor',element_id,element_type,contact_point)
        self.links.add_link(self.successor)
        self.lane_offset_suc = lane_offset


    def add_predecessor(self,element_type,element_id,contact_point=None,lane_offset=0):
        """ add_successor adds a successor link to the road
        
        Parameters
        ----------
            element_type (ElementType): type of element the linked road

            element_id (str/int): name of the linked road

            contact_point (ContactPoint): the contact point of the link

        """
        if self.predecessor:
            raise ValueError('only one predecessor is allowed')
        self.predecessor = _Link('predecessor',element_id,element_type,contact_point)
        self.links.add_link(self.predecessor)
        self.lane_offset_pred = lane_offset
        

    def add_neighbor(self,element_type,element_id,direction): 
        """ add_neighbor adds a neighbor to a road
        
        Parameters
        ----------
            element_type (ElementType): type of element the linked road

            element_id (str/int): name of the linked road

            direction (Direction): the direction of the link 
        """
        if self._neighbor_added > 1:
            raise ValueError('only two neighbors are allowed')
        suc = _Link('neighbor',element_id,element_type,direction=direction)
    
        self.links.add_link(suc)
        self._neighbor_added += 1
    def add_object(self,road_object):
        """ add_object adds an object to a road and calls a function that ensures unique IDs
        
        Parameters
        ----------
            road_object (Object/list(Object)): object(s) to be added to road 
        
        """
        if isinstance(road_object,list):
            for single_object in road_object:
                single_object._update_id()
            self.objects=self.objects+road_object
        else:
            road_object._update_id()
            self.objects.append(road_object)
            
    def add_object_roadside(self, road_object_prototype, repeatDistance, sOffset=0, tOffset=0, side=RoadSide.both):
        """ add_object_roadside is a convenience function to add a repeating object on side of the road,
            which can only be used after adjust_roads_and_lanes() has been performed
        
        Parameters
        ----------
            road_object_prototype (Object): object that will be used as a basis for generation

            repeatDistance (float): distance between repeated Objects, 0 for continuous

            sOffset (float): start s-coordinate of repeating Objects
            default: 0
            
            tOffset (float): t-offset additional to lane width, sign will be added automatically (i.e. positive if further from roadside)
            default: 0
            
            side (RoadSide): add Objects on both, left or right side 
            default: both
        
        """
        if not self.planview.adjusted:
            raise RoadsAndLanesNotAdjusted("Could not add roadside object because roads and lanes need to be adjusted first. Consider calling 'adjust_roads_and_lanes()'.")
            return
        
        hdg_factors = []
        total_widths = []
        road_objects = []
        s_lanesections = []
        #TODO: handle width parameters apart from a
        for lanesection in self.lanes.lanesections:
            if side != RoadSide.right:
                s_lanesections.append(lanesection.s)
                hdg_factors.append(1)
                total_widths.append(0)
                road_objects.append(cpy.deepcopy(road_object_prototype))
                for lane in lanesection.leftlanes:
                    total_widths[-1] = total_widths[-1] + lane.a
            if side != RoadSide.left:
                s_lanesections.append(lanesection.s)
                hdg_factors.append(-1)
                total_widths.append(0)
                road_objects.append(cpy.deepcopy(road_object_prototype))
                for lane in lanesection.rightlanes:
                    total_widths[-1] = total_widths[-1] + lane.a
        
        for idx, road_object in enumerate(road_objects):
            road_object.t = (total_widths[idx] + tOffset) * hdg_factors[idx]
            road_object.s = sOffset + s_lanesections[idx]
            road_object.hdg = np.pi * (1 + hdg_factors[idx]) / 2
            road_object.repeat(self.planview.get_total_length() - sOffset - s_lanesections[idx], repeatDistance)
        print (repeatDistance)        
        self.add_object(road_objects)

    def add_signal(self,signal):
        """ add_signal adds a signal to a road
        
        
        """
        if isinstance(signal,list):
            for single_signal in signal:
                single_signal._update_id()
            self.signals=self.signals+signal
        else:
            signal._update_id()
            self.signals.append(signal)

        
        
    def get_end_point(self):
        """ get the x, y, and heading, of the end of the road

            Return
            ------
                x (float): the end x coordinate
                y (float): the end y coordinate
                h (float): the end heading

        """
        return self.planview.present_x, self.planview.present_y, self.planview.present_h
    def get_attributes(self):
        """ returns the attributes as a dict of the Road

        """
        retdict = {}
        if self.name:
            retdict['name'] = self.name
        if self.rule:
            retdict['rule'] = self.rule
        retdict['id'] = str(self.id)
        retdict['junction'] = str(self.road_type)
        retdict['length'] = str(self.planview.get_total_length())
        return retdict

    def get_element(self):
        """ returns the elementTree of the FileHeader

        """
        element = ET.Element('road',attrib=self.get_attributes())
        element.append(self.links.get_element())
        element.append(self.planview.get_element())
        element.append(self.lanes.get_element())
        if len(self.signals) > 0:
            signalselement = ET.SubElement(element,'signals')
            for signal in self.signals:
                signalselement.append(signal.get_element())
        if len(self.objects) > 0:
            objectselement = ET.SubElement(element,'objects')
            for road_object in self.objects:
                objectselement.append(road_object.get_element())        
            
        return element

class OpenDrive():
    """ OpenDrive is the main class of the pyodrx to generate an OpenDrive road
        
        Parameters
        ----------
            name (str): name of the road

        Attributes
        ----------
            name (str): name of the road

            roads (list of Road): all roads 

            junctions (list of Junction): all junctions

        Methods
        -------
            get_element()
                Returns the full ElementTree of FileHeader

            add_road(road)
                Adds a road to the opendrive

            add_junction(junction)
                Adds a junction to the opendrive

            write_xml(filename)
                write a open scenario xml
                
    """
    def __init__(self,name):
        """ Initalize the Header

            Parameters
            ----------
            name (str): name of the road 

        """
        self.name = name
        self._header = _Header(self.name)
        self.roads = {}
        self.junctions = []
        #self.road_ids = []

    def add_road(self,road):
        """ Adds a new road to the opendrive

            Parameters
            ----------
                road (Road): the road to add 

        """
        if (len(self.roads) == 0) and road.predecessor:
            ValueError('No road was added and the added road has a predecessor, please add the predecessor first')

        self.roads[str(road.id)] = road        

    def adjust_roads_and_lanes(self): 
        """ Adjust starting position of all geometries of all roads and try to link lanes in neighbouring roads

            Parameters
            ----------

        """
        #adjust roads and their geometries 
        self.adjust_startpoints()

        results = list(combinations(self.roads, 2))

        for r in range(len(results)):
            print('analyzing roads', results[r][0], results[r][1] )
            create_lane_links(self.roads[results[r][0]],self.roads[results[r][1]])  


    def adjust_road_wrt_neighbour(self, road_id, neighbour_id, contact_point, neighbour_type):
        """ Adjust geometries of road[road_id] taking as a successor/predecessor the neighbouring road with id neighbour_id.
            NB Passing the type of contact_point is necessary because we call this function also on roads connecting to 
            to a junction road (which means that the road itself do not know the contact point of the junction road it connects to)


            Parameters
            ----------
            road_id (int): id of the road we want to adjust 

            neighbour_id(int): id of the neighbour road we take as reference (we suppose the neighbour road is already adjusted)

            contact_point(ContactPoint): type of contact point with point of view of roads[road_id]
            
            neighbour_type(str): 'successor'/'predecessor' type of linking to the neighbouring road


        """

        main_road = self.roads[str(road_id)]

        if neighbour_type == 'predecessor':

            if contact_point == ContactPoint.start :    
                x,y,h = self.roads[str(neighbour_id)].planview.get_start_point()
                h = h + np.pi #we are attached to the predecessor's start, so road[k] will start in its opposite direction 
            elif contact_point == ContactPoint.end:
                x,y,h = self.roads[str(neighbour_id)].planview.get_end_point()
            num_lane_offsets = main_road.lane_offset_pred
            x = -num_lane_offsets*3*np.sin(h) + x
            y = num_lane_offsets*3*np.cos(h) + y

            main_road.planview.set_start_point(x,y,h)
            main_road.planview.adjust_geometries()

        elif neighbour_type == 'successor':

            if contact_point == ContactPoint.start:    
                x,y,h = self.roads[str(neighbour_id)].planview.get_start_point()
                h = h + np.pi #we are attached to the predecessor's start, so road[k] will start in its opposite direction 
            elif contact_point == ContactPoint.end:
                x,y,h = self.roads[str(neighbour_id)].planview.get_end_point()
            num_lane_offsets = main_road.lane_offset_suc
            x = num_lane_offsets*3*np.sin(h) + x
            y = -num_lane_offsets*3*np.cos(h) + y
            main_road.planview.set_start_point(x,y,h)
            main_road.planview.adjust_geometries(True)


    def adjust_startpoints(self): 
        """ Adjust starting position of all geoemtries of all roads

            Parameters
            ----------

        """
        
        # Adjust logically connected roads, i.e. move them so they connect geometrically. 
        # Method:
        #    Fix a pre defined roads (if start position in planview is used), other wise fix the first road at 0
        #    Next, in the set of remaining unconnected roads, find and adjust any roads connecting to a already fixed road
        # Loop until all roads have been adjusted, 
        
        
        # adjust the roads that have a fixed start of the planview
        count_total_adjusted_roads = 0
        fixed_road = False
        for k in self.roads:
            if self.roads[k].planview.fixed:
                self.roads[k].planview.adjust_geometries()
                # print('Fixing Road: ' + k)
                count_total_adjusted_roads += 1
                fixed_road = True


        # If no roads are fixed, select the first road is selected as the pivot-road
        if fixed_road is False: 
            self.roads[list(self.roads.keys())[0]].planview.adjust_geometries()
            print('Selecting and adjusting the first road {}'.format(self.roads[list(self.roads.keys())[0] ].id))
            count_total_adjusted_roads += 1
            
        
        while count_total_adjusted_roads < len(self.roads):
            
            count_adjusted_roads = 0

            for k in self.roads: # Check all 

                if self.roads[k].planview.adjusted is False: 

                    # check if it has a normal (road) predecessor 
                    if self.roads[k].predecessor is not None and \
                        self.roads[str(self.roads[k].predecessor.element_id)].planview.adjusted is True and \
                        self.roads[k].predecessor.element_type is not ElementType.junction: 

                        print('  Adjusting {}road {} to predecessor {}'.\
                            format('' if self.roads[k].road_type == -1 else 'connecting ', self.roads[k].id, self.roads[k].predecessor.element_id))
                        self.adjust_road_wrt_neighbour(k, self.roads[k].predecessor.element_id,
                                                    self.roads[k].predecessor.contact_point, 'predecessor')
                        count_adjusted_roads +=1

                        if self.roads[k].road_type != -1 and self.roads[k].successor is not None and self.roads[str(self.roads[k].successor.element_id)].planview.adjusted is False:
                            succ_id = self.roads[k].successor.element_id
                            print('    Adjusting successor connecting road {} in junction {} to road {} '.\
                                format(succ_id, self.roads[k].road_type, self.roads[k].id))
                            if self.roads[k].successor.contact_point == ContactPoint.start:
                                self.adjust_road_wrt_neighbour(succ_id, k, ContactPoint.end, 'predecessor')
                            else:
                                self.adjust_road_wrt_neighbour(succ_id, k, ContactPoint.end, 'successor')
                            count_adjusted_roads +=1

                    # check if geometry has a normal (road) successor 
                    elif self.roads[k].successor is not None and \
                        self.roads[str(self.roads[k].successor.element_id)].planview.adjusted is True and \
                        self.roads[k].successor.element_type is not ElementType.junction: 

                        print('  Adjusting {}successor {} to road {}'.\
                            format('' if self.roads[k].road_type == -1 else 'connecting ', self.roads[k].id, self.roads[k].successor.element_id))
                        self.adjust_road_wrt_neighbour(k, self.roads[k].successor.element_id,
                                                    self.roads[k].successor.contact_point, 'successor')
                        count_adjusted_roads +=1

                        if self.roads[k].road_type != -1 and self.roads[k].predecessor is not None and self.roads[str(self.roads[k].predecessor.element_id)].planview.adjusted is False:
                            pred_id = self.roads[k].predecessor.element_id
                            print('    Adjusting predecessor connecting road {} in junction {} to road {} '.\
                                format(pred_id, self.roads[k].road_type, self.roads[k].id))
                            if self.roads[k].predecessor.contact_point == ContactPoint.start:
                                self.adjust_road_wrt_neighbour(pred_id, k, ContactPoint.start, 'predecessor')
                            else:
                                self.adjust_road_wrt_neighbour(pred_id, k, ContactPoint.start, 'successor')
                            count_adjusted_roads +=1
            
            count_total_adjusted_roads += count_adjusted_roads

            if count_total_adjusted_roads != len(self.roads) and count_adjusted_roads == 0:
                # No more connecting roads found, move to next pivot-road
                raise UndefinedRoadNetwork('Roads are either missing successor, or predecessor to connect to the roads, \n if the roads are disconnected, please add a start position for one of the planviews.')

            

    
    def add_junction(self,junction):
        """ Adds a junction to the opendrive

            Parameters
            ----------
                junction (Junction): the junction to add

        """
        self.junctions.append(junction)

    def get_element(self):
        """ returns the elementTree of the FileHeader

        """
        element = ET.Element('OpenDRIVE')
        element.append(self._header.get_element())
        for r in self.roads:
            element.append(self.roads[r].get_element())
    
        for j in self.junctions:
            element.append(j.get_element())

        return element


    def write_xml(self,filename=None,prettyprint = True):
        """ writeXml writes the open scenario xml file

        Parameters
        ----------
            filename (str): path and filename of the wanted xml file
                Default: name of the opendrive

            prettyprint (bool): pretty print or ugly print?
                Default: True

        """
        if filename == None:
            filename = self.name + '.xodr'
        printToFile(self.get_element(),filename,prettyprint)
        