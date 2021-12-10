
git pull origin master
cd docker
#sudo docker-compose build --no-cache 
sudo docker-compose build
sudo docker-compose down
sudo docker-compose up -d
