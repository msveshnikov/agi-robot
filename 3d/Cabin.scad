// --- CABIN DIMENSIONS / РАЗМЕРЫ КАБИНЫ ---
cabin_length = 220;          // [мм] Length (front to back) / Длина
cabin_width = 120;           // [мм] Width (side to side) / Ширина
cabin_height = 40;           // [мм] Height / Высота
wall_thickness = 3;          // [мм] Wall thickness / Толщина стенок
taper_angle = 70;            // [градусы] Taper angle (narrowing to top) / Угол сужения кверху

// --- MOUNTING SOCKETS / МОНТАЖНЫЕ ВПАДИНЫ ---
socket_size = 10;            // [мм] Socket size (1x1 cm) / Размер впадины
socket_depth = 5;            // [мм] Socket depth (0.5 cm) / Глубина впадины

// --- BATTERY SHELF / ПОЛКА ДЛЯ БАТАРЕИ ---
shelf_thickness = 3;         // [мм] Shelf thickness / Толщина полки
shelf_distance_from_roof = 3; // [мм] Distance from roof to shelf definition / Отступ
shelf_drop_offset = 15;      // [mm] Extra drop used in your original code / Дополнительное смещение вниз
battery_cable_dia = 15;      // [мм] Battery cable hole / Отверстие для шнура батареи
rear_cutout_width = 80;      // [мм] Rear cutout width / Ширина выреза сзади
rear_cutout_height = 15;     // [мм] Rear cutout height / Высота выреза сзади

// --- DISTANCE SENSOR / ДАТЧИК РАССТОЯНИЯ ---
sensor_hole_dia = 16.5;      // [мм] Sensor hole diameter / Диаметр отверстия датчика
sensor_spacing = 26;         // [мм] Distance between sensor holes / Расстояние между отверстиями
sensor_height = 40;          // [мм] Height from bottom / Высота от низа

// --- ROOF CAMERA / КАМЕРА НА КРЫШЕ ---
camera_hole_dia = 13.5;      // [мм] Camera hole diameter / Диаметр отверстия камеры
camera_cable_dia = 15;       // [мм] Camera cable hole / Отверстие для шнура камеры
camera_position = 30;        // [мм] Distance from front / Расстояние от передней части
cable_offset = 20;           // [мм] Distance behind camera / Расстояние за камерой

// --- QUALITY / КАЧЕСТВО ---
$fn = 60;                    // Circle resolution / Разрешение окружностей

/* =====================================================================
 *                         MODULES / МОДУЛИ
 * =====================================================================
 */

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
    // FIXED: Calculate Z based on the extra drop so dimensions are correct
    actual_z_center = cabin_height - shelf_distance_from_roof - shelf_thickness/2 - shelf_drop_offset;
    
    // FIXED: Calculate width/length based on the ACTUAL height, not the roof height
    // This ensures the shelf touches the tapered walls
    reduction = actual_z_center / tan(taper_angle);
    shelf_length = cabin_length - 2 * reduction - 2 * wall_thickness-50;
    shelf_width = cabin_width - 2 * reduction - 2 * wall_thickness;
    
    translate([-25, 0, actual_z_center]) {
        
            cube([shelf_length, shelf_width, shelf_thickness], center = true);
            
           
        
    }
}

// Rear cutout for battery access
module rear_battery_cutout() {
    // FIXED: Align cutout with the lowered shelf position
    // Shelf Top Z = (cabin_height - shelf_distance_from_roof - shelf_drop_offset)
    shelf_top_z = cabin_height - shelf_distance_from_roof - shelf_drop_offset;
    
    // Position cutout so its bottom is flush with the shelf top
    cutout_z = shelf_top_z + rear_cutout_height/2;
    
    // FIXED: Increased X depth (60mm) and pushed deeper to ensure it cuts the tapered wall
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