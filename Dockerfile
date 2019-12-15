FROM circleci/python2.7
COPY mock_F5.py .
COPY MockSSH.py .
CMD apt update && apt install -y paramiko
RUN python mock_F5.py

