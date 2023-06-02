FROM lcw2/arm32v7tensorflow2.4:v1.1
WORKDIR /app
ENV READTHEDOCS=True

RUN pip3 install docopt  && \
    pip3 install tornado==6.1 && \
    pip3 install pyinotify  && \
    pip3 install pyserial && \
    pip3 install picamera && \
    pip3 install Pillow && \
    pip3 install pandas && \
    pip3 install requests && \
    pip3 install minio

RUN rm -r ~/.cache/pip

RUN ln -s /opt/vc/lib/libbcm_host.so /usr/lib/libbcm_host.so && \
    ln -s /opt/vc/lib/libvcos.so.0 /usr/lib/libvcos.so.0 &&  \
    ln -s /opt/vc/lib/libvchiq_arm.so.0 /usr/lib/libvchiq_arm.so.0 && \
    ln -s /opt/vc/lib/libmmal_vc_client.so.0 /usr/lib/libmmal_vc_client.so.0 && \
    ln -s /opt/vc/lib/libmmal.so.0 /usr/lib/libmmal.so.0 && \
    ln -s /opt/vc/lib/libmmal.so /usr/lib/libmmal.so && \
    ln -s /opt/vc/lib/libvcsm.so.0 /usr/lib/libvcsm.so.0 && \
    ln -s /opt/vc/lib/libmmal_core.so.0 /usr/lib/libmmal_core.so.0 && \
    ln -s /opt/vc/lib/libmmal_util.so.0 /usr/lib/libmmal_util.so.0 && \
    ln -s /opt/vc/lib/libvchiq_arm.so /usr/lib/opt/vc/lib/libvchiq_arm.so && \
    ln -s /opt/vc/lib/libopenmaxil.so /usr/lib/libopenmaxil.so && \
	ln -s /opt/vc/lib/libvcos.so /usr/lib/libvcos.so &&  \
	ln -s /opt/vc/lib/libvchiq_arm.so /usr/lib/libvchiq_arm.so && \
	ln -s /opt/vc/lib/libbrcmGLESv2.so /usr/lib/libbrcmGLESv2.so && \
	ln -s /opt/vc/lib/libbrcmEGL.so /usr/lib/libbrcmEGL.so && \
	ln -s /opt/vc/lib/libGLESv2.so /usr/lib/libGLESv2.so && \
	ln -s /opt/vc/lib/libEGL.so /usr/lib/libEGL.so && \
	ln -s /opt/vc/lib/libkhrn_client.a /usr/lib/libkhrn_client.a && \
	ln -s /opt/vc/lib/libmmal_components.so /usr/lib/libmmal_components.so && \
	ln -s /opt/vc/lib/libmmal_vc_client.so /usr/lib/libmmal_vc_client.so && \
	ln -s /opt/vc/lib/libvcsm.so /usr/lib/libvcsm.so && \
	ln -s /opt/vc/lib/libmmal_core.so /usr/lib/libmmal_core.so && \
	ln -s /opt/vc/lib/libmmal_util.so /usr/lib/libmmal_util.so && \
	ln -s /opt/vc/lib/libcontainers.so /usr/lib/libcontainers.so



COPY . /app
CMD ["python", "/app/main.py"]