FROM python:2.7
COPY mock_F5.py .
COPY MockSSH.py .
COPY requirements.txt .
CMD apt update
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "mock_F5.py"]

