@echo off
setlocal enabledelayedexpansion

set "REMOTE_USER=ubuntu"
set "REMOTE_HOST=mvpgen.com"
set "REMOTE_DIR=/home/ubuntu"
set "DB_NAME=agi-robot"
set "CONTAINER_NAME=agi-robot-mongodb"

echo Starting export of MongoDB collections...

ssh -l %REMOTE_USER% %REMOTE_HOST% "docker exec %CONTAINER_NAME% mongoexport --db %DB_NAME% --collection blogposts --type=csv --fields=_id,title,content,author,slug,isPublished,tags,likes,views > blogposts.csv"
ssh -l %REMOTE_USER% %REMOTE_HOST% "docker exec %CONTAINER_NAME% mongoexport --db %DB_NAME% --collection cognitivelogs --type=csv --fields=_id,plan,subplan,memory,goal,timestamp > cognitivelogs.csv"
ssh -l %REMOTE_USER% %REMOTE_HOST% "docker exec %CONTAINER_NAME% mongoexport --db %DB_NAME% --collection commandlogs --type=csv --fields=_id,timestamp,command_type,command_data,llm_response,source > commandlogs.csv"
ssh -l %REMOTE_USER% %REMOTE_HOST% "docker exec %CONTAINER_NAME% mongoexport --db %DB_NAME% --collection robotstates --type=csv --fields=_id,agi,asi,speed,panic,forward,back,left,right,lang,goal,rgb.hue,rgb.sat,rgb.bri,rgb.swi,arm1,arm2,distance,temperature,humidity,plan,subplan,space_map,movement_history,memory,alarm,timestamp > robotstates.csv"
ssh -l %REMOTE_USER% %REMOTE_HOST% "docker exec %CONTAINER_NAME% mongoexport --db %DB_NAME% --collection telemetrylogs --type=csv --fields=_id,timestamp,distance,temperature,humidity,position_estimate.x,position_estimate.y > telemetrylogs.csv"

echo Downloading collections...
scp %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%/blogposts.csv .
scp %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%/cognitivelogs.csv .
scp %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%/commandlogs.csv .
scp %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%/robotstates.csv .
scp %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%/telemetrylogs.csv .

echo Done.
