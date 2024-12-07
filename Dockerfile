FROM public.ecr.aws/lambda/python:3.12

RUN pip3 install --upgrade pip
COPY app/lambda_function.py /var/task/

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools
RUN pip3 install python-lambda-local pymongo jq aws-lambda-powertools
CMD [ "lambda_function.handler" ]