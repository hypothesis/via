# Stage 1: Build frontend assets
FROM node:20.2.0-alpine as frontend-build

ENV NODE_ENV production
COPY .babelrc rollup.config.mjs gulpfile.mjs package.json tailwind.config.mjs yarn.lock ./
COPY via/static ./via/static

RUN yarn install --frozen-lockfile
RUN yarn build

# Stage 2: Build the rest of the app using build output from Stage 1.

# Unlike most Hypothesis projects this Docker image is based on Debian,
# so it can use glibc's DNS resolver which supports TCP retries. It can be
# reverted back to Alpine when Musl v1.2.4 is released.
#
# See https://github.com/hypothesis/product-backlog/issues/1409
FROM python:3.8.17-slim-bullseye
LABEL maintainer="Hypothes.is Project and contributors"

# Install nginx & supervisor
RUN apt-get update && apt-get install --yes nginx nginx-extras gettext-base supervisor \
  && apt-get clean

# Create the hypothesis user, group, home directory and package directory.
RUN groupadd --system hypothesis && useradd --system -g hypothesis --home /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Ensure nginx state and log directories writeable by unprivileged user.
RUN chown -R hypothesis:hypothesis /etc/nginx/conf.d /var/log/nginx /var/lib/nginx /var/lib/hypothesis

# Copy minimal data to allow installation of python dependencies.
COPY requirements/prod.txt ./

# Install build deps, build, and then clean up.
RUN pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r prod.txt

# Copy frontend assets.
COPY --from=frontend-build /build build

COPY ./conf/supervisord.conf ./conf/supervisord.conf
COPY ./conf/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./conf/nginx/includes /etc/nginx/includes
COPY ./conf/nginx/envsubst.conf.template /var/lib/hypothesis/nginx_envsubst.conf.template
COPY . .

USER hypothesis

CMD /usr/bin/envsubst '$${NGINX_SECURE_LINK_SECRET}' < /var/lib/hypothesis/nginx_envsubst.conf.template > /var/lib/hypothesis/nginx_envsubst.conf && /usr/bin/supervisord -c /var/lib/hypothesis/conf/supervisord.conf
