ARG ubuntu_version
FROM ubuntu:${ubuntu_version}

ARG ubuntu_version
RUN apt-get update
RUN apt-get -qq install python3-gi python3-cairo python3-simplejson python3-requests
RUN if [ "${ubuntu_version}" = "18.04" ]; then apt-get -qq install python3-distutils; fi
RUN apt-get -qq install gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 gir1.2-osmgpsmap-1.0
RUN apt-get -qq install xvfb git

RUN git clone https://github.com/kismetwireless/kismet.git
RUN cd kismet/python_modules/KismetRest && python3 setup.py install

WORKDIR /code
ENV DISPLAY :99.0
CMD Xvfb $DISPLAY
