# Source: https://github.com/Mirio/Zabbix-AWSAS
# License: GPL-3.0
import logging
import json
import os
import sys

# Fix lambda dep
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "./lib"))
from pyzabbix import ZabbixAPI
import boto3

## Setup logging
log = logging.getLogger()
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
for handler in log.handlers:
    handler.setFormatter(logging.Formatter(log_format))
if os.getenv("DEBUG") == "true":
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

class ZAAS:
    def __init__(self, zab_host, zab_user, zab_pwd):
        """
        Init class
        :param zab_host: Zabbix URL
        :param zab_user: Zabbix Username
        :param zab_pwd: Zabbix Pwd
        """
        self.zab_host = zab_host
        self.zab_user = zab_user
        self.zab_pwd = zab_pwd

    def login(self):
        self.client = ZabbixAPI(self.zab_host)
        self.client.login(self.zab_user, self.zab_pwd)
        self.botoclient = boto3.client('ec2')

    def addhost(self, name, ip, hostgroupid, templates, port=10050):
        """
        Add new EC2 host to zabbix
        :param name: Name used into hostname field
        :param ip: Public ip of the EC2 instance
        :param port: Zabbix agent port
        :param hostgroupid: Group Host ID to add
        :param templates: Template to link into instances host
        :return: None
        """
        params = {
            "host": name,
            "groups": hostgroupid,
            "interfaces": [
                {
                    "type": 1,
                    "main": 1,
                    "useip": 1,
                    "ip": ip,
                    "dns": "",
                    "port": 10050
                }
            ]
        }

        if templates:
            params["templates"] = templates
        log.info("Adding %s" % name)
        self.client.host.create(params)

    def get_ec2details(self, instanceid):
        """
        Get ec2 instance details
        :params instanceid: Instance EC2 ID
        :return: {"name": "<private ip without ec2 part>", "ip": "<public ip>"}
        """
        out = {}
        req = self.botoclient.describe_instances(
            InstanceIds=[instanceid])
        if req:
            name = req["Reservations"][0]["Instances"][0][
                        "PrivateDnsName"].split(".")[0]
            ip = req["Reservations"][0]["Instances"][0]["PublicIpAddress"]
            return {"name": name, "ip": ip}

    def gethostid(self, name):
        """
        Get HostID from Zabbix Server
        :params name: Name to check
        :return: HostID
        """
        for hit in self.client.host.get():
            if hit["host"] == name:
                return hit["hostid"]

    def delhost(self, name):
        """
        Delete the host from Zabbix server
        :params name: Host name to delete
        :return: None
        """
        log.info("Deleting %s" % name)
        hostid = self.gethostid(name)
        params = str(hostid)
        if hostid:
            self.client.host.delete(params)

## AddHandler
def lambda_addhandler(event, context):
    instanceid = event["detail"]["EC2InstanceId"]
    hostgroupid = []
    for hit in os.getenv("ZABGROUPID").split(","):
        hostgroupid.append({"groupid": hit})
    if os.getenv("ZABTEMPLATE"):
        templates = []
        for hit in os.getenv("ZABTEMPLATE").split(","):
            templates.append({"templateid": hit})
    else:
        templates = []
    obj = ZAAS(os.getenv("ZABHOST"), os.getenv("ZABUSER"), os.getenv("ZABPWD"))
    obj.login()
    ec2info = obj.get_ec2details(instanceid)
    if ec2info:
        obj.addhost(name=ec2info["name"], ip=ec2info["ip"],
                    port=10050, hostgroupid=hostgroupid, templates=templates)
        log.info("%s Added" % instanceid)
    else:
        log.error("EC2 Cannot detect")
    return "Done."

## DelHandler
def lambda_delhandler(event, context):
    instanceid = event["detail"]["EC2InstanceId"]
    obj = ZAAS(os.getenv("ZABHOST"), os.getenv("ZABUSER"), os.getenv("ZABPWD"))
    obj.login()
    ec2info = obj.get_ec2details(instanceid)
    if ec2info:
        obj.delhost(ec2info["name"])
        log.info("%s Deleted" % instanceid)
    else:
        log.error("EC2 Cannot detect")
    return "Done."
