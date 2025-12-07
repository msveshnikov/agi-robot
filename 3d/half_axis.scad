// Title: Axle with Inscribed Square End
// Description: A parametric axle with a square head that is perfectly inscribed within the axle's diameter.
// Author: AI Assistant
// Date: 2023-10-28
// License: MIT

/*
 * =====================================================================
 * Параметры для настройки (Parameters for Customization)
 * =====================================================================
 */

// --- Параметры оси ---
axle_diameter = 5;    // [mm] Диаметр основной цилиндрической части.
axle_stop_diameter=10;

axle_length = 10;   // [mm] Длина цилиндрической части.

// --- Параметры головки ---
// Длина стороны квадрата рассчитывается так, чтобы он был вписан в окружность оси.
// Диагональ квадрата будет равна диаметру оси.
square_head_side = axle_diameter / sqrt(2); 
square_head_height = 2; // [mm] Высота (толщина) квадратной головки.

// --- Параметры отверстия ---
hole_diameter = 1.5;  // [mm] Диаметр сквозного центрального отверстия.

// --- Качество модели ---
$fn = 80; // Количество сегментов для гладких окружностей.

/*
 * =====================================================================
 * Основной код (Main Code)
 * =====================================================================
 */

difference() {
    union() {
        // 1. Ось
        cylinder(d = axle_diameter, h = axle_length);
        cylinder(d=axle_stop_diameter, h=5);
        
        // 2. Квадратная головка
        translate([0, 0, axle_length + square_head_height / 2]) {
            cube([square_head_side, square_head_side, square_head_height], center = true);
        }
    }
    
    // 3. Отверстие
    total_length = axle_length + square_head_height;
    translate([0, 0, -1]) {
        cylinder(d = hole_diameter, h = total_length + 2);
    }
}
