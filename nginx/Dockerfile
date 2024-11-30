FROM nginx:latest

RUN groupadd -r -g 1000 tentron && useradd -r -g tentron -u 1000 tentron
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./sites-available /etc/nginx/sites-available
COPY ./error_page_template /var/www/error_page

RUN mkdir -p /etc/nginx/sites-enabled && ln -s /etc/nginx/sites-available/tentron.conf /etc/nginx/sites-enabled/ && rm /etc/nginx/conf.d/default.conf
