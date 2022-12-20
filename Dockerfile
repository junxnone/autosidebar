FROM python:3.10

RUN pip install pandas -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY update_sidebar.py update_sidebar.py
