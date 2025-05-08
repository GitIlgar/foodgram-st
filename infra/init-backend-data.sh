docker compose up -d --build
docker compose exec backend python manage.py collectstatic
sleep 15s

docker compose exec backend python manage.py migrate
sleep 5s

docker compose exec backend python manage.py loaddata data/domain.json
docker compose exec backend python manage.py createsuperuser