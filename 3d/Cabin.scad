// --- CABIN DIMENSIONS / РАЗМЕРЫ КАБИНЫ ---
cabin_length = 220;          // [mm] Length (front to back) / Длина
cabin_width = 120;           // [mm] Width (side to side) / Ширина
cabin_height = 40;           // [mm] Height / Высота
wall_thickness = 3;          // [mm] Wall thickness / Толщина стенок
taper_angle = 70;            // [degrees] Taper angle (angle from ground) / Угол от земли

// --- MOUNTING SOCKETS / МОНТАЖНЫЕ ВПАДИНЫ ---
socket_size = 10;            // [mm] Socket size
socket_depth = 5;            // [mm] Socket depth

// --- BATTERY SHELF / ПОЛКА ДЛЯ БАТАРЕИ ---
shelf_thickness = 3;         // [mm]
shelf_distance_from_roof = 3; // [mm]
shelf_drop_offset = 15;      // [mm]
battery_cable_dia = 15;      // [mm]
rear_cutout_width = 80;      // [mm]
rear_cutout_height = 15;     // [mm]

// --- DISTANCE SENSOR / ДАТЧИК РАССТОЯНИЯ ---
sensor_hole_dia = 16.5;      // [mm]
sensor_spacing = 26;         // [mm]
sensor_height = 40;          // [mm]

// --- ROOF CAMERA / КАМЕРА НА КРЫШЕ ---
camera_hole_dia = 13.5;      // [mm]
camera_cable_dia = 18;       // [mm]
camera_position = 30;        // [mm]
cable_offset = 20;           // [mm]

// --- TEXT SETTINGS / НАСТРОЙКИ ТЕКСТА ---
text_depth = 1.0;            // [mm] Emboss/Deboss depth
font_style = "Liberation Sans:style=Bold"; 

// --- QUALITY / КАЧЕСТВО ---
$fn = 60;                    

/* =====================================================================
 *                         MODULES / МОДУЛИ
 * =====================================================================
 */

// FIXED: Module to place objects flush on the 70-degree tapered walls
module place_on_surface(h, side) {
    // Calculate how far the wall has receded at height h
    // tan(theta) = Opp/Adj -> Adj = Opp/tan(theta)
    offset_at_h = h / tan(taper_angle);
    
    // The rotation needed is exactly the taper angle (or negative)
    // to align the Z-axis (text face) with the wall normal.
    rot_angle = taper_angle; 

    if (side == "roof") {
        translate([0, 0, cabin_height])
        children();
    }
    else if (side == "right") {
        // Y positive side
        y_pos = (cabin_width / 2) - offset_at_h;
        translate([0, y_pos, h])
        rotate([-rot_angle, 0, 0]) // Rotate -70 deg around X
        children();
    }
    else if (side == "left") {
        // Y negative side
        y_pos = -(cabin_width / 2) + offset_at_h;
        translate([0, y_pos, h])
        rotate([rot_angle, 0, 0]) // Rotate +70 deg around X
        rotate([0, 0, 180])       // Flip text to read correctly from outside
        children();
    }
    else if (side == "front") {
        // X positive side
        x_pos = (cabin_length / 2) - offset_at_h;
        translate([x_pos, 0, h])
        rotate([0, rot_angle, 0]) // Tilt back
        rotate([0, 0, 90])        // Align text with Y axis
        children();
    }
    else if (side == "back") {
        // X negative side
        x_pos = -(cabin_length / 2) + offset_at_h;
        translate([x_pos, 0, h])
        rotate([0, -rot_angle, 0]) // Tilt back
        rotate([0, 0, -90])        // Align text with Y axis
        children();
    }
}

module emboss_text(t_string, t_size) {
    color("Gold")
    linear_extrude(height = text_depth, convexity = 4)
        text(t_string, size = t_size, font = font_style, valign = "center", halign = "center");
}

module name_dropping() {
    // 1. Robot - Roof Center-Right
    place_on_surface(cabin_height, "roof")
        translate([20, -30, 0]) 
        emboss_text("Robot", 12);

    // 2. Commerzbank - Left Wall
    place_on_surface(20, "left") 
        translate([0, 0, 0]) 
        emboss_text("Commerzbank", 10);

    // 3. MaxSoft - Right Wall
    place_on_surface(25, "right") 
        translate([30, 0, 0]) 
        emboss_text("MaxSoft", 11);

    // 4. AGI - Front Nose
    place_on_surface(30, "front") 
        translate([0, 0, 0]) 
        emboss_text("AGI", 10);

    // 5. Julia - Back Wall
    *place_on_surface(20, "back") 
        translate([-40, 0, 0]) 
        emboss_text("Julia", 12);

    // 6. Veronica - Roof Back
    place_on_surface(cabin_height, "roof")
        translate([-5, 0, 0]) 
        emboss_text("Veronica", 9);

    // 7. DARiA - Right Wall (Front area)
    place_on_surface(15, "right") 
        translate([-50, 0, 0]) 
        emboss_text("DARiA", 14);
}

// Main cabin body with 70° taper and CLOSED TOP (ROOF)
module cabin_body() {
    top_reduction = cabin_height / tan(taper_angle);
    top_length = cabin_length - 2 * top_reduction;
    top_width = cabin_width - 2 * top_reduction;
    
    hull() {
        translate([0, 0, 0])
            cube([cabin_length, cabin_width, 0.1], center = true);
        
        translate([0, 0, cabin_height])
            cube([top_length, top_width, 0.1], center = true);
    }
}

// Inner cavity (hollow interior)
module cabin_cavity() {
    top_reduction = cabin_height / tan(taper_angle);
    top_length = cabin_length - 2 * top_reduction - 2 * wall_thickness;
    top_width = cabin_width - 2 * top_reduction - 2 * wall_thickness;
    inner_length = cabin_length - 2 * wall_thickness;
    inner_width = cabin_width - 2 * wall_thickness;
    
    difference (){
        hull() {
            translate([0, 0, -1])
                cube([inner_length, inner_width, 0.1], center = true);
            
            translate([0, 0, cabin_height - wall_thickness])
                cube([top_length, top_width, 0.1], center = true);
        }
        battery_shelf();
    }
}

// Mounting socket
module mounting_socket() {
    translate([0, 0, socket_depth/2]) {
        cube([socket_size, socket_size, socket_depth + 0.2], center = true);
    }
}

// HORIZONTAL SHELF under roof for battery
module battery_shelf() {
    actual_z_center = cabin_height - shelf_distance_from_roof - shelf_thickness/2 - shelf_drop_offset;
    reduction = actual_z_center / tan(taper_angle);
    shelf_length = cabin_length - 2 * reduction - 2 * wall_thickness-50;
    shelf_width = cabin_width - 2 * reduction - 2 * wall_thickness;
    
    translate([-25, 0, actual_z_center]) {
        cube([shelf_length, shelf_width, shelf_thickness], center = true);
    }
}

// Rear cutout for battery access
module rear_battery_cutout() {
    shelf_top_z = cabin_height - shelf_distance_from_roof - shelf_drop_offset;
    cutout_z = shelf_top_z + rear_cutout_height/2;
    translate([-cabin_length/2, 0, cutout_z]) {
        cube([60, rear_cutout_width, rear_cutout_height], center = true);
    }
}

// Distance sensor holes
module sensor_holes() {
    extra_length = 30;
    translate([ 100, 0, -cabin_height/2 + sensor_height]) {
        translate([0, -sensor_spacing/2, 0])
            rotate([0, 90, 0])
                cylinder(h = wall_thickness + extra_length, d = sensor_hole_dia, center = true);
        
        translate([0, sensor_spacing/2, 0])
            rotate([0, 90, 0])
                cylinder(h = wall_thickness + extra_length, d = sensor_hole_dia, center = true);
    }
}

// Camera and cable holes
module roof_holes() {
    translate([0, 0, cabin_height]) {
        translate([cabin_length/2 - camera_position, 0, 0])
            cylinder(h = wall_thickness + 10, d = camera_hole_dia, center = true);
        
        translate([cabin_length/2 - camera_position - cable_offset, 0, 0])
            cylinder(h = wall_thickness + 10, d = camera_cable_dia, center = true);
    }
}

/* =====================================================================
 *                    MAIN ASSEMBLY / ОСНОВНАЯ СБОРКА
 * =====================================================================
 */

difference() {
    union() {
        cabin_body();
        battery_shelf();
        name_dropping(); // Text emboss
    }
    
    cabin_cavity();
    
    // Remove bottom
    translate([0, 0, -10])
        cube([cabin_length + 10, cabin_width + 10, 20], center = true);
    
    // Mounting sockets
    translate([cabin_length/2 - socket_size/2, cabin_width/2 - socket_size/2, 0]) mounting_socket();
    translate([cabin_length/2 - socket_size/2, -cabin_width/2 + socket_size/2, 0]) mounting_socket();
    translate([-cabin_length/2 + socket_size/2, cabin_width/2 - socket_size/2, 0]) mounting_socket();
    translate([-cabin_length/2 + socket_size/2, -cabin_width/2 + socket_size/2, 0]) mounting_socket();
    
    sensor_holes();
    roof_holes();
    rear_battery_cutout();
}