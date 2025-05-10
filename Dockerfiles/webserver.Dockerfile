FROM nginx:alpine

# Remove default Nginx config to prevent conflicts.
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy our custom Nginx configuration (for reverse proxy) into the image.
COPY ./configs/webserver/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80