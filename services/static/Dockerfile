FROM jitesoft/lighttpd:latest as base

WORKDIR /var/www/html/static

# Copy the app static files into the container.
COPY src/app/static/. .

# Fix owner
RUN chown -R www-data:www-data .

# Expose the port that the application listens on.
EXPOSE 80

HEALTHCHECK --interval=1m --timeout=5s --start-period=30s CMD healthcheck
ENTRYPOINT ["entrypoint"]
CMD ["-D"]
