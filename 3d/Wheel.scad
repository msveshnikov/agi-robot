// Title: Parametric Servo Wheel with Tread (Improved Fit)
// Description: A wheel with a simple tread pattern, designed to be mounted on a standard servo horn (like SG90). This version has smaller mounting holes and a larger recess for the servo horn for an easier fit.
// Author: AI Assistant
// Date: 2023-10-27 (Updated)
// License: MIT

/*
 * =====================================================================
 * Параметры для настройки (Parameters for Customization)
 * =====================================================================
 */

// --- Основные параметры колеса (Main Wheel Parameters) ---
wheel_diameter = 60;    // [mm] Общий диаметр колеса.
wheel_thickness = 5;     // [mm] Общая толщина колеса.

// --- Параметры протектора (Tread Parameters) ---
tread_grooves = 40;      // Количество "зубцов" или выемок на протекторе. Поставьте 0, чтобы убрать протектор.
tread_groove_depth = 1.5; // [mm] Глубина выемки протектора.
tread_groove_width = 4;  // [mm] Ширина каждой выемки.

// --- Параметры крепления (Mounting Parameters) ---
// Расстояние между центрами двух крепёжных отверстий на серво-качалке.
mount_hole_distance = 32; // [mm] 
// Диаметр крепёжных отверстий в колесе.
mount_hole_diameter = 1; // [mm]  <<< ИЗМЕНЕНО: Уменьшено до 1 мм по вашему запросу.

// --- Параметры выемки под серво-качалку (Servo Horn Recess Parameters) ---
// Эти размеры основаны на стандартной качалке для SG90. Возможно, их придётся немного подогнать.

// Глубина, на которую качалка будет "утоплена" в колесо.
servo_horn_recess_depth = 2.5; // [mm] 
// Диаметр центрального отверстия для вала сервопривода.
servo_spline_hole_diameter = 6;  // [mm] 
// Диаметр центральной, круглой части серво-качалки.
servo_horn_hub_diameter = 7.5;   // [mm] <<< ИЗМЕНЕНО: Увеличено для более свободной посадки.
// Ширина "руки" серво-качалки.
servo_horn_arm_width = 6.5;      // [mm] <<< ИЗМЕНЕНО: Увеличено для более свободной посадки.

// --- Качество модели (Model Quality) ---
$fn = 100; // Количество сегментов для гладких окружностей.

/*
 * =====================================================================
 * Модули (Modules)
 * =====================================================================
 * Здесь код разбит на логические части для удобства чтения.
 */

// Модуль для создания основного тела колеса
module wheel_body() {
    // Создаем простой цилиндр, который будет основой колеса.
    cylinder(d = wheel_diameter, h = wheel_thickness);
}

// Модуль для создания протектора (выемок на поверхности)
module tread_cutter() {
    // Если количество выемок больше нуля, создаем их.
    if (tread_grooves > 0) {
        // Цикл для создания каждой выемки по окружности
        for (i = [0 : 360/tread_grooves : 359]) {
            rotate([0, 0, i]) {
                // Располагаем режущий куб на краю колеса.
                // Он смещён так, чтобы вырезать паз снаружи внутрь.
                // +1 и -1 по оси Z нужны для гарантированного чистого вырезания по всей толщине.
                translate([wheel_diameter/2 - tread_groove_depth, -tread_groove_width/2, -1]) {
                    cube([tread_groove_depth + 1, tread_groove_width, wheel_thickness + 2]);
                }
            }
        }
    }
}


// Модуль для создания выемки под серво-качалку
module servo_horn_cutout() {
    // Высота режущего объекта (чуть больше глубины для чистого выреза)
    cutter_h = servo_horn_recess_depth + 1;
    
    // Сдвигаем режущий объект вверх, чтобы он вырезал углубление с верхней стороны колеса.
    translate([0, 0, wheel_thickness - servo_horn_recess_depth]) {
        // Используем hull() для создания формы, повторяющей серво-качалку.
        hull() {
            // Центральная круглая часть
            cylinder(d = servo_horn_hub_diameter, h = cutter_h);
            
            // "Рука" качалки в одном направлении
            translate([mount_hole_distance / 2, 0, 0])
                cylinder(d = servo_horn_arm_width, h = cutter_h);
                
            // "Рука" качалки в другом направлении
            translate([-mount_hole_distance / 2, 0, 0])
                cylinder(d = servo_horn_arm_width, h = cutter_h);
        }
    }
}

// Модуль для создания всех сквозных отверстий
module all_holes() {
    // Делаем цилиндры для вырезания отверстий длиннее толщины колеса,
    // чтобы гарантировать сквозное прохождение.
    hole_h = wheel_thickness + 2;
    
    // Сдвигаем все отверстия в центр толщины колеса по оси Z для вырезания.
    translate([0, 0, wheel_thickness / 2]) {
        // 1. Центральное отверстие для вала сервопривода
        cylinder(d = servo_spline_hole_diameter, h = hole_h, center = true);
        
        // 2. Крепёжное отверстие №1
        translate([mount_hole_distance / 2, 0, 0])
            cylinder(d = mount_hole_diameter, h = hole_h, center = true);
        
        // 3. Крепёжное отверстие №2
        translate([-mount_hole_distance / 2, 0, 0])
            cylinder(d = mount_hole_diameter, h = hole_h, center = true);
    }
}

/*
 * =====================================================================
 * Основной код (Main Code)
 * =====================================================================
 * Собираем финальную модель, вычитая из основного тела все вырезы.
 */

module wheel() {
difference() {
    // 1. Создаём основное тело колеса
    wheel_body();
    
    // 2. Вырезаем протектор
    tread_cutter();
    
    // 3. Вычитаем из него выемку под серво-качалку
    servo_horn_cutout();
    
    // 4. Вычитаем все сквозные отверстия
    all_holes();
}
}

wheel();