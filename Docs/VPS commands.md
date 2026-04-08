# docker-compose -f docker-compose.prod.yml exec web python manage.py shell -c "from django.conf import settings; print(settings.CSRF_USE_SESSIONS)"

docker-compose -f docker-compose.prod.yml restart web

docker-compose -f docker-compose.prod.yml restart web

docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput


git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
