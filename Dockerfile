FROM python:2.7
COPY mock_F5.py .
COPY MockSSH.py .
COPY requirements.txt .
CMD apt update
CMD pip install -r requirements.txt
CMD python --version
RUN python mock_F5.py

