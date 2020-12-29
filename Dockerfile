FROM arm32v7/python:3.6
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "/app/main.py", "drive"]