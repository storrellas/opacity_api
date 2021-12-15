
git pull origin master
cd docker
#sudo docker-compose build --no-cache 
docker-compose build
docker-compose down
docker-compose up -d
