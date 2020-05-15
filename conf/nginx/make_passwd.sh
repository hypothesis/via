#!/bin/sh

# This script will create the password file for authenticating the
# user accessing the status stub.

# sudo apt-get install apache2-utils

# See: https://httpd.apache.org/docs/2.4/programs/htpasswd.html
# Use -B to enable bcrypt for more secure passwords
htpasswd -c -B via/stats_passwd via3_stats
