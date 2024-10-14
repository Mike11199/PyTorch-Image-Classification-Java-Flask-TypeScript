# Notes

## Run Flask App
- `source .venv/Scripts/Activate`
- make sure `which pip` is in the right folder for activated environment if installing requirements with `pip install -r requirements.txt`
- run app with `python app.py`

## Run Flask App - EC2
- Not on windows: `nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > gunicorn_output.log 2>&1 &`

