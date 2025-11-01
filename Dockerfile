# Stage 1: Build frontend assets
FROM node:25.1.0-alpine as frontend-build

ENV NODE_ENV production
RUN mkdir -p /tmp/frontend-build
COPY .babelrc rollup.config.js gulpfile.js package.json .yarnrc.yml yarn.lock /tmp/frontend-build/
COPY .yarn /tmp/frontend-build/.yarn
COPY via/static /tmp/frontend-build/via/static

WORKDIR /tmp/frontend-build
RUN yarn install --immutable
RUN yarn build

# Stage 2: Build the rest of the app using build output from Stage 1.

# Unlike most Hypothesis projects this Docker image is based on Debian,
# so it can use glibc's DNS resolver which supports TCP retries. It can be
# reverted back to Alpine when Musl v1.2.4 is released.
#
# See https://github.com/hypothesis/product-backlog/issues/1409
FROM python:3.11.13-slim-bullseye
LABEL maintainer="Hypothes.is Project and contributors"

RUN apt-get update && apt-get install --yes nginx nginx-extras gettext-base git supervisor libpq-dev \
  && apt-get clean

# Create the hypothesis user, group, home directory and package directory.
RUN groupadd --system hypothesis && useradd --system -g hypothesis --home /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Ensure nginx state and log directories writeable by unprivileged user.
RUN chown -R hypothesis:hypothesis /etc/nginx/conf.d /var/log/nginx /var/lib/nginx /var/lib/hypothesis

# Copy minimal data to allow installation of python dependencies.
COPY requirements/prod.txt ./

# Install build deps, build, and then clean up.
RUN apt-get install --yes gcc \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r prod.txt \
  && apt-get remove --yes gcc \
  && apt-get autoremove --yes

# Copy frontend assets.
COPY --from=frontend-build /tmp/frontend-build/build build

COPY ./conf/supervisord.conf ./conf/supervisord.conf
COPY ./conf/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./conf/nginx/includes /etc/nginx/includes
COPY ./conf/nginx/envsubst.conf.template /var/lib/hypothesis/nginx_envsubst.conf.template
COPY . .

ENV PYTHONPATH /var/lib/hypothesis:$PYTHONPATH

USER hypothesis

CMD /usr/bin/envsubst '$${NGINX_SECURE_LINK_SECRET}' < /var/lib/hypothesis/nginx_envsubst.conf.template > /var/lib/hypothesis/nginx_envsubst.conf && /usr/bin/supervisord -c /var/lib/hypothesis/conf/supervisord.conf
