# Backend Data Models

This document outlines the Mongoose models used in the AGI Robot backend.

## 1. BlogPost

Represents a generated blog post, typically creating a narrative from the robot's logs.

- **File**: `models/BlogPost.js`
- **Schema**:
  - `title` (String, required): The title of the blog post.
  - `content` (String, required): The main body text of the post.
  - `date` (Date, default: `Date.now`): When the post was created. Indexed for sorting.
  - `logsCount` (Number, required): Number of logs aggregated to create this post.
  - `timestamps`: Automatically manages `createdAt` and `updatedAt`.

## 2. CognitiveLog

Stores the robot's internal cognitive state, including plans and goals.

- **File**: `models/CognitiveLog.js`
- **Schema**:
  - `plan` (String): The high-level plan the robot is executing.
  - `subplan` (String): Specific steps or immediate sub-goals.
  - `memory` (String): Short-term or context-specific memory string.
  - `goal` (String): The current overarching goal.
  - `timestamp` (Date, default: `Date.now`): Time of the log entry. Indexed.
  - `timestamps`: Automatically manages `createdAt` and `updatedAt`.

## 3. CommandLog

Records commands sent to or executed by the robot.

- **File**: `models/CommandLog.js`
- **Schema**:
  - `timestamp` (Date, default: `Date.now`): Time of the command. Indexed.
  - `command_type` (String, required): Type of command. 
    - Enum: `['move', 'turn', 'stop', 'agi', 'panic', 'speak', 'rgb', 'arm']`
  - `command_data` (Mixed): Additional parameters for the command (e.g., speed, angle).
  - `llm_response` (Mixed): The raw response from the LLM if the command originated there.
  - `source` (String, default: 'user'): Origin of the command.
    - Enum: `['user', 'agi', 'panic', 'api']`
  - `timestamps`: Automatically manages `createdAt` and `updatedAt`.

## 4. RobotState

The single source of truth for the robot's current capabilities and status. Note that this collection likely contains a single document representing the "current" state.

- **File**: `models/RobotState.js`
- **Schema**:
  - **Control Variables**:
    - `agi` (Boolean): AGI mode active.
    - `asi` (Boolean): ASI mode active.
    - `speed` (Number): Movement speed (0-90).
    - `panic` (Boolean): Emergency stop state.
    - `forward`, `back`, `left`, `right` (Boolean): Directional flags.
    - `lang` (String): Language setting (default 'en').
    - `goal` (String): Current mission statement.
  - **RGB Control** (HSV format):
    - `rgb.hue` (0-360)
    - `rgb.sat` (0-100)
    - `rgb.bri` (0-100)
    - `rgb.swi` (Boolean): Switch state.
  - **Arm Control**:
    - `arm1` (Number): Position of arm joint 1 (0-180).
    - `arm2` (Number): Position of arm joint 2 (0-180).
  - **Telemetry** (Read-only):
    - `distance` (Number): Ultrasonic sensor reading.
    - `temperature` (Number)
    - `humidity` (Number)
  - **Planning & Memory**:
    - `plan`, `subplan`, `space_map`, `memory`.
    - `movement_history` (Array of Strings).
  - **Alarm**:
    - `alarm` (String)
  - `updated_at` (Date): Manually updated on save.
  - `timestamps`: Automatically manages `createdAt` and `updatedAt`.

## 5. TelemetryLog

Historical record of sensor data.

- **File**: `models/TelemetryLog.js`
- **Schema**:
  - `timestamp` (Date, default: `Date.now`): Indexed.
  - `distance` (Number, required): Distance sensor reading.
  - `temperature` (Number)
  - `humidity` (Number)
  - `position_estimate`:
    - `x` (Number)
    - `y` (Number)
  - `timestamps`: Automatically manages `createdAt` and `updatedAt`.
