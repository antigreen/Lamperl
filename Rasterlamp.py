# source venv/bin/activate

"""
Python Script for generating a lamp shade
manufacturing method: laser cutting

OpenSCAD needs to be installed to run script properly
--> http://www.openscad.org/

SolidPython is a Python for OpenSCAD
by Evan Jones, evan_t_jones@mac.com
--> https://github.com/SolidCode/SolidPython

Copyright (C) 2019 Thomas Minke - tom@der-pfusch.de

License (similar and successors):
Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)
https://creativecommons.org/licenses/by-nc-sa/3.0/

"""

from solid import *
from solid.utils import *
import math
import os
import subprocess

# -------------------------------------------------------------------------------------------------------
# adapt values below to define your lamp shade properties

# Path & Filename for output files
file_path = '/home/tom/Schreibtisch/'
file_name = 'Rasterlamp'   # without any .xxx ending!


# Base Variables
lamp_width_x = 350  # in [mm] - for construction the longer side
lamp_width_y = 250  # in [mm] - for construction the shorter side
lamp_height = 100    # in [mm]
arc_height_main_rib = 30  # in [mm] - width of arc
number_of_ribs_long_side = 25   # just odd number - for the longer side - min. 3
number_of_ribs_short_side = -1   # just odd number - for the shorter side -  will be calculated if value = -1
dist_rib_edge = 10  # in [mm] - distance last rib from the edge

thickness_material = 3.0    # in [mm] - thickness of used material for lamp - adapt to your material thickness used
                            #           for manufacturing
tolerance = 2.0             # in [mm] - tolerance for mechanical clearence 0.1-0.2mm recommended
                            # on a LaserCutter calculate Kerf in tolerance - if Kerf is 0.2mm -->
                            # set tolerance to 0mm

rib_cutout_chamfer = 2      # in [mm] - chamfer in rib cutout corners - esthetics :o)
                            # see: Rib Hole cutouts (non) circular ribs
rib_cutout_residue = 4.0    # in [mm] - remaining material left after cutout - recommencation --> depends on material...and aesthetics

# set view for showing in Openscad
# view = "2D_plotting"      # drawstyle in SCAD 2D_plotting for 2D show
# view = "2D_cutting"     # drawstyle in SCAD 2D_cutting for generating G-Code
view = "3D_show"        # drawstyle in SCAD 2D_plotting for generating G-Code, 3D_show for show

# adapt values above to define your lamp shade properties
# -------------------------------------------------------------------------------------------------------

epsilon = 0.02      # very small adder for better cutting in OpenSCAD
smoothness = 100    # higher number, smoother curves, langer calculation times


# -------------------------------------------------------------------------------------------------------
# General calculations

# reverse lamp_width_x and lamp_width_y if lamp_width_y > lamp_width_x
if lamp_width_x < lamp_width_y:
    print("lamp_width_x < lamp_width_y: change necessary")
    tmp = lamp_width_x
    lamp_width_x = lamp_width_y
    lamp_width_y = tmp
    print("new values are lamp_width_x={0} & lamp_width_y={1}".format(lamp_width_x, lamp_width_y))

# calculation of lamp outer shell circle radius acc. to Pytagoras - see drawing
radius_0_y = (((lamp_width_x / 2) ** 2 + lamp_height ** 2) / (2 * lamp_height))     # bigger radius
radius_0_x = (((lamp_width_y / 2) ** 2 + lamp_height ** 2) / (2 * lamp_height))     # smaller radius

# error check - lamp height > radius_x_0
if lamp_height > radius_0_x:
    radius_0_x = lamp_height
    print('Error: lamp height > (small side lamp)/2 ')
    print("small side lamp width changed to {0}[mm]".format(2*radius_0_x))

# calculation rib numbers & rib distances

# input error check and divide by 2 due to symmetry
def Rib_Error_Check(number_ribs):
    if number_ribs == 0 or number_ribs == 1:  # check for 0 or 1 as rib input
        number_ribs = 3
        print('minumum 3 ribs! Ribs number changed to 3')
    elif number_ribs % 2 == 0:  # check for odd number and add 1 for even number
        number_ribs += 1
        print('one rib added - just odd numbers allowed')
        print('new number of ribs: ', number_ribs)
    return number_ribs


# due to symmetry half number of ribs + Rib_0 & type conv. to int necessary due to division
number_of_ribs_x = int((Rib_Error_Check(number_of_ribs_long_side) + 1) / 2)

# calculate distance between ribs in x
dist_ribs_x = (lamp_width_x / 2 - dist_rib_edge) / (number_of_ribs_x - 1)

# same for y, but option "-1 - automated calculation" included
if number_of_ribs_short_side != -1:
    number_of_ribs_y = int((Rib_Error_Check(number_of_ribs_short_side) + 1) / 2)
    dist_ribs_y = (lamp_width_y / 2 - dist_rib_edge) / (number_of_ribs_y - 1)
else:
    number_of_ribs_y = math.ceil((lamp_width_y / 2 - dist_rib_edge) / dist_ribs_x) + 1  # +1 to add rib at y=0
    dist_ribs_y = (lamp_width_y / 2 - dist_rib_edge) / (number_of_ribs_y - 1)


# calculation lamp_base - baseline, where the lamp should finally sit on - different in calculation for x&y
lamp_base_x = radius_0_x - lamp_height
lamp_base_y = radius_0_y - lamp_height

# General calculations
# -------------------------------------------------------------------------------------------------------


# Calculate circle coordinate 'x' at given 'z' & 'radius'
def Circle_Coords_X(z_coord, radius):

    if (radius ** 2 - z_coord ** 2) < 0:
        return -1
    else:
        return math.sqrt(radius ** 2 - z_coord ** 2)


# Calculate circle coordinate 'z' at given 'x' & 'radius'
def Circle_Coords_Z(x_coord, radius):

    if (radius ** 2 - x_coord ** 2) < 0:
        return -1
    else:
        return math.sqrt(radius ** 2 - x_coord ** 2)


def Non_Circular_Coords_Z(x_coord, rib_number):
    radius = radius_0_x - (radius_0_y - Circle_Coords_Z(x_coord, radius_0_y))
    z_coord = Circle_Coords_Z(rib_number * dist_ribs_y, radius)
    return z_coord


def Rect_Rib_Cutouts(rib_object, number_of_ribs, dist_ribs, cutout_location, lamp_base, shape, rib_radius, rib_number=0):
    # cuts out the intersecting parts of the ribs

    for k in range(0, number_of_ribs):

        if shape == 'circular':
            z_coord = Circle_Coords_Z(k*dist_ribs, rib_radius)  # on circle from which rectangle is cut out

        elif shape == 'non_circular':
            z_coord = Non_Circular_Coords_Z(k * dist_ribs, rib_number)

        if z_coord != -1:                                   # compliance - circle coordinate was calculated correctly

            if z_coord - arc_height_main_rib < lamp_base:   # check if coord approaching lamp_base - room for cutout
                cutout_height = z_coord - lamp_base         # if yes - limit cutout height
            else:
                cutout_height = arc_height_main_rib

            if cutout_location == "inner":                  # long ribs are cut on the inner perimeter
                                                            # short ones on the outer perimeter
                if z_coord - arc_height_main_rib > lamp_base:
                    z_coord -= arc_height_main_rib          # in circular area inner perimeter
                else:
                    z_coord = lamp_base                     # in flat area cut on flats

            cutout_square = translate([k*dist_ribs, z_coord]) (
                square(size=[thickness_material+2*tolerance, cutout_height], center=True)
                )

            if cutout_location == "outer":                  # enlarge very tiny cutouts towards the top
                cutout_square += translate([k*dist_ribs-(thickness_material/2+tolerance), z_coord])(
                square(size=[thickness_material+2*tolerance, 500], center=False)
                )

            rib_object = rib_object - cutout_square

    return rib_object


def Rib_Holes_Rectangular(rib_object, number_of_ribs, dist_ribs, lamp_base, shape, rib_radius, rib_number=0):
    # cuts out the "holes" in the ribs for aesthetics
    
    smooth_rib_cutout = int(smoothness / number_of_ribs)

    increment = (dist_ribs-2*rib_cutout_residue-thickness_material) / smooth_rib_cutout

    for m in range(0, number_of_ribs):

        start_polygon_x = m * dist_ribs + thickness_material / 2 + rib_cutout_residue
        
        if shape == 'non_circular':
            start_polygon_top_y = Non_Circular_Coords_Z(start_polygon_x, rib_number) - rib_cutout_residue
            start_polygon_bot_y = Non_Circular_Coords_Z(start_polygon_x, rib_number) - arc_height_main_rib + rib_cutout_residue
        elif shape == 'circular':
            start_polygon_top_y = Circle_Coords_Z(start_polygon_x, rib_radius) - rib_cutout_residue
            start_polygon_bot_y = Circle_Coords_Z(start_polygon_x, rib_radius) - arc_height_main_rib + rib_cutout_residue


        polygon_rib_cutout_top = [[start_polygon_x, start_polygon_top_y]]
        polygon_rib_cutout_bot = [[start_polygon_x, start_polygon_bot_y]]

        lamp_cutout_bottom = lamp_base + rib_cutout_residue

        # curved section of top cutout
        for n in range(0, smooth_rib_cutout + 1):
            polygon_1_x = start_polygon_x + n * increment
            
            if shape == 'non_circular':
                polygon_1_y = Non_Circular_Coords_Z(polygon_1_x, rib_number) - rib_cutout_residue
            elif shape == 'circular':
                polygon_1_y = Circle_Coords_Z(polygon_1_x, rib_radius) - rib_cutout_residue

            # case 1: triangular cutout at rib end (complete polygon)
            if (polygon_1_y < lamp_cutout_bottom) and (start_polygon_bot_y < lamp_cutout_bottom):
                last_x, _ = polygon_rib_cutout_top[-1]
                polygon_rib_cutout_top.append([last_x, lamp_cutout_bottom])
                polygon_rib_cutout_top.append([start_polygon_x, lamp_cutout_bottom])
                break

            # case 1,5: cutout with circular and flat bottom at rib end
            elif polygon_1_y < lamp_cutout_bottom:
                break

            # normal cutout, case 2 and case 3
            else:
                polygon_rib_cutout_top.append([polygon_1_x, polygon_1_y])

        last_x_top, last_y_top = polygon_rib_cutout_top[-1]

        # curved section of bottom cutout
        for p in range(0, smooth_rib_cutout + 1):
            polygon_2_x = start_polygon_x + p * increment
            
            if shape == 'non_circular':
                polygon_2_y = Non_Circular_Coords_Z(polygon_2_x, rib_number) - arc_height_main_rib + rib_cutout_residue
            elif shape == 'circular':
                polygon_2_y = Circle_Coords_Z(polygon_2_x, rib_radius) - arc_height_main_rib + rib_cutout_residue

            # case 1
            if (start_polygon_bot_y < lamp_cutout_bottom) and (last_y_top <= lamp_cutout_bottom):
                break

            # case 3
            elif (start_polygon_bot_y < lamp_cutout_bottom) and (last_y_top > lamp_cutout_bottom):
                polygon_rib_cutout_bot.append([polygon_2_x, lamp_cutout_bottom])
                polygon_rib_cutout_bot.append([last_x_top, lamp_cutout_bottom])
                break

            # case 1,5 & 2
            elif polygon_2_y < lamp_cutout_bottom:
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


def DrawRib_Circular(rib_radius, lamp_base, move_direction):
    # generates circular ribs (just the half of it) (rib_y[0] and ribs_x[n])

    # create the half-rib
    rib_object = difference()(

        # create an arc - this is the upper lamp shape
        arc(rad=rib_radius, start_degrees=0, end_degrees=90, segments=smoothness*10),

        # cut away the same arc, just shifted to -arc_height_main_rib in y
        translate([0, -arc_height_main_rib])(
            arc(rad=rib_radius, start_degrees=0, end_degrees=90, segments=smoothness*10)
        ),

        # cut away anything that is below the lamp base (radius_0-lamp_height)
        translate([-epsilon, -radius_0_y])(
            square(size=[radius_0_y + 2 * epsilon, lamp_base + radius_0_y], center=False)
        )
    )

    # square cutouts rib intersection (for putting ribs together)
    if move_direction == "y":       # calculation of rib_y_0
        number_of_ribs = number_of_ribs_x
        dist_ribs = dist_ribs_x
        cutout_location = "inner"
    elif move_direction == "x":     # calculation of rib_x_[n]
        number_of_ribs = number_of_ribs_y
        dist_ribs = dist_ribs_y
        cutout_location = "outer"
    else:
        print("error - rib cutout calc in Draw_Rib_circular - move_direction not 'x' or 'y'")
        return rib_object

    rib_object = Rect_Rib_Cutouts(rib_object, number_of_ribs, dist_ribs, cutout_location, lamp_base, 'circular', rib_radius)
 
    # Rib Hole Rectangular cutouts circular ribs
    rib_object = Rib_Holes_Rectangular(rib_object, number_of_ribs, dist_ribs, lamp_base, 'circular', rib_radius)

    # mirror the half-rib to create full one
    rib_object = rib_object + mirror([1, 0, 0])(rib_object)

    return rib_object


def DrawRib_NonCircular(rib_number, lamp_base):
    # generates non-circular ribs (just the half of it) in y-direction

    increment = lamp_width_x / (2 * smoothness)

    polygon_coords_outer = [[0, -2 * epsilon]]
    polygon_coords_inner = [[0, -2 * epsilon]]

    # create 2 polygons (outer and inner)
    # outer for the outer perimeter - Geometry see drawing
    # inner for the inner perimeter
    for j in range(0, smoothness+1):

        z_coord = Non_Circular_Coords_Z(j*increment, rib_number)
        polygon_coords_outer.append([j * increment, z_coord])
        polygon_coords_inner.append([j * increment, z_coord-arc_height_main_rib])

    # subtract inner from outer polygon, remove base
    rib_object = difference()(
        polygon(polygon_coords_outer),
        polygon(polygon_coords_inner),
        translate([-epsilon, -lamp_width_x+lamp_base])(
            square(size=[lamp_width_x+2*epsilon, lamp_width_x], center=False)
            )
        )

    # Square cutouts rib intersection non circular (for putting ribs together)
    dist_ribs = dist_ribs_x
    cutout_location = "inner"
    rib_radius = 0
    number_of_ribs = number_of_ribs_x

    rib_object = Rect_Rib_Cutouts(rib_object, number_of_ribs, dist_ribs, cutout_location, lamp_base, 'non_circular', rib_radius, rib_number)

    # Rib Hole Rectangular cutouts non circular ribs
    rib_object = Rib_Holes_Rectangular(rib_object, number_of_ribs, dist_ribs, lamp_base, 'non_circular', rib_radius, rib_number)

    # mirror the half-rib to create full one
    rib_object = rib_object + mirror([1, 0, 0])(rib_object)

    return rib_object


def Generate_OpenSCAD_view(rib_object, direction, i):
    # 2D-view
    if direction == "x" and view == "2D_plotting":
        rib_object = translate([0, -lamp_base_x - i * lamp_height])(rib_object)
    elif direction == "y" and view == "2D_plotting":
        rib_object = translate([lamp_width_x, -lamp_base_y - i * lamp_height])(rib_object)
    elif direction == "ny" and view == "2D_plotting":
        rib_object = translate([lamp_width_x, -i * lamp_height])(rib_object)

    if direction == "x" and view == "2D_cutting":
        rib_object = translate([0, -lamp_base_x -i * arc_height_main_rib + 1/(i+1)*10, 0])(rib_object)
    elif direction == "y" and view == "2D_cutting":
        rib_object = translate([lamp_width_x, -lamp_base_y - i * arc_height_main_rib + 1/(i+1)*10, 0])(rib_object)
    elif direction == "ny" and view == "2D_cutting":
        rib_object = translate([lamp_width_x, - (i + 3) * arc_height_main_rib + 1/(i+1)*10, 0])(rib_object)

    # 3D-view
    # extrude, rotate, move to rib spot, down to lamp base & mirror 2 times to create 360° lamp
    elif direction == "x" and view == "3D_show":
        rib_object = linear_extrude(height=thickness_material, center=True)(rib_object)
        rib_object = rotate(v=[1, 0, 0], a=90)(rib_object)
        rib_object = rotate(v=[0, 0, 1], a=90)(rib_object)
        rib_object = right(i * dist_ribs_x)(rib_object)
        rib_object = down(lamp_base_x)(rib_object)
        if i:
            rib_object = rib_object + mirror([1, 0, 0])(rib_object)

    elif direction == "y" and view == "3D_show":
        rib_object = linear_extrude(height=thickness_material, center=True)(rib_object)
        rib_object = rotate(v=[1, 0, 0], a=90)(rib_object)
        rib_object = forward(i * dist_ribs_y)(rib_object)
        rib_object = down(lamp_base_y)(rib_object)
        rib_object = color(Brass)(rib_object)

    elif direction == "ny" and view == "3D_show":
        rib_object = linear_extrude(height=thickness_material, center=True)(rib_object)
        rib_object = rotate(v=[1, 0, 0], a=90)(rib_object)
        rib_object = forward(i * dist_ribs_y)(rib_object)
        rib_object = down(lamp_base_x)(rib_object)
        rib_object = rib_object + mirror([0, 1, 0])(rib_object)
        rib_object = color(Red)(rib_object)

    else:
        print ("Fehler")

    # TODO: create a visualisation of a complete top & bottom lamp
    # rib_object = rib_object + mirror([0, 0, 1])(rib_object)

    return rib_object


if __name__ == "__main__":
    SCAD_codelist = []          # empty list for storing the different solid-python objects

    # calculate circular ribs Rib_y_0 and Rib_x_[n]

    # the "x", "y" and "ny" indicators are for providing the movement direction of ribs as well as
    # square cutout indicators

    # calculate circular ribs Rib_y_0
    rib_0_y = Generate_OpenSCAD_view(DrawRib_Circular(radius_0_y, lamp_base_y, "y"), "y", 0)
    SCAD_codelist.append(scad_render(rib_0_y))  # render the SCAD-objects to SCAD-text

    # calculate circular ribs Rib_x_[n]

    for k in range(0, number_of_ribs_x):
        if k == 0:
            radius = radius_0_x
        else:
            radius = radius_0_x - (radius_0_y - Circle_Coords_Z(k * dist_ribs_x, radius_0_y))

        rib_x_n = Generate_OpenSCAD_view(DrawRib_Circular(radius, lamp_base_x, "x"), "x", k)
        SCAD_codelist.append(scad_render(rib_x_n))  # render the SCAD-objects to SCAD-text

    # calculate non-circular ribs Rib_y_[1...m]
    
    
    for m in range(1, number_of_ribs_y):    # start at '1' cause rib_0_y is already created
        rib_y_n = Generate_OpenSCAD_view(DrawRib_NonCircular(m, lamp_base_x), "ny", m)
        SCAD_codelist.append(scad_render(rib_y_n))  # render the SCAD-objects to SCAD-text
    
    # combine the SCAD-text and write to the named file
    
    SCAD_code = "\n".join(SCAD_codelist)  # join the object fragments from SCAD_codelist together

    file_name_scad = file_name + '.scad'
    file_name_dxf = file_name + '.dxf'
    file_name_svg = file_name + '.svg'
    file_name_png = file_name + '.png'

    file_out_scad = os.path.join(file_path, file_name_scad)
    file_out_dxf = os.path.join(file_path, file_name_dxf)
    file_out_svg = os.path.join(file_path, file_name_svg)
    file_out_png = os.path.join(file_path, file_name_png)

    f = open(file_out_scad, "w")
    f.write(SCAD_code)
    f.close()

    # export 2D-View as dxf in same folder as SCAD-file
    if view == "2D_plotting":
        subprocess.run(["openscad", "-o", file_out_dxf, file_out_scad])
        subprocess.run(["openscad", "-o", file_out_svg, file_out_scad])

    elif view == "3D_show":
        subprocess.run(["openscad", "-o", file_out_png, "--imgsize=1600,1200",
                        "--camera=0,-100,100,60,0,20,1200", file_out_scad])
        # examples for working command line options
        # for more beautiful pics use "--render" before camera command, but it needs time....

        # openscad -o Rasterlamp2.png --viewall --imgsize=1600,1200 --camera=250,-300,150,0,0,0 Rasterlamp2.scad
        # openscad -o Rasterlamp2.png --imgsize=1600,1200 --camera=0,-100,100,50,0,0,1200 Rasterlamp2.scad

    # open OpenSCAD for viewing the created lamp
    # subprocess.run(["openscad", file_out_scad])
