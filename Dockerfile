#
# Stand-alone tesseract-ocr web service in python.
#
# Version: 0.0.4
# Developed by Mark Peng (markpeng.ntu at gmail)
# Developed by Richard Leigh (rich.leigh at gmail)
#

FROM ubuntu:22.04

LABEL maintainer=richleigh

RUN apt update
RUN apt upgrade -y
RUN apt-get install -y \
  autoconf \
  automake \
  autotools-dev \
  build-essential \
  checkinstall \
  libjpeg-dev \
  libpng-dev \
  libtiff-dev \
  libtool \
  pkg-config \
  python3 \
  python3-pil \
  python3-tornado \
  wget \
  zlib1g-dev
RUN update-ca-certificates --fresh

RUN mkdir ~/temp
WORKDIR /root/temp/
RUN wget https://github.com/DanBloomberg/leptonica/releases/download/1.83.1/leptonica-1.83.1.tar.gz
RUN tar xvf leptonica-1.83.1.tar.gz
WORKDIR /root/temp/leptonica-1.83.1
RUN ./configure
RUN make
RUN checkinstall
RUN ldconfig

WORKDIR /root/temp/
RUN wget https://github.com/tesseract-ocr/tesseract/archive/refs/tags/5.3.1.tar.gz
RUN tar xvf 5.3.1.tar.gz
WORKDIR /root/temp/tesseract-5.3.1
RUN ./autogen.sh
RUN mkdir ~/local
RUN ./configure --prefix=$HOME/local/
RUN make
RUN make install

WORKDIR /root/local/share/tessdata
RUN wget https://github.com/tesseract-ocr/tessdata_best/raw/main/eng.traineddata
RUN wget https://github.com/tesseract-ocr/tessdata_best/raw/main/chi_tra.traineddata
RUN wget https://github.com/tesseract-ocr/tessdata_best/raw/main/hin.traineddata
RUN wget https://github.com/tesseract-ocr/tessdata_best/raw/main/spa.traineddata
RUN wget https://github.com/tesseract-ocr/tessdata_best/raw/main/fra.traineddata
RUN wget https://github.com/tesseract-ocr/tessdata_best/raw/main/ara.traineddata

RUN mkdir -p /opt/ocr/static

COPY tesseractcapi.py /opt/ocr/tesseractcapi.py
COPY tesseractserver.py /opt/ocr/tesseractserver.py

RUN chmod 755 /opt/ocr/*.py

EXPOSE 1688

WORKDIR /opt/ocr
CMD ["python3", "/opt/ocr/tesseractserver.py", "-p", "1688", "-b", "/root/local/lib", "-d", "/root/local/share/tessdata"]