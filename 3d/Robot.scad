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
rotate([0,0,-360*$t])
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
color("white") make_chassis();

// 2. Render Cabin (Rotated and placed on top)
color("orange") 
    translate([chassis_width/2, chassis_length/2, chassis_height])
    rotate([0,0,90])
    cabin();

// 3. Render Wheels
// Positioned inside the wells, with the outer face flush with chassis wall
x_left = wheel_thickness/2-10; // Center of wheel
x_right = chassis_width - wheel_thickness/2+10; // Center of wheel

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
    
    
    
    
    // --- Configuration ---
// Select part to render: "assembly", "mount", "arm1", "arm2", "servo_ref"
part = "assembly"; 

// --- Rotation for Animation/View ---
// Change these to see the arm move in the preview
joint1_angle = 180*$t; 
joint2_angle = 90*$t;

// --- Dimensions (SG90 Standard) ---
servo_body_len = 23;
servo_body_wid = 12.5;
servo_body_h = 22.5; // Height excluding gear
servo_hole_dist = 28;
servo_tab_len = 32;
servo_gear_h = 4;    // How high gear sticks out
servo_horn_h = 2;    // Thickness of plastic horn
horn_arm_len = 15;   // Length of horn arm (center to hole)

// --- Design Parameters ---
wall = 4;                // Thickness of plastic parts
arm_len = 150;            // Center to center length
clearance = 0.4;         // 3D print tolerance
cable_channel_w = 6;     // Cable channel width
cable_channel_h = 3;     // Cable channel depth
//$fn = 80;                // Circle resolution

// =========================================================
// --- Helper Modules (Drills and Shapes) ---
// =========================================================

module SG90_Servo() {
    color("#0055aa") {
        // Body
        translate([-servo_body_len/2, -servo_body_wid/2, -servo_body_h])
            cube([servo_body_len, servo_body_wid, servo_body_h]);
        // Tabs
        translate([-servo_tab_len/2, -servo_body_wid/2, -17])
            cube([servo_tab_len, servo_body_wid, 2.5]);
        // Geartrain bump
        translate([-6, -servo_body_wid/2, 0])
            cube([12, servo_body_wid, servo_gear_h]);
        // Output Shaft
        translate([0, 0, 0]) cylinder(d=5, h=servo_gear_h);
    }
    // The Horn (White plastic part)
    color("white")
    translate([0, 0, servo_gear_h + 1]) {
        hull() {
            cylinder(d=7, h=servo_horn_h, center=true);
            translate([horn_arm_len, 0, 0]) cylinder(d=4, h=servo_horn_h, center=true);
            translate([-5, 0, 0]) cylinder(d=4, h=servo_horn_h, center=true);
        }
    }
}

module servo_mount_cutout() {
    // The main rectangular hole for the servo body
    cube([servo_body_len + clearance, servo_body_wid + clearance, 50], center=true);
    
    // The screw holes for the tabs
    translate([servo_hole_dist/2, 0, 0])
        cylinder(d=2, h=50, center=true);
    translate([-servo_hole_dist/2, 0, 0])
        cylinder(d=2, h=50, center=true);
}

module horn_attachment_cutout() {
    // 1. Recess for the horn (Non-through pocket)
    // The horn is roughly 7mm hub, arms stick out
    translate([0, 0, -0.1]) {
        hull() {
            cylinder(d=7.5, h=2.5); // Hub
            translate([horn_arm_len, 0, 0]) cylinder(d=6, h=2.5); // Arm tip
            translate([-5, 0, 0]) cylinder(d=6, h=2.5); // Back tip
        }
    }
    
    // 2. Screw holes (Through holes)
    // Center screw (connects horn to servo metal shaft)
    translate([0,0,-10]) cylinder(d=3, h=20);
    
    // Horn arm screws (connect plastic arm to plastic horn)
    // Assuming standard horns have holes ~14mm apart (7mm radius) or close to end
    translate([horn_arm_len - 2, 0, -10]) cylinder(d=2, h=20);
    translate([-3, 0, -10]) cylinder(d=2, h=20);
}

// =========================================================
// --- Main Parts ---
// =========================================================

module roof_mount() {
    // This bracket holds Servo 1 horizontally
    
    bracket_w = servo_tab_len + 10;
    bracket_d = servo_body_wid + wall*2;
    bracket_h = 20;
    
    difference() {
        // Main Block with rounded corners
        translate([0, 0, bracket_h/2])
            hull() {
                for(x = [-1, 1]) for(y = [-1, 1])
                    translate([x * (bracket_w/2 - 3), y * (bracket_d/2 - 3), 0])
                        cylinder(d=6, h=bracket_h, center=true);
            }
        
        // Remove Servo Shape
        translate([0, 0, -1]) // Shift down slightly
            servo_mount_cutout();
            
        // Add roof mounting screw holes at the edges (countersunk)
        for(x = [-1, 1]) for(y = [-1, 1]) {
            translate([x * (bracket_w/2 - 4), y * (bracket_d/2 - 4), 0]) {
                cylinder(d=3, h=50, center=true);
                translate([0, 0, bracket_h - 3]) cylinder(d1=3, d2=6, h=2);
            }
        }
    }
}

module first_arm() {
    difference() {
        union() {
            // Proximal Hub (Connects to Servo 1) - Made larger and stronger
            cylinder(d=24, h=wall);
            
            // The Arm Shaft - Improved design with rounded edges
            hull() {
                translate([0, -12, 0])
                    cube([10, 24, wall]);
                translate([arm_len - 15, -12, 0])
                    cube([15, 24, wall]);
            }
            
            // Distal Mount (Holds Servo 2) - Stronger mounting plate
            translate([arm_len, 0, 0]) {
                hull() {
                    cube([servo_body_wid + wall*2 + 2, servo_tab_len + 10, wall], center=true);
                    translate([-5, 0, wall])
                        cube([servo_body_wid + wall*2, servo_tab_len + 8, 1], center=true);
                }
            }
            
            // Cable channel walls (raised edges)
            translate([15, -8.5, 0])
                cube([arm_len - 30, 1, wall + 1]);
            translate([15, 7.5, 0])
                cube([arm_len - 30, 1, wall + 1]);
        }
        
        // -- Cutout for Servo 1 Horn (Proximal) --
        // Flip so recess is on bottom
        translate([0, 0, wall]) 
            mirror([0,0,1])
            horn_attachment_cutout();
            
        // -- Cutout for Servo 2 Body (Distal) --
        // Rotate 90 deg so servo sits perpendicular to arm
        translate([arm_len, 0, 0])
            rotate([0, 0, 90]) 
            servo_mount_cutout();
            
        // -- Cable routing channel --
        // Channel runs along the length of the arm
        translate([15, -cable_channel_w/2, -0.1])
            cube([arm_len - 30, cable_channel_w, cable_channel_h]);
        
        // Cable exit hole near servo 2
        translate([arm_len - 10, 0, -0.1])
            cylinder(d=5, h=wall + 2);
            
        // Cable entry hole near servo 1
        *translate([12, 0, -0.1])
            cylinder(d=5, h=wall + 2);
            
        // Lightening holes for aesthetics and weight reduction
        for(i = [0:47]) {
            translate([25 + i*20, 0, -0.1])
                cylinder(d=8, h=wall + 0.2);
        }
    }
}

module second_arm() {
    difference() {
        union() {
            // Proximal Hub (Connects to Servo 2) - Larger and stronger
            cylinder(d=24, h=wall);
            
            // The Arm Shaft - More elegant tapered design
            hull() {
                translate([0, -10, 0]) 
                    cube([15, 20, wall]);
                translate([arm_len - 5, -6, 0]) 
                    cube([5, 12, wall]);
            }
            
            // M10 mounting boss at the end
            translate([arm_len, 0, 0])
                cylinder(d=20, h=wall + 4);
        }
        
        // -- Cutout for Servo 2 Horn --
        translate([0, 0, wall]) 
            mirror([0,0,1])
            horn_attachment_cutout();
            
        // -- M10 mounting hole (10mm diameter, 10mm deep) --
        translate([arm_len, 0, wall]) {
            // Main hole - 10mm diameter
            cylinder(d=10, h=10.5);
            // Chamfer for easier bolt insertion
            translate([0, 0, -0.1])
                cylinder(d1=12, d2=10, h=1.1);
        }
        
        // Lightening holes
        for(i = [0:4]) {
            translate([20 + i*18, 0, -0.1])
                cylinder(d=6, h=wall + 0.2);
        }
    }
}

// =========================================================
// --- Assembly Logic ---
// =========================================================

if (part == "mount") {
    roof_mount();
} 
else if (part == "arm1") {
    first_arm();
} 
else if (part == "arm2") {
    second_arm();
} 
else if (part == "servo_ref") {
    SG90_Servo();
}
else if (part == "assembly") 
{
translate([20,200,90]) 
rotate([90,0,90])
{
    
    // 1. The Roof Mount
    color("gray", 0.8) roof_mount();
    
    // 2. Servo 1 (Fixed in Mount)
    translate([0, 0, -1]) // Adjust for recess depth
        rotate([180, 0, 0]) // Flip upside down to put shaft at bottom
        SG90_Servo();
        
    // Calculate Position of Joint 1 (The Horn of Servo 1)
    // Servo 1 is at 0,0. Shaft sticks out down (negative Z).
    // The horn face is roughly at Z = - (servo_gear_h + servo_horn_h) ~ -6mm
    
    horn_face_z = - (servo_gear_h + servo_horn_h + 1);
    
    // 3. First Arm
    translate([0, 0, horn_face_z]) 
        rotate([0, 0, joint1_angle]) // Rotate Arm 1
        {
            color("orange", 0.9) first_arm();
            
            // 4. Servo 2 (Mounted in First Arm)
            translate([arm_len, 0, -wall/2]) // Move to end of arm
                rotate([0, 0, 90]) // Orient correctly in the slot
                translate([0, 0, 15]) // Push into the slot
                SG90_Servo();
            
            // 5. Second Arm (Attached to Servo 2)
            // Servo 2 horn face calculation relative to Arm 1 end
            // Servo 2 is mounted, its shaft points +Z relative to Arm 1
             translate([arm_len, 0, -wall/2 + servo_gear_h + servo_horn_h + 17])
                rotate([180, 0, joint2_angle])
                color("yellow", 0.9) second_arm();
        }
}}
