# Multiple Movement Commands Update

## Summary
Updated the AGI robot to support **multiple sequential movement commands** in a single LLM response, allowing the robot to plan and execute complex maneuvers (e.g., "turn left 30°, move forward 50cm, turn right 45°") in one decision cycle.

## Changes Made

### 1. `media_service.py`
- **Line 260**: Changed the LLM prompt from single `move` object to `moves` array
- **New format**: `"moves": ARRAY of movement commands [{"command": "forward"|"back"|"left"|"right"|"stop", "distance_cm": int (20-300), "angle_deg": int (10-180)}]`
- **Max**: 5 moves per response
- **Example**: 
  ```json
  {
    "moves": [
      {"command": "left", "angle_deg": 30},
      {"command": "forward", "distance_cm": 50},
      {"command": "right", "angle_deg": 45}
    ]
  }
  ```

### 2. `main.py`
- **Lines 420-483**: Completely refactored movement handling in `agi_loop()`
  - Now processes `moves` array (if present)
  - Iterates through each movement command sequentially
  - Executes commands one by one using `Bridge.notify("move", move_cmd, is_last_move)`
  - Adds small delay (0.2s) between moves for stability
  - Maintains backward compatibility with single `move` command
  - Each move is added to `movement_history` for LLM context

- **Lines 357-369**: Updated docstring to reflect new API

### 3. `sketch.ino`
- **No changes needed**: The existing `move()` function already supports the command protocol and the `stop` parameter controls whether to stop after execution
- The sketch receives sequential commands from Python and executes them correctly

## How It Works

1. **LLM Decision**: The LLM now returns an array of movement commands in the `moves` field
2. **Sequential Execution**: Python iterates through each command and sends them to Arduino one by one
3. **History Tracking**: Each executed move is added to `movement_history` so the LLM has context
4. **Stability**: Small delays between moves ensure smooth execution

## Example LLM Response

```json
{
  "speak": {"text": "I'll navigate around the obstacle"},
  "sound": null,
  "moves": [
    {"command": "left", "angle_deg": 45},
    {"command": "forward", "distance_cm": 30},
    {"command": "right", "angle_deg": 45},
    {"command": "forward", "distance_cm": 20}
  ],
  "rgb": "255,165,0",
  "plan": "Navigating around detected obstacle",
  "subplan": "Turning left, advancing, then correcting course",
  "space_map": "...",
  "memory": "...",
  "alarm": null
}
```

## Benefits

1. **Smarter Navigation**: Robot can plan multi-step maneuvers
2. **Better Obstacle Avoidance**: Can execute scanning patterns (e.g., look left, look right, then decide)
3. **More Efficient**: Reduces LLM calls by batching movements
4. **Backward Compatible**: Still supports single `move` command for simple cases

## Testing Recommendations

1. Test with simple single-move commands to ensure backward compatibility
2. Test with multi-move sequences (2-3 moves)
3. Test edge cases: empty moves array, invalid commands, mixed valid/invalid moves
4. Monitor the `movement_history` to ensure it's being populated correctly
5. Test that the robot stops between moves as expected
