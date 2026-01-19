// Title: Robot Assembly (Recessed Wheels + Mounting Walls)
// Description: Wheels tucked into chassis. Mounting holes restored on inner well walls.
// Modified by: AI Assistant

/*
 * =====================================================================
 * 1. GLOBAL PARAMETERS
 * =====================================================================
 */

// --- Chassis Dimensions ---
chassis_length = 220;
chassis_width = 120;
chassis_height = 40;
wall_thickness = 3;

// --- Wheel Parameters ---
wheel_diameter = 60;
wheel_thickness = 20; // Thick wheels
wheel_clearance = 3;  // Gap between wheel and chassis walls
// The depth of the "pit" into the chassis side
well_depth = wheel_thickness + 2; 

// --- Servo/Axle Positions ---
servo_pos_from_front = 50; 
rear_hole_pos_from_back = 40;
cutouts_z_pos = 20;

// Calculated Axle Y positions
global_y_front_axle = chassis_length - servo_pos_from_front;
global_y_rear_axle = rear_hole_pos_from_back;

// --- Servo Dimensions ---
servo_cutout_width = 24;
servo_cutout_height = 12;
servo_hole_distance = 28;
servo_hole_diameter = 1.5;

// --- Rear Axle Holes ---
rear_hole_diameter = 6;

// --- Sensor Parameters ---
sensor_hole_dia = 16.5;      
sensor_spacing = 26;         
sensor_z_pos = chassis_height / 2;

// --- Wheel Detail ---
tread_grooves = 40;
mount_hole_distance = 32;

$fn = 40;

/*
 * =====================================================================
 * 2. MODULE: CHASSIS (With Recessed Mounting Walls)
 * =====================================================================
 */
module make_chassis() {
    
    // 1. The Solid Outer Block
    module solid_block() {
        cube([chassis_width, chassis_length, chassis_height]);
    }

    // 2. The Interior Hollow (Narrower to fit wheel wells)
    module internal_hollow() {
        // Calculate internal width based on the deep wheel wells
        // We need 3mm wall BEHIND the wheel well.
        inner_w = chassis_width - (2 * well_depth) - (2 * wall_thickness);
        inner_l = chassis_length - (2 * wall_thickness);
        
        translate([well_depth + wall_thickness, wall_thickness, wall_thickness])
            cube([inner_w, inner_l, chassis_height]); // Cuts through top
    }

    // 3. The Wheel Wells (The "Pits")
    module wheel_wells() {
        well_len = wheel_diameter + (wheel_clearance * 2);
        // We cut slightly deeper than well_depth to ensure clean face
        cut_depth = well_depth + 0.1; 
        
        // Front Left Pit
        translate([-0.1, global_y_front_axle - well_len/2, -1])
            cube([cut_depth, well_len, chassis_height + 2]);
            
        // Front Right Pit
        translate([chassis_width - well_depth + 0.1, global_y_front_axle - well_len/2, -1])
            cube([cut_depth, well_len, chassis_height + 2]);
            
        // Rear Left Pit
        translate([-0.1, global_y_rear_axle - well_len/2, -1])
            cube([cut_depth, well_len, chassis_height + 2]);
            
        // Rear Right Pit
        translate([chassis_width - well_depth + 0.1, global_y_rear_axle - well_len/2, -1])
            cube([cut_depth, well_len, chassis_height + 2]);
    }

    // 4. Mounting Holes (Servos & Axles)
    module mounting_holes() {
        // We mount on the vertical wall created by the well.
        // Left Wall X = well_depth
        // Right Wall X = chassis_width - well_depth
        
        // --- FRONT: SERVO PATTERNS ---
        
        // Left Servo
        translate([well_depth, global_y_front_axle, cutouts_z_pos]) {
            // Main rectangular cutout (centered)
            translate([-wall_thickness*2, -servo_cutout_width/2, -servo_cutout_height/2])
                cube([wall_thickness*4, servo_cutout_width, servo_cutout_height]);
            // Screw holes
            translate([0, -servo_hole_distance/2, 0]) rotate([0, 90, 0])
                cylinder(d=servo_hole_diameter, h=wall_thickness*6, center=true);
            translate([0, servo_hole_distance/2, 0]) rotate([0, 90, 0])
                cylinder(d=servo_hole_diameter, h=wall_thickness*6, center=true);
        }
        
        // Right Servo
        translate([chassis_width - well_depth, global_y_front_axle, cutouts_z_pos]) {
             // Main rectangular cutout
            translate([-wall_thickness*2, -servo_cutout_width/2, -servo_cutout_height/2])
                cube([wall_thickness*4, servo_cutout_width, servo_cutout_height]);
            // Screw holes
            translate([0, -servo_hole_distance/2, 0]) rotate([0, 90, 0])
                cylinder(d=servo_hole_diameter, h=wall_thickness*6, center=true);
            translate([0, servo_hole_distance/2, 0]) rotate([0, 90, 0])
                cylinder(d=servo_hole_diameter, h=wall_thickness*6, center=true);
        }

        // --- REAR: AXLE HOLES ---
        
        // Left Axle
        translate([well_depth, global_y_rear_axle, cutouts_z_pos])
            rotate([0, 90, 0])
            cylinder(d=rear_hole_diameter, h=wall_thickness*6, center=true);

        // Right Axle
        translate([chassis_width - well_depth, global_y_rear_axle, cutouts_z_pos])
            rotate([0, 90, 0])
            cylinder(d=rear_hole_diameter, h=wall_thickness*6, center=true);
    }
    
    // 5. Sonar Holes (Front)
    module sonar_holes() {
        translate([chassis_width/2 + sensor_spacing/2, chassis_length, sensor_z_pos])
            rotate([90, 0, 0]) 
            cylinder(d=sensor_hole_dia, h=wall_thickness*4, center=true);
        
        translate([chassis_width/2 - sensor_spacing/2, chassis_length, sensor_z_pos])
            rotate([90, 0, 0]) 
            cylinder(d=sensor_hole_dia, h=wall_thickness*4, center=true);
    }
    
    // 6. Posts
     module mounting_posts() {
        post_size=10; post_h=5;
        translate([0, 0, chassis_height]) cube([post_size, post_size, post_h]);
        translate([chassis_width-post_size, 0, chassis_height]) cube([post_size, post_size, post_h]);
        translate([0, chassis_length-post_size, chassis_height]) cube([post_size, post_size, post_h]);
        translate([chassis_width-post_size, chassis_length-post_size, chassis_height]) cube([post_size, post_size, post_h]);
    }

    difference() {
        union() {
            solid_block();
            mounting_posts();
        }
        internal_hollow();
        wheel_wells();
        mounting_holes();
        sonar_holes();
    }
}

/*
 * =====================================================================
 * 3. MODULE: WHEEL (Unchanged logic, updated params)
 * =====================================================================
 */
module make_wheel() {
    difference() {
        // Base
        cylinder(d = wheel_diameter, h = wheel_thickness);
        
        // Treads
        for (i = [0 : 360/tread_grooves : 359]) {
            rotate([0, 0, i])
            translate([wheel_diameter/2 - 1.5, -2, -1])
            cube([2.5, 4, wheel_thickness + 2]);
        }
        
        // Servo Horn Recess
        translate([0, 0, wheel_thickness - 2.5]) {
            hull() {
                cylinder(d = 7, h = 4);
                translate([mount_hole_distance / 2, 0, 0]) cylinder(d = 6, h = 4);
                translate([-mount_hole_distance / 2, 0, 0]) cylinder(d = 6, h = 4);
            }
        }
        
        // Holes
        translate([0,0,wheel_thickness/2]) {
             cylinder(d = 6, h = wheel_thickness+2, center=true); // Spline
             translate([mount_hole_distance/2,0,0]) cylinder(d = 1.5, h = wheel_thickness+2, center=true);
             translate([-mount_hole_distance/2,0,0]) cylinder(d = 1.5, h = wheel_thickness+2, center=true);
        }
    }
}

/*
 * =====================================================================
 * 4. MODULE: CABIN (With Arches matching Chassis Wells)
 * =====================================================================
 */
module cabin() {
    // Cabin dims
    c_len = 220; c_wid = 120; c_ht = 40; taper = 70;
    
    // Axle positions relative to Cabin center
    // Note: Cabin Local X = Global Y of chassis
    center_y_global = chassis_length / 2;
    pos_front_x = global_y_front_axle - center_y_global; 
    pos_rear_x = global_y_rear_axle - center_y_global;   

    module body() {
        top_red = c_ht / tan(taper);
        hull() {
            translate([0,0,0]) cube([c_len, c_wid, 0.1], center=true);
            translate([0,0,c_ht]) cube([c_len-2*top_red, c_wid-2*top_red, 0.1], center=true);
        }
    }
    
    module cavity() {
         top_red = c_ht / tan(taper);
         wt = 3;
         hull() {
            translate([0,0,-1]) cube([c_len-2*wt, c_wid-2*wt, 0.1], center=true);
            translate([0,0,c_ht-wt]) cube([c_len-2*top_red-2*wt, c_wid-2*top_red-2*wt, 0.1], center=true);
        }
    }

    module wheel_arches() {
        // Cut arches to match the chassis wells
        cut_depth = well_depth; 
        cut_len = wheel_diameter + (wheel_clearance * 2);
        cut_h = 25; 
        
        // Front
        translate([pos_front_x, c_wid/2, 0]) cube([cut_len, cut_depth*2, cut_h], center=true);
        translate([pos_front_x, -c_wid/2, 0]) cube([cut_len, cut_depth*2, cut_h], center=true);
        // Rear
        translate([pos_rear_x, c_wid/2, 0]) cube([cut_len, cut_depth*2, cut_h], center=true);
        translate([pos_rear_x, -c_wid/2, 0]) cube([cut_len, cut_depth*2, cut_h], center=true);
    }

    // Battery shelf, roof holes etc omitted for brevity, keeping main shape
    // Re-adding shelf for completeness
    module shelf() {
        sh_z = c_ht - 3 - 1.5 - 15;
        red = sh_z / tan(taper);
        translate([-25, 0, sh_z]) cube([c_len-2*red-6-50, c_wid-2*red-6, 3], center=true);
    }
    
    module misc_holes() {
        // Rear cutout
        translate([-c_len/2, 0, c_ht-18-7.5]) cube([60, 80, 15], center=true);
        // Roof
        translate([c_len/2 - 30, 0, c_ht]) cylinder(d=13.5, h=20, center=true);
    }

    difference() {
        union() { body(); shelf(); }
        cavity();
        translate([0,0,-10]) cube([c_len+20, c_wid+20, 20], center=true); // Cut bottom
        wheel_arches();
        misc_holes();
    }
}

/* =====================================================================
 *                    MAIN ASSEMBLY
 * =====================================================================
 */

// 1. Render Chassis
color("yellow") make_chassis();

// 2. Render Cabin (Rotated and placed on top)
color("orange") 
    translate([chassis_width/2, chassis_length/2, chassis_height])
    rotate([0,0,90])
    cabin();

// 3. Render Wheels
// Positioned inside the wells, with the outer face flush with chassis wall
x_left = wheel_thickness/2-10; // Center of wheel
x_right = chassis_width - wheel_thickness/2 +10; // Center of wheel

// Front Left
translate([x_left, global_y_front_axle, cutouts_z_pos])
    rotate([0, 90, 0]) color("DimGray") make_wheel();

// Front Right
translate([x_right, global_y_front_axle, cutouts_z_pos])
    rotate([0, -90, 0]) color("DimGray") make_wheel();

// Rear Left
translate([x_left, global_y_rear_axle, cutouts_z_pos])
    rotate([0, 90, 0]) color("DimGray") make_wheel();

// Rear Right
translate([x_right, global_y_rear_axle, cutouts_z_pos])
    rotate([0, -90, 0]) color("DimGray") make_wheel();