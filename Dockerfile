FROM python:3.8.12-alpine3.13
LABEL maintainer="Hypothes.is Project and contributors"

# Install nginx & supervisor
RUN apk add --no-cache nginx gettext supervisor

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Ensure nginx state and log directories writeable by unprivileged user.
RUN chown -R hypothesis:hypothesis /etc/nginx/conf.d /var/log/nginx /var/lib/nginx

# Copy minimal data to allow installation of python dependencies.
COPY requirements/requirements.txt ./

# Install build deps, build, and then clean up.
RUN apk add --no-cache --virtual build-deps \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps

COPY ./conf/supervisord.conf ./conf/supervisord.conf
COPY ./conf/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./conf/nginx/includes /etc/nginx/includes
COPY ./conf/nginx/envsubst.conf.template /var/lib/hypothesis/nginx_envsubst.conf.template
COPY . .

USER hypothesis

CMD /usr/bin/envsubst '$${NGINX_SECURE_LINK_SECRET}' < /var/lib/hypothesis/nginx_envsubst.conf.template > /var/lib/hypothesis/nginx_envsubst.conf && /usr/bin/supervisord -c /var/lib/hypothesis/conf/supervisord.conf
