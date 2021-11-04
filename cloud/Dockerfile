FROM tensorflow/tensorflow:2.5.0
WORKDIR /app
ADD ./requirements.txt requirements.txt
RUN pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
ADD . /app
EXPOSE 8080
CMD ["python","/app/main.py"]