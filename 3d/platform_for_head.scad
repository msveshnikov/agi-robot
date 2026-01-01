// Title: Robot Assembly (Chassis + 4 Wheels + 1cm Platform)
// Description: Parametric chassis with 4 wheels and a thick top platform that fits over the posts.
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

// --- Servo Cutouts ---
servo_cutout_width = 24;
servo_cutout_height = 12;
servo_hole_distance = 28;
servo_hole_diameter = 1.5;
servo_pos_from_front = 50; 

// --- Rear Axle Holes ---
rear_hole_diameter = 6;
rear_hole_pos_from_back = 40;

// --- Vertical Positioning ---
cutouts_z_pos = 20; 

// --- Chassis Posts ---
post_size = 10;
post_height = 5;

// --- Platform Parameters (NEW) ---
platform_height = 10;      // Total height 1cm
platform_hole_width = 90;  // 7 cm window
platform_hole_length = 160; // 9 cm window
platform_screw_hole_d = 3; // Screw size
fit_tolerance = 0.4;       // Extra gap to ensure platform fits over posts

// --- Wheel Parameters ---
wheel_diameter = 60;
wheel_thickness = 5;
wheel_offset = 2; 

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
 * 4. MODULE: 1cm PLATFORM (UPDATED)
 * =====================================================================
 */
module make_platform() {
    difference() {
        // 1. The main block (10mm high)
        cube([chassis_width, chassis_length, platform_height]);
        
        // 2. The Big Window (7x9 cm), Centered
        translate([chassis_width/2, chassis_length/2, -1])
            cube([platform_hole_width, platform_hole_length, platform_height + 25], center=true);
            
        // 3. Corner Pockets (Underside)
        // These cutouts allow the chassis posts to slide *inside* the platform
        // We add a small tolerance so it fits easily.
        pocket_s = post_size + fit_tolerance;
        pocket_h = post_height + 0.2; // slightly deeper to ensure flush fit
        
        // Front Left Pocket
        translate([-fit_tolerance/2, -fit_tolerance/2, -0.1])
            cube([pocket_s, pocket_s, pocket_h]);
            
        // Front Right Pocket
        translate([chassis_width - post_size - fit_tolerance/2, -fit_tolerance/2, -0.1])
            cube([pocket_s, pocket_s, pocket_h]);
            
        // Rear Left Pocket
        translate([-fit_tolerance/2, chassis_length - post_size - fit_tolerance/2, -0.1])
            cube([pocket_s, pocket_s, pocket_h]);
            
        // Rear Right Pocket
        translate([chassis_width - post_size - fit_tolerance/2, chassis_length - post_size - fit_tolerance/2, -0.1])
            cube([pocket_s, pocket_s, pocket_h]);

        // 4. Screw holes (Through the corners)
        hole_z_height = platform_height + 2;
        center_offset = post_size / 2;

        translate([center_offset, center_offset, platform_height/2])
            cylinder(d=platform_screw_hole_d, h=hole_z_height, center=true);
            
        translate([chassis_width - center_offset, center_offset, platform_height/2])
            cylinder(d=platform_screw_hole_d, h=hole_z_height, center=true);
            
        translate([center_offset, chassis_length - center_offset, platform_height/2])
            cylinder(d=platform_screw_hole_d, h=hole_z_height, center=true);
            
        translate([chassis_width - center_offset, chassis_length - center_offset, platform_height/2])
            cylinder(d=platform_screw_hole_d, h=hole_z_height, center=true);
    }
}

/*
 * =====================================================================
 * 5. ASSEMBLY
 * =====================================================================
 */

// 1. Render the Chassis
color("yellow") 
    make_chassis();

// 2. Render the Platform
// Placed at Chassis Height (40mm). 
// The pockets on the bottom of the platform will "swallow" the posts (which stick up to 45mm).
color("Cyan")
    translate([0, 0, chassis_height]) 
    make_platform();


// --- Wheels Visuals ---

// Calculated Y coordinates for wheels
y_front = chassis_length - servo_pos_from_front;
y_rear = rear_hole_pos_from_back;

// Calculated X coordinates for wheels (2mm gap)
x_left_wheel = 0 - wheel_offset - wheel_thickness; 
x_right_wheel = chassis_width + wheel_offset + wheel_thickness; 

// Front Left
*translate([x_left_wheel, y_front, cutouts_z_pos])
    rotate([0, 90, 0]) 
    color("White") make_wheel();

// Front Right
*translate([x_right_wheel, y_front, cutouts_z_pos])
    rotate([0, -90, 0]) 
    color("White") make_wheel();

// Rear Left
*translate([x_left_wheel, y_rear, cutouts_z_pos])
    rotate([0, 90, 0])
    color("White") make_wheel();

// Rear Right
*translate([x_right_wheel, y_rear, cutouts_z_pos])
    rotate([0, -90, 0])
    color("White") make_wheel();