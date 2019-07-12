FROM centos:7
LABEL maintainer="dilaksun@hotmail.com"

RUN python -m virtualenv venv

RUN source venv/bin/activate

RUN pip install -r requirements.txt

RUN python initial.py

RUN python app.py


