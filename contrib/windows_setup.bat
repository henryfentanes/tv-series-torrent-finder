@ECHO OFF
cd ../
echo "######################## Installing requirements ########################"
pip install -r requirements.txt
echo "######################## Running the Tests ########################"
python tests.py
echo "######################## Setting Up ########################"
echo "You may leave empty parameters, but remember to provide at least one source of Series (list or folder)"
echo "TV Series List must be separated by commas (e.g.:TV.Series.One,Tv.Series.Two,...)"
set final_query=python downloader.py
set /p sl="Please, provide a list of tv series: "
if not "%sl%"=="" (set final_query=%final_query% -sl %sl%)
set /p sf="Please, provide a folder with tv series folders inside: "
if not "%sf%"=="" (set final_query=%final_query% -sf %sf%)
set /p df="Please, provide a download folder: "
if not "%df%"=="" (set final_query=%final_query% -df %df%)
echo %final_query%
%final_query%
echo "Thank you, your downloader should be configured by now. If you wanna change anything you may go directly into the settings or watchlist (.json)"
pause