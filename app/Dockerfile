FROM python:3.10
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update && apt-get install -y netcat-traditional

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy enterpoint.sh
COPY enterpoint.sh .
RUN sed -i 's/\r$//g' enterpoint.sh
RUN chmod +x enterpoint.sh

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web

# create the base directory
RUN mkdir $HOME
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

# copy project
COPY .. .

# run entrypoint.sh
ENTRYPOINT ["./enterpoint.sh"]
