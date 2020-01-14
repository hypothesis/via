FROM python:3.8.1-alpine3.10
LABEL maintainer="Hypothes.is Project and contributors"

# Install nginx & supervisor
RUN apk add --no-cache nginx gettext supervisor

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Ensure nginx state and log directories writeable by unprivileged user.
RUN chown -R hypothesis:hypothesis /etc/nginx/conf.d /var/log/nginx /var/lib/nginx /var/tmp/nginx

# Copy minimal data to allow installation of python dependencies.
COPY ./requirements.txt ./

# Install build deps, build, and then clean up.
RUN apk add --no-cache --virtual build-deps \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps

COPY ./conf/supervisord.conf ./conf/supervisord.conf

COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./nginx/nginx_envsubst.conf.template /var/lib/hypothesis/nginx_envsubst.conf.template
COPY . .

USER hypothesis

CMD /usr/bin/envsubst '$${ACCESS_CONTROL_ALLOW_ORIGIN}' < /var/lib/hypothesis/nginx_envsubst.conf.template > /var/lib/hypothesis/nginx_envsubst.conf && /usr/bin/supervisord -c /var/lib/hypothesis/conf/supervisord.conf
