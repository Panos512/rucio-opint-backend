FROM centos:7
LABEL maintainer="dilaksun@hotmail.com"

EXPOSE 8080

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["initial.py", "app.py"]


