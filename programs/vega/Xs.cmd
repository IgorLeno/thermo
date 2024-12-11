@Echo off

REM Shell interface for X-Score

set _vegadir=%VEGADIR%
for /F "tokens=*" %%i in ('GetProgramData') do set _datadir=%%i
if exist "%_datadir%\VEGA ZZ" set _vegadir=%_datadir%\VEGA ZZ
set XSCORE_PARAMETER=%_vegadir%\Data\Xscore\

Xscore %*

set _datadir=
set _vegadir=
set XSCORE_PARAMETER=
