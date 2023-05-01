from Rasterlamp import rib_cutout_residue, smoothness, thickness_material, arc_height_main_rib
from Rasterlamp import Circle_Coords_Z, Non_Circular_Coords_Z

from solid import *
from solid.utils import *

def Rib_Holes_Rectangular_Chamfer(rib_object, number_of_ribs, dist_ribs, lamp_base, shape, rib_radius, rib_cutout_chamfer, rib_number=0):
    # cuts out the "holes" in the ribs for aesthetics - here with a chamfer

    lamp_cutout_bottom = lamp_base + rib_cutout_residue
    
    # first tests with a symetrical chamfer size
    cdx = rib_cutout_chamfer  # chamfer size in x
    cdy = rib_cutout_chamfer  # chamfer size in y

    smooth_rib_cutout = int(smoothness / (number_of_ribs/2))

    size_cutout = dist_ribs-2*rib_cutout_residue-thickness_material

    increment = size_cutout / smooth_rib_cutout

    for m in range(0, number_of_ribs):

        start_polygon_x = m * dist_ribs + thickness_material / 2 + rib_cutout_residue
        end_polygon_x = start_polygon_x + size_cutout
        
        # defines outer edge coordinates before applying the chamfer 

        if shape == 'non_circular':
            start_polygon_top_y = Non_Circular_Coords_Z(start_polygon_x, rib_number) - rib_cutout_residue
            start_polygon_bot_y = Non_Circular_Coords_Z(start_polygon_x, rib_number) - arc_height_main_rib + rib_cutout_residue
            end_polygon_top_y = Non_Circular_Coords_Z(end_polygon_x, rib_number) - rib_cutout_residue
            end_polygon_bot_y = Non_Circular_Coords_Z(end_polygon_x, rib_number) - arc_height_main_rib + rib_cutout_residue
        elif shape == 'circular':
            start_polygon_top_y = Circle_Coords_Z(start_polygon_x, rib_radius) - rib_cutout_residue
            start_polygon_bot_y = Circle_Coords_Z(start_polygon_x, rib_radius) - arc_height_main_rib + rib_cutout_residue
            end_polygon_top_y = Circle_Coords_Z(end_polygon_x, rib_radius) - rib_cutout_residue
            end_polygon_bot_y = Circle_Coords_Z(end_polygon_x, rib_radius) - arc_height_main_rib + rib_cutout_residue

        # starting the polygon including the chamfer
        # test if the distance between top and bottom start is enough to do a chamfer
        # if the distance is smaller than 2*cdy - reduce the chamfer --> cdy_applied 

        if min((start_polygon_top_y-start_polygon_bot_y),(start_polygon_top_y-lamp_cutout_bottom)) <= 2*cdy:
            cdy_applied = min((start_polygon_top_y-start_polygon_bot_y),(start_polygon_top_y-lamp_cutout_bottom))/2
        else:
            cdy_applied = cdy

        polygon_rib_cutout_top = [[start_polygon_x, start_polygon_top_y-cdy_applied]]

        if start_polygon_bot_y < lamp_cutout_bottom:
            polygon_rib_cutout_bot = [[start_polygon_x, lamp_cutout_bottom+cdy_applied]]
        else:
            polygon_rib_cutout_bot = [[start_polygon_x, start_polygon_bot_y+cdy_applied]]
        
        if end_polygon_x - start_polygon_x <= 2*cdx:
            continue
        
        # curved section of top cutout
        for n in range(0, smooth_rib_cutout + 1):
            polygon_1_x = start_polygon_x + cdx + n * increment
            
            # calculate the top cutout y-coordinates
            if shape == 'non_circular':
                polygon_1_y = Non_Circular_Coords_Z(polygon_1_x, rib_number) - rib_cutout_residue
            elif shape == 'circular':
                polygon_1_y = Circle_Coords_Z(polygon_1_x, rib_radius) - rib_cutout_residue

            # case 1 & 1,5: cutout with circular and flat bottom at rib end
            if polygon_1_y < lamp_cutout_bottom:
                break

            # normal cutout, case 2 and case 3
            else:
                polygon_rib_cutout_top.append([polygon_1_x, polygon_1_y])
                
                if polygon_1_x >= end_polygon_x - cdx:   
                    
                    # no chamfer if the potential end_polygon_top_y is below the lamp_cutout_bottom
                    if end_polygon_top_y <= lamp_cutout_bottom:
                        continue

                    # test if the distance between top and bottom start is enough to do a chamfer
                    # if the distance is smaller than 2*cdy - reduce the chamfer --> cdy_applied 
                    if min(end_polygon_top_y-end_polygon_bot_y, end_polygon_top_y-lamp_cutout_bottom) <= 2*cdy:
                        cdy_applied = min(end_polygon_top_y-end_polygon_bot_y, end_polygon_top_y-lamp_cutout_bottom)/2
                    else:
                        cdy_applied = cdy                                                            
                      
                    polygon_rib_cutout_top.append([end_polygon_x, end_polygon_top_y - cdy_applied])

                    break


        # the "last" coords are needed for the bottom cutout to decide which edge case to choose from
        last_x_top, last_y_top = polygon_rib_cutout_top[-1]

        # curved section of bottom cutout
        for p in range(0, smooth_rib_cutout + 1):
            polygon_2_x = start_polygon_x + cdx + p * increment
            
            # calculate the bottom cutout y-coordinates
            if shape == 'non_circular':
                polygon_2_y = Non_Circular_Coords_Z(polygon_2_x, rib_number) - arc_height_main_rib + rib_cutout_residue
            elif shape == 'circular':
                polygon_2_y = Circle_Coords_Z(polygon_2_x, rib_radius) - arc_height_main_rib + rib_cutout_residue

            # check the edge cases, if the coords should be appended to the polygon
            # all cases except "normal"
            if polygon_2_y < lamp_cutout_bottom:
                last_x, _ = polygon_rib_cutout_bot[-1]
                polygon_rib_cutout_bot.append([last_x + increment, lamp_cutout_bottom])
                polygon_rib_cutout_bot.append([last_x_top, lamp_cutout_bottom])
                break

            # normal cutout
            else:
                polygon_rib_cutout_bot.append([polygon_2_x, polygon_2_y])

                if polygon_2_x >= end_polygon_x - cdx:
                    polygon_rib_cutout_bot.append([end_polygon_x-cdx, polygon_2_y])
                    polygon_rib_cutout_bot.append([end_polygon_x, end_polygon_bot_y + cdy])
                    break
            
        # put top and (reversed) bottom line together to form the cutout polygon
        polygon_rib_cutout = polygon_rib_cutout_top + polygon_rib_cutout_bot[::-1]

        rib_object = difference()(
            rib_object,
            polygon(polygon_rib_cutout)
        )

    return rib_object


def Rib_Holes_Rectangular(rib_object, number_of_ribs, dist_ribs, lamp_base, shape, rib_radius, rib_number=0):
    # cuts out the "holes" in the ribs for aesthetics
    
    lamp_cutout_bottom = lamp_base + rib_cutout_residue

    smooth_rib_cutout = int(smoothness / number_of_ribs)

    size_cutout = dist_ribs-2*rib_cutout_residue-thickness_material

    increment = size_cutout / smooth_rib_cutout

    for m in range(0, number_of_ribs):

        start_polygon_x = m * dist_ribs + thickness_material / 2 + rib_cutout_residue
        
        if shape == 'non_circular':
            start_polygon_top_y = Non_Circular_Coords_Z(start_polygon_x, rib_number) - rib_cutout_residue
            start_polygon_bot_y = Non_Circular_Coords_Z(start_polygon_x, rib_number) - arc_height_main_rib + rib_cutout_residue
        elif shape == 'circular':
            start_polygon_top_y = Circle_Coords_Z(start_polygon_x, rib_radius) - rib_cutout_residue
            start_polygon_bot_y = Circle_Coords_Z(start_polygon_x, rib_radius) - arc_height_main_rib + rib_cutout_residue


        # set the first polygon coordinates 
        polygon_rib_cutout_top = [[start_polygon_x, start_polygon_top_y]]

        if start_polygon_bot_y < lamp_cutout_bottom:
            polygon_rib_cutout_bot = [[start_polygon_x, lamp_cutout_bottom]]
        else:
            polygon_rib_cutout_bot = [[start_polygon_x, start_polygon_bot_y]]

        # curved section of top cutout
        for n in range(0, smooth_rib_cutout + 1):
            polygon_1_x = start_polygon_x + n * increment
            
            # calculate the top cutout y-coordinates
            if shape == 'non_circular':
                polygon_1_y = Non_Circular_Coords_Z(polygon_1_x, rib_number) - rib_cutout_residue
            elif shape == 'circular':
                polygon_1_y = Circle_Coords_Z(polygon_1_x, rib_radius) - rib_cutout_residue

            # check the edge cases, if the coords should be appended to the polygon
            # case 1: triangular cutout at rib end
            # case 1,5: cutout with circular and flat bottom at rib end
            if polygon_1_y < lamp_cutout_bottom:
                break

            # normal cutout, case 2 and case 3
            else:
                polygon_rib_cutout_top.append([polygon_1_x, polygon_1_y])

        # the "last" coords are needed for the bottom cutout to decide which edge case to choose from
        last_x_top, last_y_top = polygon_rib_cutout_top[-1]

        # curved section of bottom cutout
        for p in range(0, smooth_rib_cutout + 1):
            polygon_2_x = start_polygon_x + p * increment
            
            # calculate the top cutout y-coordinates
            if shape == 'non_circular':
                polygon_2_y = Non_Circular_Coords_Z(polygon_2_x, rib_number) - arc_height_main_rib + rib_cutout_residue
            elif shape == 'circular':
                polygon_2_y = Circle_Coords_Z(polygon_2_x, rib_radius) - arc_height_main_rib + rib_cutout_residue

            # check the edge cases, if the coords should be appended to the polygon
            # all cases except "normal"
            if polygon_2_y < lamp_cutout_bottom:
                last_x, _ = polygon_rib_cutout_bot[-1]
                polygon_rib_cutout_bot.append([last_x + increment, lamp_cutout_bottom])
                polygon_rib_cutout_bot.append([last_x_top, lamp_cutout_bottom])
                break

            # normal cutout
            else:
                polygon_rib_cutout_bot.append([polygon_2_x, polygon_2_y])

        last_x_bot, last_y_bot = polygon_rib_cutout_bot[-1]  # will be needed für stiffening stuff in cutouts

        polygon_rib_cutout = polygon_rib_cutout_top + polygon_rib_cutout_bot[::-1]

        rib_object = difference()(
            rib_object,
            polygon(polygon_rib_cutout)
        )

    return rib_object