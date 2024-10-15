# Notes

## Run Flask App
- `source .venv/Scripts/Activate`
- make sure `which pip` is in the right folder for activated environment if installing requirements with `pip install -r requirements.txt`
- run app with `python app.py`

## Install Pip Packages
- export TMPDIR=/home/ec2-user/pip_cache
- pip install -r requirements.txt --no-cache-dir

## Run Flask App - EC2
- Not on windows: `nohup gunicorn -w 1 -b 0.0.0.0:5000 app:app > gunicorn_output.log 2>&1 &`

## Misc
- `aws s3 cp s3://michael-models/fasterrcnn_resnet50_fpn.pth .`
- show ec2 cpu usage - `mpstat`
- show processes `ps`

## Start nginx - Frontend
- `sudo systemctl start nginx`
- `sudo systemctl status nginx`
- `sudo systemctl restart nginx`
