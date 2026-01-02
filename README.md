create virtual environment in you project's directory: python -m venv venv

activate it: venv\Scripts\activate

git pull origin main

install all the required packages:
pip install -r requirements.txt

python train_model.py -> model/model.h5 and model/tokenizer.pl will be created.

python app.py -> to host server which will listen to all review flagging requests from the extractor

to turn on extension -> go to chrome -> extensions -> load unpacked -> open extensions folder from the project directory and you are done
