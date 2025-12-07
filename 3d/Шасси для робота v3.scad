// Title: Robot Assembly (Chassis + 4 Wheels)
// Description: Parametric chassis with 4 wheels positioned 2mm outward.
// Combined and Modified by: AI Assistant

/*
 * =====================================================================
 * 1. GLOBAL PARAMETERS (Merged)
 * =====================================================================
 */

// --- Chassis Dimensions ---
chassis_length = 220;  // [mm] Y-axis
chassis_width = 120;   // [mm] X-axis
chassis_height = 40;   // [mm] Z-axis
wall_thickness = 3;    // [mm]

// --- Servo Cutouts ---
servo_cutout_width = 24;
servo_cutout_height = 12;
servo_hole_distance = 28;
servo_hole_diameter = 1.5;
servo_pos_from_front = 50; // Distance from servo center to front

// --- Rear Axle Holes ---
rear_hole_diameter = 6;
rear_hole_pos_from_back = 40;

// --- Vertical Positioning ---
cutouts_z_pos = 20; // Height of axles/servos

// --- Chassis Posts ---
post_size = 10;
post_height = 5;

// --- Wheel Parameters ---
wheel_diameter = 60;
wheel_thickness = 5;
wheel_offset = 2; // [mm] Distance from chassis wall to wheel

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

// --- Quality ---
$fn = 30;

/*
 * =====================================================================
 * 2. MODULE: CHASSIS
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
        
        y_center_servo = chassis_length - servo_pos_from_front;
        z_center = cutouts_z_pos;
        
        // --- Left Servo ---
        translate([-1, y_center_servo - servo_cutout_width/2, z_center - servo_cutout_height/2])
            cube([wall_thickness + 2, servo_cutout_width, servo_cutout_height]);
        translate([wall_thickness/2, y_center_servo - servo_hole_distance/2, z_center])
            rotate([0, 90, 0]) cylinder(d=servo_hole_diameter, h=wall_thickness*3, center=true);
        translate([wall_thickness/2, y_center_servo + servo_hole_distance/2, z_center])
            rotate([0, 90, 0]) cylinder(d=servo_hole_diameter, h=wall_thickness*3, center=true);
        
        // --- Right Servo ---
        translate([chassis_width - wall_thickness, y_center_servo - servo_cutout_width/2, z_center - servo_cutout_height/2])
            cube([wall_thickness + 2, servo_cutout_width, servo_cutout_height]);
        translate([chassis_width - wall_thickness/2, y_center_servo - servo_hole_distance/2, z_center])
            rotate([0, 90, 0]) cylinder(d=servo_hole_diameter, h=wall_thickness*3, center=true);
        translate([chassis_width - wall_thickness/2, y_center_servo + servo_hole_distance/2, z_center])
            rotate([0, 90, 0]) cylinder(d=servo_hole_diameter, h=wall_thickness*3, center=true);
        
        // --- Rear Axles ---
        translate([-1, rear_hole_pos_from_back, cutouts_z_pos])
            rotate([0, 90, 0]) cylinder(d = rear_hole_diameter, h = wall_thickness + 2);
        translate([chassis_width - wall_thickness, rear_hole_pos_from_back, cutouts_z_pos])
            rotate([0, 90, 0]) cylinder(d = rear_hole_diameter, h = wall_thickness + 2);
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
 * 4. ASSEMBLY (Main Code)
 * =====================================================================
 */

// 1. Render the Chassis
color("yellow") 
    make_chassis();

// Calculated Y coordinates
y_front = chassis_length - servo_pos_from_front;
y_rear = rear_hole_pos_from_back;

// Calculated X coordinates for wheels (2mm gap)
// Left wheel origin: Gap (2mm) + Thickness (5mm) = 7mm from edge
x_left_wheel = 0 - wheel_offset - wheel_thickness; 
// Right wheel origin: Width + Gap (2mm) + Thickness (5mm)
x_right_wheel = chassis_width + wheel_offset + wheel_thickness; 

// 2. Render 4 Wheels
// Note: We rotate the wheels so the "Recess" (Servo horn side) faces the chassis.
// The recess is at the top of the cylinder (Z=thickness).

// Front Left
*translate([x_left_wheel, y_front, cutouts_z_pos])
    rotate([0, 90, 0]) // Rotate 90 deg so top faces Right (towards chassis)
    color("White") make_wheel();

// Front Right
*translate([x_right_wheel, y_front, cutouts_z_pos])
    rotate([0, -90, 0]) // Rotate -90 deg so top faces Left (towards chassis)
    color("White") make_wheel();

// Rear Left
*translate([x_left_wheel, y_rear, cutouts_z_pos])
    rotate([0, 90, 0])
    color("White") make_wheel();

// Rear Right
*translate([x_right_wheel, y_rear, cutouts_z_pos])
    rotate([0, -90, 0])
    color("White") make_wheel();