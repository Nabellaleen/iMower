# -*- mode: ruby -*-
# vi: set ft=ruby :

ipythonNotebookPort = 9898

$initScript = <<SCRIPT
sudo apt-get update

#Apache Server
sudo apt-get install -y apache2

#iMower Play Script
echo -e "#!/bin/sh\ncd ~/iMower/the-mower-world\npython game.py" >> /home/vagrant/Desktop/play-iMower.sh
sudo chmod +x /home/vagrant/Desktop/play-iMower.sh

#Setup the Mower Environment
sudo apt-get install -y vim git python-pip ipython ipython-notebook python-pygame
git clone https://github.com/tounnas/iMower.git
mv iMower/first-ai-planning-agent-dev /vagrant
sudo rm /var/www/html/* 
mv iMower/presentations/im-planning /var/www/html/

SCRIPT

Vagrant.configure(2) do |config|
  config.vm.define "iMower" do |master|
    master.vm.box = "box-cutter/ubuntu1404-desktop"
    config.vm.network "forwarded_port", host: 4567, guest: 80
    master.vm.network "forwarded_port", host: ipythonNotebookPort, guest: 8888
    master.vm.hostname = "iMower"
    master.vm.provision "shell", inline: $initScript  
    master.vm.provider :virtualbox do |v|
      v.name = master.vm.hostname.to_s
      v.gui = true
    end
  end
end