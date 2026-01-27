// --- CABIN DIMENSIONS / РАЗМЕРЫ КАБИНЫ ---
cabin_length = 220;          // [mm] Length (front to back)
cabin_width = 120;           // [mm] Width (side to side)
cabin_height = 40;           // [mm] Height
wall_thickness = 3;          // [mm] Wall thickness
taper_angle = 70;            // [degrees] Taper angle

// --- MOUNTING SOCKETS ---
socket_size = 10;            
socket_depth = 5;            

// --- BATTERY SHELF ---
shelf_thickness = 3;         
shelf_distance_from_roof = 3; 
shelf_drop_offset = 15;      
battery_cable_dia = 15;      
rear_cutout_width = 80;      
rear_cutout_height = 15;     

// --- SENSORS & CAMERAS ---
sensor_hole_dia = 16.5;      
sensor_spacing = 26;         
sensor_height = 40;          
camera_hole_dia = 13.5;      
camera_cable_dia = 18;       
camera_position = 30;        
cable_offset = 20;           

// --- DECORATION SETTINGS ---
text_depth = 1.0;            // [mm] Emboss depth
font_style = "Liberation Sans:style=Bold"; // Font supporting basic symbols

// --- QUALITY ---
$fn = 60;                    

/* =====================================================================
 *                         MODULES
 * =====================================================================
 */

// Logic to align objects to the tapered walls
module place_on_surface(h, side) {
    offset_at_h = h / tan(taper_angle);
    rot_angle = taper_angle; 

    if (side == "roof") {
        translate([0, 0, cabin_height])
        children();
    }
    else if (side == "right") {
        y_pos = (cabin_width / 2) - offset_at_h;
        translate([0, y_pos, h])
        rotate([-rot_angle, 0, 0]) 
        children();
    }
    else if (side == "left") {
        y_pos = -(cabin_width / 2) + offset_at_h;
        translate([0, y_pos, h])
        rotate([rot_angle, 0, 0]) 
        rotate([0, 0, 180])       
        children();
    }
    else if (side == "front") {
        x_pos = (cabin_length / 2) - offset_at_h;
        translate([x_pos, 0, h])
        rotate([0, rot_angle, 0]) 
        rotate([0, 0, 90])        
        children();
    }
    else if (side == "back") {
        x_pos = -(cabin_length / 2) + offset_at_h;
        translate([x_pos, 0, h])
        rotate([0, -rot_angle, 0]) 
        rotate([0, 0, -90])        
        children();
    }
}

module emboss_text(t_string, t_size) {
    color("Gold")
    linear_extrude(height = text_depth, convexity = 4)
        text(t_string, size = t_size, font = font_style, valign = "center", halign = "center");
}

module name_dropping() {
    // Existing Text
    place_on_surface(cabin_height, "roof") translate([20, -30, 0]) emboss_text("Robot", 12);
    place_on_surface(20, "left") translate([0, 0, 0]) emboss_text("Commerzbank", 10);
    place_on_surface(25, "right") translate([30, 0, 0]) emboss_text("MaxSoft", 11);
    place_on_surface(30, "front") translate([0, 0, 0]) emboss_text("AGI", 10);
    place_on_surface(20, "back") translate([-40, 0, 0]) emboss_text("Julia", 8);
    place_on_surface(cabin_height, "roof") translate([-60, 0, 0]) emboss_text("Veronica", 9);
    place_on_surface(15, "right") translate([-50, 0, 0]) emboss_text("DARiA", 14);
}

module scattered_smiles() {
    // Using Unicode symbols: \u263A (☺), \u263B (☻), and text representation :)
    
    // --- RIGHT SIDE ---
    place_on_surface(10, "right") translate([70, 0, 0]) emboss_text("\u263A", 15); // ☺
    place_on_surface(30, "right") translate([-10, 0, 0]) emboss_text(":)", 10);
    place_on_surface(12, "right") translate([0, 0, 0]) emboss_text("\u263B", 12); // ☻
    
    // --- LEFT SIDE ---
    place_on_surface(30, "left") translate([50, 0, 0]) emboss_text(":-)", 10);
    place_on_surface(10, "left") translate([-60, 0, 0]) emboss_text("\u263A", 12); // ☺
    place_on_surface(35, "left") translate([-20, 0, 0]) emboss_text(";)", 10);

    // --- FRONT ---
    place_on_surface(10, "front") translate([30, 0, 0]) emboss_text("\u263A", 12); // ☺
    place_on_surface(15, "front") translate([-30, 0, 0]) emboss_text("(:", 10);
    
    // --- BACK ---
    place_on_surface(30, "back") translate([20, 0, 0]) emboss_text("\u263B", 10); // ☻
    place_on_surface(10, "back") translate([35, 0, 0]) emboss_text(":D", 9);
    place_on_surface(35, "back") translate([-20, 0, 0]) emboss_text("\u263A", 10); // ☺

    // --- ROOF ---
    place_on_surface(cabin_height, "roof") 
        translate([40, 25, 0]) rotate([0,0,30]) emboss_text("\u263A", 18); // Large ☺
        
    place_on_surface(cabin_height, "roof") 
        translate([-20, 35, 0]) rotate([0,0,-15]) emboss_text(":)", 12);
        
    place_on_surface(cabin_height, "roof") 
        translate([-80, -20, 0]) rotate([0,0,180]) emboss_text("\u263B", 14); // ☻
}

// Main cabin body
module cabin_body() {
    top_reduction = cabin_height / tan(taper_angle);
    top_length = cabin_length - 2 * top_reduction;
    top_width = cabin_width - 2 * top_reduction;
    
    hull() {
        translate([0, 0, 0]) cube([cabin_length, cabin_width, 0.1], center = true);
        translate([0, 0, cabin_height]) cube([top_length, top_width, 0.1], center = true);
    }
}

// Inner cavity
module cabin_cavity() {
    top_reduction = cabin_height / tan(taper_angle);
    top_length = cabin_length - 2 * top_reduction - 2 * wall_thickness;
    top_width = cabin_width - 2 * top_reduction - 2 * wall_thickness;
    inner_length = cabin_length - 2 * wall_thickness;
    inner_width = cabin_width - 2 * wall_thickness;
    
    difference (){
        hull() {
            translate([0, 0, -1]) cube([inner_length, inner_width, 0.1], center = true);
            translate([0, 0, cabin_height - wall_thickness]) cube([top_length, top_width, 0.1], center = true);
        }
        battery_shelf();
    }
}

// Mounting socket
module mounting_socket() {
    translate([0, 0, socket_depth/2]) cube([socket_size, socket_size, socket_depth + 0.2], center = true);
}

// Battery Shelf
module battery_shelf() {
    actual_z_center = cabin_height - shelf_distance_from_roof - shelf_thickness/2 - shelf_drop_offset;
    reduction = actual_z_center / tan(taper_angle);
    shelf_length = cabin_length - 2 * reduction - 2 * wall_thickness-50;
    shelf_width = cabin_width - 2 * reduction - 2 * wall_thickness;
    
    translate([-25, 0, actual_z_center]) cube([shelf_length, shelf_width, shelf_thickness], center = true);
}

// Rear cutout
module rear_battery_cutout() {
    shelf_top_z = cabin_height - shelf_distance_from_roof - shelf_drop_offset;
    cutout_z = shelf_top_z + rear_cutout_height/2;
    translate([-cabin_length/2, 0, cutout_z]) cube([60, rear_cutout_width, rear_cutout_height], center = true);
}

// Sensors
module sensor_holes() {
    extra_length = 30;
    translate([ 100, 0, -cabin_height/2 + sensor_height]) {
        translate([0, -sensor_spacing/2, 0]) rotate([0, 90, 0]) cylinder(h = wall_thickness + extra_length, d = sensor_hole_dia, center = true);
        translate([0, sensor_spacing/2, 0]) rotate([0, 90, 0]) cylinder(h = wall_thickness + extra_length, d = sensor_hole_dia, center = true);
    }
}

// Roof holes
module roof_holes() {
    translate([0, 0, cabin_height]) {
        translate([cabin_length/2 - camera_position, 0, 0]) cylinder(h = wall_thickness + 10, d = camera_hole_dia, center = true);
        translate([cabin_length/2 - camera_position - cable_offset, 0, 0]) cylinder(h = wall_thickness + 10, d = camera_cable_dia, center = true);
    }
}

/* =====================================================================
 *                    MAIN ASSEMBLY
 * =====================================================================
 */

difference() {
    union() {
        cabin_body();
        battery_shelf();
        name_dropping();    // Embossed Text
        scattered_smiles(); // Embossed Symbolic Smiles
    }
    
    cabin_cavity();
    
    // Remove bottom
    translate([0, 0, -10]) cube([cabin_length + 10, cabin_width + 10, 20], center = true);
    
    // Sockets
    translate([cabin_length/2 - socket_size/2, cabin_width/2 - socket_size/2, 0]) mounting_socket();
    translate([cabin_length/2 - socket_size/2, -cabin_width/2 + socket_size/2, 0]) mounting_socket();
    translate([-cabin_length/2 + socket_size/2, cabin_width/2 - socket_size/2, 0]) mounting_socket();
    translate([-cabin_length/2 + socket_size/2, -cabin_width/2 + socket_size/2, 0]) mounting_socket();
    
    sensor_holes();
    roof_holes();
    rear_battery_cutout();
}