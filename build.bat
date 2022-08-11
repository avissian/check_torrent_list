call .\venv\Scripts\activate
pip install -r requirements.txt

pyinstaller.exe --onefile --noupx main.py
move /Y .\dist\main.exe .\dist\check_torrent_list.exe
copy /Y .\config.yml .\dist\
rd /S /Q build
del /F /Q main.spec
call deactivate

