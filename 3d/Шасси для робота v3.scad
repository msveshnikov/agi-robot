// Title: Шасси для робота (Robot Chassis) v3
// Description: Параметрическое шасси с двумя креплениями для сервоприводов и сквозными отверстиями для осей.
// Author: AI Assistant
// Date: 2023-10-28
// License: MIT

/*
 * =====================================================================
 * Параметры для настройки (Parameters for Customization)
 * =====================================================================
 */

// --- Размеры шасси ---
chassis_length = 240;  // [mm] Длина корпуса (ось Y)
chassis_width = 120;   // [mm] Ширина корпуса (ось X)
chassis_height = 40;   // [mm] Высота корпуса (ось Z)
wall_thickness = 3;    // [mm] Толщина всех стенок

// --- Вырезы для сервоприводов ---
servo_cutout_width = 24;   // [mm] Ширина паза для корпуса серво (по оси Y)
servo_cutout_height = 12;  // [mm] Высота паза для корпуса серво (по оси Z)
servo_hole_distance = 28;  // [mm] Расстояние между центрами крепежных отверстий
servo_hole_diameter = 1.5; // [mm] Диаметр крепежных отверстий
servo_pos_from_front = 50; // [mm] Расстояние от центральной линии серво до передней части шасси

// --- Задние вырезы (для пассивных колес) ---
rear_hole_diameter = 6;   // [mm] Диаметр отверстия
rear_hole_pos_from_back = 40; // [mm] Расстояние от центра отверстия до задней части шасси

// --- Общие параметры вырезов ---
cutouts_z_pos = 20; // [mm] Высота центров всех вырезов от нижней плоскости шасси

// --- Верхние крепежные штыри ---
post_size = 10;       // [mm] Размер стороны квадратного штыря
post_height = 5;      // [mm] Высота штыря над основной высотой шасси

// --- Качество модели ---
$fn = 100;

/*
 * =====================================================================
 * Модули (Modules)
 * =====================================================================
 */

// Модуль для создания полого корпуса
module chassis_body() {
    difference() {
        // Внешний параллелепипед
        cube([chassis_width, chassis_length, chassis_height]);
        
        // Внутренний вырез (создает полый корпус с дном)
        translate([wall_thickness, wall_thickness, wall_thickness]) {
            cube([
                chassis_width - 2 * wall_thickness, 
                chassis_length - 2 * wall_thickness, 
                chassis_height
            ]);
        }
    }
}

// Модуль для создания крепежных штырей
module mounting_posts() {
    // Штыри теперь являются продолжением углов корпуса.
    translate([0, 0, chassis_height])
        cube([post_size, post_size, post_height]);
    translate([chassis_width - post_size, 0, chassis_height])
        cube([post_size, post_size, post_height]);
    translate([0, chassis_length - post_size, chassis_height])
        cube([post_size, post_size, post_height]);
    translate([chassis_width - post_size, chassis_length - post_size, chassis_height])
        cube([post_size, post_size, post_height]);
}


/*
 * =====================================================================
 * Основной код (Main Code)
 * =====================================================================
 */

difference() {
    // 1. Создаем основной корпус и добавляем к нему штыри
    union() {
        chassis_body();
        mounting_posts();
    }
    
    // =====================================================================
    // 2. Вырезаем крепления для сервоприводов
    // =====================================================================
    y_center = chassis_length - servo_pos_from_front;
    z_center = cutouts_z_pos;
    
    // --- Левый сервопривод ---
    // Основной паз
    translate([-1, y_center - servo_cutout_width/2, z_center - servo_cutout_height/2]) {
        cube([wall_thickness + 2, servo_cutout_width, servo_cutout_height]);
    }
    // Крепежные отверстия
    translate([wall_thickness/2, y_center - servo_hole_distance/2, z_center]) {
        rotate([0, 90, 0]) cylinder(d=servo_hole_diameter, h=wall_thickness*3, center=true);
    }
    translate([wall_thickness/2, y_center + servo_hole_distance/2, z_center]) {
        rotate([0, 90, 0]) cylinder(d=servo_hole_diameter, h=wall_thickness*3, center=true);
    }
    
    // --- Правый сервопривод ---
    // Основной паз
    translate([chassis_width - wall_thickness, y_center - servo_cutout_width/2, z_center - servo_cutout_height/2]) {
        cube([wall_thickness + 2, servo_cutout_width, servo_cutout_height]);
    }
    // Крепежные отверстия
    translate([chassis_width - wall_thickness/2, y_center - servo_hole_distance/2, z_center]) {
        rotate([0, 90, 0]) cylinder(d=servo_hole_diameter, h=wall_thickness*3, center=true);
    }
    translate([chassis_width - wall_thickness/2, y_center + servo_hole_distance/2, z_center]) {
        rotate([0, 90, 0]) cylinder(d=servo_hole_diameter, h=wall_thickness*3, center=true);
    }
    
    // =====================================================================
    // 3. Вырезаем задние сквозные отверстия для осей
    // =====================================================================
    // Левое отверстие
    translate([-1, rear_hole_pos_from_back, cutouts_z_pos]) {
        rotate([0, 90, 0])
            cylinder(d = rear_hole_diameter, h = wall_thickness + 2);
    }
    // Правое отверстие
    translate([chassis_width - wall_thickness, rear_hole_pos_from_back, cutouts_z_pos]) {
        rotate([0, 90, 0])
            cylinder(d = rear_hole_diameter, h = wall_thickness + 2);
    }
}
