apt-get update -y
apt-get install -y nginx supervisor gcc g++ make curl unzip sudo python3-pip git
apt-get install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa
apt-get update -y && apt install -y python3.7 libpython3.7 python3.7-dev

update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.5 1
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2
python --version
python3 --version

# update pip
pip3 install pip --upgrade
pip3 install -r /deploy/app/requirements.txt
pip install torch==1.7.1+cu110 -f https://download.pytorch.org/whl/torch_stable.html

# setup GRIDD
pip3 install -r /deploy/app/GRIDD/requirements.txt
git clone https://github.com/jdfinch/structpy /deploy/app/structpy_outer
mv /deploy/app/structpy_outer/structpy /deploy/app/
rm -r /deploy/app/structpy_outer