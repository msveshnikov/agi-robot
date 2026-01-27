// --- Configuration ---
// Select which part to view/render: 
// "assembly", "mount", "arm1", "arm2"
show_part = "assembly"; 

// --- User Parameters ---
servo_cutout_width = 24;       // Length of servo body
servo_cutout_height = 12;      // Width/Thickness of servo body
servo_hole_distance = 28;      // Distance between mounting screw centers
servo_hole_diameter = 2;       // Screw hole size for mounting servo
servo_horn_recess_depth = 2.5;
servo_spline_hole_diameter = 6; 
servo_horn_hub_diameter = 7.5; // Slightly larger for clearance
servo_horn_arm_width = 6; 

// --- Additional Design Parameters ---
arm_length = 80;               // Length from joint to joint
wall_thickness = 4;            // Thickness of the plastic parts
mount_hole_distance = 15;      // Distance of screw holes on the plastic horn
mount_hole_diameter = 2;       // Screw size for the horn
tolerance = 0.3;               // 3D printing clearance
$fn = 60;                      // Resolution for circles

// ---------------------------------------------------------
// --- Modules (Reusable Logic) ---
// ---------------------------------------------------------

// Creates the negative space to remove material where the Servo Body goes
module servo_body_cutout() {
    // Main Body
    translate([0, 0, -10])
        cube([servo_cutout_width + tolerance, servo_cutout_height + tolerance, 20], center=true);
    
    // Mounting Screw Holes (Left)
    translate([servo_hole_distance/2, 0, 0])
        cylinder(d=servo_hole_diameter, h=50, center=true);
        
    // Mounting Screw Holes (Right)
    translate([-servo_hole_distance/2, 0, 0])
        cylinder(d=servo_hole_diameter, h=50, center=true);
}

// Creates the negative space for the Horn (Spline + Screw holes + Recess)
module servo_horn_interface() {
    cutter_h = servo_horn_recess_depth + 1;
    
    // 1. Recess for the plastic horn arm (Pocket)
    translate([0, 0, -0.01]) { // Slight offset to ensure surface cut
        hull() {
            cylinder(d = servo_horn_hub_diameter, h = servo_horn_recess_depth);
            translate([mount_hole_distance / 2, 0, 0])
                cylinder(d = servo_horn_arm_width, h = servo_horn_recess_depth);
            translate([-mount_hole_distance / 2, 0, 0])
                cylinder(d = servo_horn_arm_width, h = servo_horn_recess_depth);
        }
    }

    // 2. Through holes for the screws
    hole_h = wall_thickness * 3;
    translate([0, 0, -wall_thickness]) {
        // Center Spline access
        cylinder(d = servo_spline_hole_diameter, h = hole_h, center = true);
        
        // Horn attachment screws
        translate([mount_hole_distance / 2, 0, 0])
            cylinder(d = mount_hole_diameter, h = hole_h, center = true);
        translate([-mount_hole_distance / 2, 0, 0])
            cylinder(d = mount_hole_diameter, h = hole_h, center = true);
    }
}

// ---------------------------------------------------------
// --- Parts ---
// ---------------------------------------------------------

module roof_mount() {
    base_w = servo_hole_distance + 12;
    base_h = servo_cutout_height + 10;
    
    difference() {
        union() {
            // Flat ceiling plate
            translate([-base_w/2, -base_h/2, 0])
                cube([base_w, base_h, wall_thickness]);
            
            // Vertical Block to hold servo
            translate([-base_w/2, -base_h/2, 0])
                cube([base_w, wall_thickness, servo_cutout_width + 10]);
        }
        
        // Remove Servo Body Shape
        // Rotate to place servo horizontal
        translate([0, 0, (servo_cutout_width/2) + wall_thickness + 2])
            rotate([90, 0, 0])
            rotate([0, 0, 90])
            servo_body_cutout();
            
        // Screw holes for roof mounting
        translate([base_w/2 - 5, 0, 0]) cylinder(d=4, h=20, center=true);
        translate([-base_w/2 + 5, 0, 0]) cylinder(d=4, h=20, center=true);
    }
}

module first_arm() {
    difference() {
        union() {
            hull() {
                // Joint 1 (Connection to Base)
                cylinder(d=20, h=wall_thickness);
                
                // Joint 2 (Holder for Servo 2)
                translate([arm_length, 0, 0])
                    cube([servo_hole_distance + 10, servo_cutout_height + 8, wall_thickness], center=true);
            }
        }
        
        // Cutout for connection to Servo 1 Horn
        // We flip it so the recess is on the bottom side facing the servo
        rotate([0, 180, 0])
            translate([0, 0, -wall_thickness])
            servo_horn_interface();
            
        // Cutout to hold Servo 2 Body
        translate([arm_length, 0, 0])
            servo_body_cutout();
    }
}

module second_arm() {
    difference() {
        hull() {
            // Connection to Servo 2
            cylinder(d=20, h=wall_thickness);
            
            // The Tip
            translate([arm_length, 0, 0])
                cylinder(d=5, h=wall_thickness);
        }
        
        // Cutout for connection to Servo 2 Horn
        rotate([0, 180, 0])
            translate([0, 0, -wall_thickness])
            servo_horn_interface();
    }
}

// ---------------------------------------------------------
// --- Rendering Logic ---
// ---------------------------------------------------------

if (show_part == "mount") {
    roof_mount();
} else if (show_part == "arm1") {
    first_arm();
} else if (show_part == "arm2") {
    second_arm();
} else if (show_part == "assembly") {
    
    // 1. Roof Mount
    color("gray") roof_mount();
    
    // Simulate Servo 1 placement (Invisible/Ghost logic)
    servo_z_center = (servo_cutout_width/2) + wall_thickness + 2;
    
    // 2. First Arm (Attached to Servo 1)
    // Rotated 90 degrees to be vertical, attached to the side of the mount
    translate([0, -12, servo_z_center]) 
        rotate([90, 0, 0]) // Orient vertical
        rotate([0, -45, 0]) // Simulate 45 degree angle
        {
            color("orange") first_arm();
            
            // 3. Second Arm (Attached to Servo 2 on First Arm)
            translate([arm_length, 0, 0]) // Move to end of arm 1
            translate([0, 0, -15]) // Offset for Servo 2 thickness
            rotate([0, 0, 180]) // Flip orientation if needed for servo face
            rotate([0, -45, 0]) // Simulate joint movement
            color("skyblue") second_arm();
        }
}