FROM arm32v7/python:3.6
COPY parts /app
WORKDIR /app
ENV READTHEDOCS=True
RUN pip install -r requirements.txt
RUN ln -s /opt/vc/lib/libopenmaxil.so /usr/lib/libopenmaxil.so && \
	ln -s /opt/vc/lib/libbcm_host.so /usr/lib/libbcm_host.so && \
	ln -s /opt/vc/lib/libvcos.so /usr/lib/libvcos.so &&  \
	ln -s /opt/vc/lib/libvchiq_arm.so /usr/lib/libvchiq_arm.so && \
	ln -s /opt/vc/lib/libbrcmGLESv2.so /usr/lib/libbrcmGLESv2.so && \
	ln -s /opt/vc/lib/libbrcmEGL.so /usr/lib/libbrcmEGL.so && \
	ln -s /opt/vc/lib/libGLESv2.so /usr/lib/libGLESv2.so && \
	ln -s /opt/vc/lib/libEGL.so /usr/lib/libEGL.so && \
	ln -s /opt/vc/lib/libkhrn_client.a /usr/lib/libkhrn_client.a && \
	ln -s /opt/vc/lib/libmmal_components.so /usr/lib/libmmal_components.so && \
	ln -s /opt/vc/lib/libmmal_vc_client.so /usr/lib/libmmal_vc_client.so && \
	ln -s /opt/vc/lib/libmmal.so /usr/lib/libmmal.so && \
	ln -s /opt/vc/lib/libvcsm.so /usr/lib/libvcsm.so && \
	ln -s /opt/vc/lib/libmmal_core.so /usr/lib/libmmal_core.so && \
	ln -s /opt/vc/lib/libmmal_util.so /usr/lib/libmmal_util.so && \
	ln -s /opt/vc/lib/libcontainers.so /usr/lib/libcontainers.so
CMD ["python", "/app/main.py", "drive"]