// Title: Detailed Robot Model (Fixed Assembly)
// Description: Подробная 3D модель робота с правильными соединениями всех частей
// Author: AI Assistant
// Date: 2024-12-19
// License: MIT

/*===== ПАРАМЕТРЫ =====*/
// Общие настройки
scale_factor = 1.0;
$fn = 50; // Качество округлых форм

// Голова
head_radius = 12;
eye_radius = 2;
antenna_height = 8;

// Шея
neck_radius = 3;
neck_height = 8;

// Торс
torso_width = 25;
torso_depth = 15;
torso_height = 35;

// Плечи и руки
shoulder_width = 8;
shoulder_height = 6;
upper_arm_length = 20;
lower_arm_length = 18;
arm_radius = 3;

// Кисти
hand_width = 6;
hand_depth = 4;
hand_height = 8;
finger_length = 6;

// Таз и ноги
hip_width = 6;
hip_height = 4;
upper_leg_length = 22;
lower_leg_length = 20;
leg_radius = 3.5;

// Ступни
foot_length = 12;
foot_width = 6;
foot_height = 4;

/*===== МОДУЛИ =====*/

// Главная сборка робота
module robot() {
    scale(scale_factor) {
        // Торс (центр координат)
        torso();
        
        // Шея и голова
        translate([0, 0, torso_height/2]) {
            neck();
            translate([0, 0, neck_height]) {
                head();
            }
        }
        
        // Левое плечо и рука
        translate([-torso_width/2, 0, torso_height/2 - 3]) {
            left_shoulder_arm();
        }
        
        // Правое плечо и рука
        translate([torso_width/2, 0, torso_height/2 - 3]) {
            right_shoulder_arm();
        }
        
        // Левый таз и нога
        translate([-torso_width/4, 0, -torso_height/2]) {
            left_hip_leg();
        }
        
        // Правый таз и нога
        translate([torso_width/4, 0, -torso_height/2]) {
            right_hip_leg();
        }
    }
}

// Модуль: голова с деталями
module head() {
    // Основная голова
    color("lightblue") 
        sphere(r = head_radius);
    
    // Глаза
    translate([head_radius * 0.4, head_radius * 0.7, head_radius * 0.2]) {
        color("white") sphere(r = eye_radius);
        translate([0, eye_radius * 0.3, 0])
            color("black") sphere(r = eye_radius * 0.6);
    }
    
    translate([-head_radius * 0.4, head_radius * 0.7, head_radius * 0.2]) {
        color("white") sphere(r = eye_radius);
        translate([0, eye_radius * 0.3, 0])
            color("black") sphere(r = eye_radius * 0.6);
    }
    
    // Рот
    translate([0, head_radius * 0.8, -head_radius * 0.3])
        color("red") 
        rotate([90, 0, 0])
        cylinder(h = 1, r = 3, center = true);
    
    // Антенна
    translate([0, 0, head_radius]) {
        color("silver") cylinder(h = antenna_height, r = 0.8);
        translate([0, 0, antenna_height])
            color("red") sphere(r = 2);
    }
    
    // Уши
    translate([head_radius * 0.9, 0, head_radius * 0.3])
        color("gray") cylinder(h = 4, r = 2, center = true);
    translate([-head_radius * 0.9, 0, head_radius * 0.3])
        color("gray") cylinder(h = 4, r = 2, center = true);
}

// Модуль: шея
module neck() {
    color("silver") 
        cylinder(h = neck_height, r = neck_radius);
    
    // Соединительные кольца
    for (z = [neck_height * 0.3, neck_height * 0.7]) {
        translate([0, 0, z])
            color("darkgray")
            cylinder(h = 1, r = neck_radius + 0.5);
    }
}

// Модуль: торс с деталями
module torso() {
    // Основной торс
    color("gray") 
        cube([torso_width, torso_depth, torso_height], center = true);
    
    // Передняя панель
    translate([0, torso_depth/2 + 0.5, 0]) {
        color("darkblue") 
            cube([torso_width * 0.8, 1, torso_height * 0.6], center = true);
        
        // Индикаторы на панели
        for (x = [-6, -2, 2, 6]) {
            for (z = [-8, -4, 0, 4, 8]) {
                translate([x, 0.5, z])
                    color("lime") 
                    cylinder(h = 1, r = 0.8);
            }
        }
        
        // Центральный экран
        translate([0, 0.5, 5])
            color("black") 
            cube([8, 1, 6], center = true);
    }
    
    // Вентиляционные отверстия по бокам
    for (side = [-1, 1]) {
        for (z = [-10, -5, 0, 5, 10]) {
            translate([side * torso_width/2, 0, z])
                rotate([0, 90, 0])
                color("black")
                cylinder(h = 2, r = 1, center = true);
        }
    }
}

// Модуль: левое плечо и рука
module left_shoulder_arm() {
    // Плечевой сустав
    color("silver") 
        rotate([0, 90, 0])
        cylinder(h = shoulder_width, r = shoulder_height/2, center = true);
    
    // Верхняя часть руки
    translate([-shoulder_width/2, 0, -upper_arm_length/2]) {
        color("lightgray") 
            cylinder(h = upper_arm_length, r = arm_radius, center = true);
        
        // Локтевой сустав
        translate([0, 0, -upper_arm_length/2]) {
            color("silver") sphere(r = arm_radius + 1);
            
            // Нижняя часть руки
            translate([0, 0, -lower_arm_length/2]) {
                color("lightgray") 
                    cylinder(h = lower_arm_length, r = arm_radius * 0.8, center = true);
                
                // Кисть
                translate([0, 0, -lower_arm_length/2])
                    left_hand();
            }
        }
    }
}

// Модуль: правое плечо и рука
module right_shoulder_arm() {
    // Плечевой сустав
    color("silver") 
        rotate([0, 90, 0])
        cylinder(h = shoulder_width, r = shoulder_height/2, center = true);
    
    // Верхняя часть руки
    translate([shoulder_width/2, 0, -upper_arm_length/2]) {
        color("lightgray") 
            cylinder(h = upper_arm_length, r = arm_radius, center = true);
        
        // Локтевой сустав
        translate([0, 0, -upper_arm_length/2]) {
            color("silver") sphere(r = arm_radius + 1);
            
            // Нижняя часть руки
            translate([0, 0, -lower_arm_length/2]) {
                color("lightgray") 
                    cylinder(h = lower_arm_length, r = arm_radius * 0.8, center = true);
                
                // Кисть
                translate([0, 0, -lower_arm_length/2])
                    right_hand();
            }
        }
    }
}

// Модуль: левая кисть
module left_hand() {
    // Ладонь
    color("darkgray") 
        cube([hand_width, hand_depth, hand_height], center = true);
    
    // Пальцы
    for (i = [-1.5, -0.5, 0.5, 1.5]) {
        translate([i * 1.2, hand_depth/2, -hand_height/2]) {
            color("silver") 
                cylinder(h = finger_length, r = 0.6);
            // Суставы пальцев
            translate([0, 0, finger_length * 0.6])
                color("gold") sphere(r = 0.8);
        }
    }
    
    // Большой палец
    translate([hand_width/2, 0, -hand_height/4])
        rotate([0, 45, 0])
        color("silver") 
        cylinder(h = finger_length * 0.8, r = 0.7);
}

// Модуль: правая кисть
module right_hand() {
    // Ладонь
    color("darkgray") 
        cube([hand_width, hand_depth, hand_height], center = true);
    
    // Пальцы
    for (i = [-1.5, -0.5, 0.5, 1.5]) {
        translate([i * 1.2, hand_depth/2, -hand_height/2]) {
            color("silver") 
                cylinder(h = finger_length, r = 0.6);
            // Суставы пальцев
            translate([0, 0, finger_length * 0.6])
                color("gold") sphere(r = 0.8);
        }
    }
    
    // Большой палец
    translate([-hand_width/2, 0, -hand_height/4])
        rotate([0, -45, 0])
        color("silver") 
        cylinder(h = finger_length * 0.8, r = 0.7);
}

// Модуль: левый таз и нога
module left_hip_leg() {
    // Тазобедренный сустав
    color("silver") 
        rotate([90, 0, 0])
        cylinder(h = hip_height, r = hip_width/2, center = true);
    
    // Верхняя часть ноги
    translate([0, 0, -upper_leg_length/2]) {
        color("gray") 
            cylinder(h = upper_leg_length, r = leg_radius, center = true);
        
        // Коленный сустав
        translate([0, 0, -upper_leg_length/2]) {
            color("silver") sphere(r = leg_radius + 1);
            
            // Нижняя часть ноги
            translate([0, 0, -lower_leg_length/2]) {
                color("gray") 
                    cylinder(h = lower_leg_length, r = leg_radius * 0.9, center = true);
                
                // Ступня
                translate([0, 0, -lower_leg_length/2])
                    left_foot();
            }
        }
    }
}

// Модуль: правый таз и нога
module right_hip_leg() {
    // Тазобедренный сустав
    color("silver") 
        rotate([90, 0, 0])
        cylinder(h = hip_height, r = hip_width/2, center = true);
    
    // Верхняя часть ноги
    translate([0, 0, -upper_leg_length/2]) {
        color("gray") 
            cylinder(h = upper_leg_length, r = leg_radius, center = true);
        
        // Коленный сустав
        translate([0, 0, -upper_leg_length/2]) {
            color("silver") sphere(r = leg_radius + 1);
            
            // Нижняя часть ноги
            translate([0, 0, -lower_leg_length/2]) {
                color("gray") 
                    cylinder(h = lower_leg_length, r = leg_radius * 0.9, center = true);
                
                // Ступня
                translate([0, 0, -lower_leg_length/2])
                    right_foot();
            }
        }
    }
}

// Модуль: левая ступня
module left_foot() {
    // Основание ступни
    translate([0, foot_length/4, -foot_height/2])
        color("black") 
        cube([foot_width, foot_length, foot_height], center = true);
    
    // Пятка
    translate([0, -foot_length/4, -foot_height/2])
        color("black") 
        cylinder(h = foot_height, r = foot_width/2, center = true);
    
    // Носок
    translate([0, foot_length/2, -foot_height/2])
        color("black") 
        sphere(r = foot_width/2);
}

// Модуль: правая ступня
module right_foot() {
    // Основание ступни
    translate([0, foot_length/4, -foot_height/2])
        color("black") 
        cube([foot_width, foot_length, foot_height], center = true);
    
    // Пятка
    translate([0, -foot_length/4, -foot_height/2])
        color("black") 
        cylinder(h = foot_height, r = foot_width/2, center = true);
    
    // Носок
    translate([0, foot_length/2, -foot_height/2])
        color("black") 
        sphere(r = foot_width/2);
}

/*===== ОСНОВНОЙ КОД =====*/
// Отображение полной модели робота
robot();

// Для отладки отдельных частей (раскомментируйте нужное):
// head();
// torso();
// left_shoulder_arm();
// right_shoulder_arm();
// left_hip_leg();
// right_hip_leg();