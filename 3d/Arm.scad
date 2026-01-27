// --- Configuration ---
// Select part to render: "assembly", "mount", "arm1", "arm2", "servo_ref"
part = "assembly"; 

// --- Rotation for Animation/View ---
// Change these to see the arm move in the preview
joint1_angle = 45; 
joint2_angle = -45;

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
arm_len = 80;            // Center to center length
clearance = 0.4;         // 3D print tolerance
$fn = 50;                // Circle resolution

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
    // This brackets holds Servo 1 horizontally
    
    bracket_w = servo_tab_len + 10;
    bracket_d = servo_body_wid + wall*2;
    bracket_h = 20;
    
    difference() {
        // Main Block
        translate([0, 0, bracket_h/2])
            cube([bracket_w, bracket_d, bracket_h], center=true);
        
        // Remove Servo Shape
        translate([0, 0, -1]) // Shift down slightly
            servo_mount_cutout();
            
        // Add roof mounting screw holes at the edges
        translate([bracket_w/2 - 4, bracket_d/2 - 4, 0]) cylinder(d=3, h=50, center=true);
        translate([-bracket_w/2 + 4, bracket_d/2 - 4, 0]) cylinder(d=3, h=50, center=true);
        translate([bracket_w/2 - 4, -bracket_d/2 + 4, 0]) cylinder(d=3, h=50, center=true);
        translate([-bracket_w/2 + 4, -bracket_d/2 + 4, 0]) cylinder(d=3, h=50, center=true);
    }
}

module first_arm() {
    difference() {
        union() {
            // Proximal Hub (Connects to Servo 1)
            cylinder(d=20, h=wall);
            
            // The Arm Shaft
            translate([0, -10, 0])
                cube([arm_len, 20, wall]);
            
            // Distal Mount (Holds Servo 2)
            // We need a plate thick enough to hold the servo
            translate([arm_len, 0, 0])
                cube([servo_body_wid + wall*2, servo_tab_len + 8, wall], center=true);
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
    }
}

module second_arm() {
    difference() {
        union() {
            // Proximal Hub (Connects to Servo 2)
            cylinder(d=20, h=wall);
            
            // The Arm Shaft Tapered
            hull() {
                translate([0, -8, 0]) cube([10, 16, wall]);
                translate([arm_len, -2, 0]) cube([1, 4, wall]);
            }
        }
        
        // -- Cutout for Servo 2 Horn --
        translate([0, 0, wall]) 
            mirror([0,0,1])
            horn_attachment_cutout();
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
else if (part == "assembly") {
    
    // 1. The Roof Mount
    color("gray") roof_mount();
    
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
            color("orange") first_arm();
            
            // 4. Servo 2 (Mounted in First Arm)
            translate([arm_len, 0, -wall/2]) // Move to end of arm
                rotate([0, 0, 90]) // Orient correctly in the slot
                translate([0, 0, -10]) // Push into the slot
                SG90_Servo();
            
            // 5. Second Arm (Attached to Servo 2)
            // Servo 2 horn face calculation relative to Arm 1 end
            // Servo 2 is mounted, its shaft points +Z relative to Arm 1
             translate([arm_len, 0, -wall/2 + servo_gear_h + servo_horn_h + 2])
                rotate([0, 0, joint2_angle])
                color("yellow") second_arm();
        }
}