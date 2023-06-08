FROM continuumio/miniconda3
WORKDIR /home

COPY environment.yml ./
RUN conda env create -f environment.yml

RUN apt-get -y update && apt-get install make
RUN apt-get -y install git g++ autoconf-archive make libtool
RUN apt-get -y install python-setuptools python-dev
RUN apt-get -y install gfortran
RUN mkdir g2p
WORKDIR g2p
RUN wget http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.7.2.tar.gz
RUN tar -xvzf openfst-1.7.2.tar.gz
WORKDIR openfst-1.7.2
RUN ./configure --enable-static --enable-shared --enable-far --enable-ngram-fsts
RUN make -j 
RUN make install
RUN echo 'export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib:/usr/local/lib/fst' >> ~/.bashrc
RUN . ~/.bashrc
WORKDIR ..
RUN git clone https://github.com/AdolfVonKleist/Phonetisaurus.git
WORKDIR Phonetisaurus
RUN pip3 install pybindgen
RUN PYTHON=python3 ./configure --enable-python
RUN PYTHON=python3 ./configure --with-openfst-includes=${OFST_PATH}/openfst-1.7.2/include --with-openfst-libs=${OFST_PATH}/openfst-1.7.2/lib --enable-python
RUN make
RUN make install
WORKDIR python
RUN cp ../.libs/Phonetisaurus.so .
RUN python3 setup.py install
WORKDIR ../.
RUN git clone https://github.com/mitlm/mitlm.git
WORKDIR mitlm/
RUN ./autogen.sh
RUN make
RUN make install
WORKDIR ..
RUN mkdir example
WORKDIR example
COPY example .
WORKDIR /home
COPY main.py .