resource "random_string" "do_ssh" {
  length = 16
  special = false
}
resource "tls_private_key" "do_pvt_key" {
  algorithm = "RSA"
  rsa_bits = 4096
}
resource "digitalocean_ssh_key" "ssh_key" {
  name = random_string.do_ssh.result
  public_key = tls_private_key.do_pvt_key.public_key_openssh
}
resource "digitalocean_droplet" "redcisco-remote-fs" {
  depends_on = [tls_private_key.do_pvt_key]
  image = "ubuntu-18-04-x64"
  name = "redcisco-remote-fs"
  region = "nyc1"
  size = "s-1vcpu-1gb"
  private_networking = false
  ssh_keys = [
    digitalocean_ssh_key.ssh_key.id]

  connection {
    host = self.ipv4_address
    user = "root"
    type = "ssh"
    private_key = tls_private_key.do_pvt_key.private_key_pem
    timeout = "5m"
  }

  provisioner "file" {
    source = "src/key/terraform_rsa.pub"
    destination = "/tmp/key.pub"
  }

  provisioner "remote-exec" {
    inline = [
      "export DEBIAN_FRONTEND=noninteractive",
      "export PATH=$PATH:/usr/bin",
      #"yes | apt-get update -qy && yes | apt-get upgrade -qy",
      "apt-get install nginx -qy",
      "add-apt-repository universe",
      "apt update -qy",
      "cat /tmp/key.pub >> /root/.ssh/authorized_keys",
      "touch /tmp/task.complete",
    ]
  }
}

resource "null_resource" "nginx_configuration" {

  depends_on = [digitalocean_droplet.redcisco-remote-fs, random_string.do_ssh]

  connection {
    host = digitalocean_droplet.redcisco-remote-fs.ipv4_address
    user = "root"
    type = "ssh"
    private_key = tls_private_key.do_pvt_key.private_key_pem
    timeout = "5m"
  }

  provisioner "file" {
    source = "src/file/nmap.tcl"
    destination = "/tmp/nmap.tcl"
  }

  provisioner "file" {
    source = "src/file/proxy.tcl"
    destination = "/tmp/proxy.tcl"
  }

  provisioner "remote-exec" {
    inline = [
      "systemctl stop nginx",
      "rm -rf /var/www/html/*",
      "mv /tmp/nmap.tcl /var/www/html/nmap.tcl",
      "mv /tmp/proxy.tcl /var/www/html/proxy.tcl",
      "chmod 644 /var/www/html/*",
      "chown www-data:www-data /var/www/html -R",
      "sed -i -e '/^[ \t]*#/d' /etc/nginx/sites-enabled/default",
      "sed -i 's/try_files/autoindex on;\n\t\ttry_files/g' /etc/nginx/sites-enabled/default",
      "systemctl enable nginx && systemctl start nginx"
    ]
  }
}
