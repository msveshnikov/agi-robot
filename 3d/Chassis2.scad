// Title: Robot Assembly (Chassis + 4 Thick Wheels + Cabin + Wheel Wells)
// Description: Wheels thickened (4x) and tucked into chassis/cabin pits.
// Modified by: AI Assistant

/*
 * =====================================================================
 * 1. GLOBAL PARAMETERS
 * =====================================================================
 */

// --- Chassis Dimensions ---
chassis_length = 220;  // [mm] Y-axis
chassis_width = 120;   // [mm] X-axis
chassis_height = 40;   // [mm] Z-axis
wall_thickness = 3;    // [mm]

// --- Wheel Parameters (MODIFIED) ---
wheel_diameter = 60;
wheel_thickness = 20;  // INCREASED: 4x thicker (was 5)
wheel_clearance = 4;   // Gap around the wheel in the well
wheel_well_depth = wheel_thickness + 2; // How deep the pits go into the body

// --- Servo/Axle Positions ---
servo_pos_from_front = 50; // Distance from servo center to front
rear_hole_pos_from_back = 40;
cutouts_z_pos = 20; // Height of axles/servos

// --- Calculated Global Axle Y positions ---
// We define these globally so both Chassis and Cabin can align to them
global_y_front_axle = chassis_length - servo_pos_from_front;
global_y_rear_axle = rear_hole_pos_from_back;

// --- Servo Cutouts ---
servo_cutout_width = 24;
servo_cutout_height = 12;
servo_hole_distance = 28;
servo_hole_diameter = 1.5;

// --- Rear Axle Holes ---
rear_hole_diameter = 6;

// --- Chassis Posts ---
post_size = 10;
post_height = 5;

// --- Tread Parameters ---
tread_grooves = 40;
tread_groove_depth = 1.5;
tread_groove_width = 4;

// --- Wheel Mounting Parameters ---
mount_hole_distance = 32;
mount_hole_diameter = 1.5;
servo_horn_recess_depth = 2.5;
servo_spline_hole_diameter = 6;
servo_horn_hub_diameter = 7;
servo_horn_arm_width = 6;

// --- DISTANCE SENSOR (SONAR) ---
sensor_hole_dia = 16.5;      
sensor_spacing = 26;         
sensor_z_pos = chassis_height / 2; 

// --- Quality ---
$fn = 40;

/*
 * =====================================================================
 * 2. MODULE: CHASSIS (With Wheel Pits)
 * =====================================================================
 */
module make_chassis() {
    
    // Sub-module for body
    module chassis_body_shape() {
        difference() {
            cube([chassis_width, chassis_length, chassis_height]);
            translate([wall_thickness, wall_thickness, wall_thickness]) {
                cube([
                    chassis_width - 2 * wall_thickness, 
                    chassis_length - 2 * wall_thickness, 
                    chassis_height
                ]);
            }
        }
    }

    // Sub-module to cut the wheel pits
    module wheel_wells() {
        well_len = wheel_diameter + wheel_clearance * 2;
        well_h = chassis_height + 10; // Cut all the way vertically
        
        // Front Left
        translate([-1, global_y_front_axle - well_len/2, -1])
            cube([wheel_well_depth + 1, well_len, well_h]);
            
        // Front Right
        translate([chassis_width - wheel_well_depth, global_y_front_axle - well_len/2, -1])
            cube([wheel_well_depth + 1, well_len, well_h]);
            
        // Rear Left
        translate([-1, global_y_rear_axle - well_len/2, -1])
            cube([wheel_well_depth + 1, well_len, well_h]);
            
        // Rear Right
        translate([chassis_width - wheel_well_depth, global_y_rear_axle - well_len/2, -1])
            cube([wheel_well_depth + 1, well_len, well_h]);
    }

    // Sub-module for posts
    module mounting_posts() {
        translate([0, 0, chassis_height])
            cube([post_size, post_size, post_height]);
        translate([chassis_width - post_size, 0, chassis_height])
            cube([post_size, post_size, post_height]);
        translate([0, chassis_length - post_size, chassis_height])
            cube([post_size, post_size, post_height]);
        translate([chassis_width - post_size, chassis_length - post_size, chassis_height])
            cube([post_size, post_size, post_height]);
    }

    difference() {
        union() {
            chassis_body_shape();
            mounting_posts();
        }
        
        // Subtract Wheel Wells
        wheel_wells();
        
        y_center_servo = global_y_front_axle;
        z_center = cutouts_z_pos;
        
        // --- Left Servo Mounting ---
        // Adjusted position to be inside the inner wall due to wheel well
        translate([wheel_well_depth - 2, y_center_servo - servo_cutout_width/2, z_center - servo_cutout_height/2])
            cube([wall_thickness + 4, servo_cutout_width, servo_cutout_height]);
        
        // --- Right Servo Mounting ---
        translate([chassis_width - wheel_well_depth - wall_thickness - 2, y_center_servo - servo_cutout_width/2, z_center - servo_cutout_height/2])
            cube([wall_thickness + 4, servo_cutout_width, servo_cutout_height]);

        // Note: Simple holes for servo screws omitted for brevity in thick wall, can be added if needed
        
        // --- Rear Axles ---
        translate([-1, global_y_rear_axle, cutouts_z_pos])
            rotate([0, 90, 0]) cylinder(d = rear_hole_diameter, h = chassis_width + 2);

        // --- Front Sonar ---
        translate([chassis_width/2 + sensor_spacing/2, chassis_length, sensor_z_pos])
            rotate([90, 0, 0]) 
            cylinder(d=sensor_hole_dia, h=wall_thickness*4, center=true);
        
        translate([chassis_width/2 - sensor_spacing/2, chassis_length, sensor_z_pos])
            rotate([90, 0, 0]) 
            cylinder(d=sensor_hole_dia, h=wall_thickness*4, center=true);
    }
}

/*
 * =====================================================================
 * 3. MODULE: WHEEL
 * =====================================================================
 */
module make_wheel() {
    
    module wheel_base() {
        cylinder(d = wheel_diameter, h = wheel_thickness);
    }

    module tread_cutter() {
        if (tread_grooves > 0) {
            for (i = [0 : 360/tread_grooves : 359]) {
                rotate([0, 0, i]) {
                    // Adjusted for dynamic thickness
                    translate([wheel_diameter/2 - tread_groove_depth, -tread_groove_width/2, -1]) {
                        cube([tread_groove_depth + 1, tread_groove_width, wheel_thickness + 2]);
                    }
                }
            }
        }
    }

    module servo_horn_cutout() {
        cutter_h = servo_horn_recess_depth + 1;
        translate([0, 0, wheel_thickness - servo_horn_recess_depth]) {
            hull() {
                cylinder(d = servo_horn_hub_diameter, h = cutter_h);
                translate([mount_hole_distance / 2, 0, 0])
                    cylinder(d = servo_horn_arm_width, h = cutter_h);
                translate([-mount_hole_distance / 2, 0, 0])
                    cylinder(d = servo_horn_arm_width, h = cutter_h);
            }
        }
    }

    module all_holes() {
        hole_h = wheel_thickness + 2;
        translate([0, 0, wheel_thickness / 2]) {
            cylinder(d = servo_spline_hole_diameter, h = hole_h, center = true);
            translate([mount_hole_distance / 2, 0, 0])
                cylinder(d = mount_hole_diameter, h = hole_h, center = true);
            translate([-mount_hole_distance / 2, 0, 0])
                cylinder(d = mount_hole_diameter, h = hole_h, center = true);
        }
    }

    difference() {
        wheel_base();
        tread_cutter();
        servo_horn_cutout();
        all_holes();
    }
}

/*
 * =====================================================================
 * 4. MODULE: CABIN (With Wheel Pits)
 * =====================================================================
 */

// --- CABIN DIMENSIONS ---
cabin_length = 220;          
cabin_width = 120;           
cabin_height = 40;           
taper_angle = 70;            
socket_size = 10;            
socket_depth = 5;            
shelf_thickness = 3;         
shelf_distance_from_roof = 3; 
shelf_drop_offset = 15;      
rear_cutout_width = 80;      
rear_cutout_height = 15;     
camera_hole_dia = 13.5;      
camera_cable_dia = 20;       
camera_position = 30;        
cable_offset = 25;           

module cabin() {
    
    // Calculates position of axles relative to the Cabin's LOCAL center
    // Note: Cabin Center is at global Y=110. 
    // Cabin Local X aligns with Global Y.
    center_y_global = chassis_length / 2;
    
    // Relative positions for wheel cutouts in Cabin Frame
    pos_front_x = global_y_front_axle - center_y_global; // +60mm
    pos_rear_x = global_y_rear_axle - center_y_global;   // -70mm

    module cabin_body() {
        top_reduction = cabin_height / tan(taper_angle);
        hull() {
            translate([0, 0, 0]) cube([cabin_length, cabin_width, 0.1], center = true);
            translate([0, 0, cabin_height]) 
                cube([cabin_length - 2*top_reduction, cabin_width - 2*top_reduction, 0.1], center = true);
        }
    }

    module cabin_cavity() {
        top_reduction = cabin_height / tan(taper_angle);
        difference (){
            hull() {
                translate([0, 0, -1]) cube([cabin_length - 2*wall_thickness, cabin_width - 2*wall_thickness, 0.1], center = true);
                translate([0, 0, cabin_height - wall_thickness]) 
                    cube([cabin_length - 2*top_reduction - 2*wall_thickness, cabin_width - 2*top_reduction - 2*wall_thickness, 0.1], center = true);
            }
            battery_shelf();
        }
    }

    module battery_shelf() {
        actual_z_center = cabin_height - shelf_distance_from_roof - shelf_thickness/2 - shelf_drop_offset;
        reduction = actual_z_center / tan(taper_angle);
        translate([-25, 0, actual_z_center]) {
            cube([cabin_length - 2*reduction - 2*wall_thickness - 50, cabin_width - 2*reduction - 2*wall_thickness, shelf_thickness], center = true);
        }
    }

    module cabin_wheel_arches() {
        // Since the wheel comes up to Z=50 (approx), and cabin starts at Z=40,
        // we need to cut deep into the cabin bottom.
        
        cut_depth = wheel_well_depth; 
        cut_len = wheel_diameter + wheel_clearance * 2;
        cut_h = 25; // Height of the arch inside the cabin
        
        // The cabin is rotated in assembly, but here we work in local coordinates.
        // Local Y is Width. Local X is Length.
        // Wheels are on the Left and Right sides (Y axis extremes).
        
        // Front Axle Cuts (Left and Right)
        translate([pos_front_x, cabin_width/2, 0]) 
            cube([cut_len, cut_depth*2, cut_h], center=true);
        translate([pos_front_x, -cabin_width/2, 0]) 
            cube([cut_len, cut_depth*2, cut_h], center=true);
            
        // Rear Axle Cuts (Left and Right)
        translate([pos_rear_x, cabin_width/2, 0]) 
            cube([cut_len, cut_depth*2, cut_h], center=true);
        translate([pos_rear_x, -cabin_width/2, 0]) 
            cube([cut_len, cut_depth*2, cut_h], center=true);
    }
    
    // Other cutouts
    module other_holes() {
        // Rear battery
        shelf_top_z = cabin_height - shelf_distance_from_roof - shelf_drop_offset;
        translate([-cabin_length/2, 0, shelf_top_z + rear_cutout_height/2])
            cube([60, rear_cutout_width, rear_cutout_height], center = true);
            
        // Roof holes
        translate([cabin_length/2 - camera_position, 0, cabin_height])
            cylinder(h = 20, d = camera_hole_dia, center = true);
        translate([cabin_length/2 - camera_position - cable_offset, 0, cabin_height])
            cylinder(h = 20, d = camera_cable_dia, center = true);
            
        // Mounting sockets
        for(mx = [-1, 1]) for(my = [-1, 1]) {
            translate([mx*(cabin_length/2 - socket_size/2), my*(cabin_width/2 - socket_size/2), 0])
                translate([0, 0, socket_depth/2])
                    cube([socket_size, socket_size, socket_depth + 0.2], center = true);
        }
    }

    difference() {
        union() {
            cabin_body();
            battery_shelf();
        }
        cabin_cavity();
        
        // Cut bottom off cleanly
        translate([0, 0, -10]) cube([cabin_length + 20, cabin_width + 20, 20], center = true);
        
        cabin_wheel_arches();
        other_holes();
    }
}

/* =====================================================================
 *                    MAIN ASSEMBLY
 * =====================================================================
 */

// 1. Render the Chassis
color("yellow") 
    make_chassis();

// 2. Render the Cabin
// Centered on chassis: X=60, Y=110. Rotated so Local X aligns with Global Y.
color("orange") 
    translate([chassis_width/2, chassis_length/2, chassis_height])
    rotate([0,0,90])
    cabin();

// 3. Render 4 Wheels
// New Positioning: Tucked inside the pits.
// Outer face of wheel aligns with chassis outer wall.

// Left Wheels X: Aligned to X=0. Center is at wheel_thickness/2.
x_left_wheel = wheel_thickness/2;

// Right Wheels X: Aligned to X=120. Center is at width - wheel_thickness/2.
x_right_wheel = chassis_width - wheel_thickness/2;

// Front Left
translate([x_left_wheel, global_y_front_axle, cutouts_z_pos])
    rotate([0, 90, 0])
    color("DimGray") make_wheel();

// Front Right
translate([x_right_wheel, global_y_front_axle, cutouts_z_pos])
    rotate([0, -90, 0])
    color("DimGray") make_wheel();

// Rear Left
translate([x_left_wheel, global_y_rear_axle, cutouts_z_pos])
    rotate([0, 90, 0])
    color("DimGray") make_wheel();

// Rear Right
translate([x_right_wheel, global_y_rear_axle, cutouts_z_pos])
    rotate([0, -90, 0])
    color("DimGray") make_wheel();