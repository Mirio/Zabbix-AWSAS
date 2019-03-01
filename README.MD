## What is this?
This repo is created for share the AWS lambda functions to manage the scale-in/scale-out of the AWS EC2 instances on Zabbix.

## Getting started
### Create the API user on Zabbix
* Login As Admin on Zabbix
* Go to Administration -> Users
* Create User and select
  * Groups: "Zabbix administrators"
  * Permissions -> User type: Zabbix Super Admin

### Create IAM Policy
Create IAM policy as below
Name: Zabbix_AWSAS
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceStatus"
            ],
            "Resource": "*"
        }
    ]
}
```

### Create lambda ZIP package
```
git clone git@github.com:Mirio/Zabbix-AWSAS.git
cd Zabbix-AWSAS
virtualenv -v -p python3 VENV
. ./VENV/bin/activate
pip install -t lib pyzabbix boto3
zip lambda.zip -r lib README.MD LICENSE zaas.py
```


### Create AddHost Lambda Functions
Name: Zabbix_AWSAS_HostReg
Runtime: Python 3.7
Role: Create a new role from one or more templates.
Role name: Zabbix_AWSAS_HostReg
--> Create Function

Timeout: 2 min
Handler: `zaas.lambda_addhandler`
Upload the "lambda.zip" previusly created
Fill our Environment variables as below:

| Env Name | Description | Required |
| ---- | ---- | ---- |
| ZABHOST | Zabbix Url **without trailing slash** | YES |
| ZABUSER | Zabbix username | YES |
| ZABPWD | Zabbix Password | YES |
| ZABGROUPID | Zabbix Host Group ID (comma separated) | YES |
| ZABTEMPLATE | Zabbix Template ID (comma separated) | NO |
| DEBUG | Debug Script | NO |

### Create Delete Host Lambda Functions
Name: Zabbix_AWSAS_HostDel
Runtime: Python 3.7
Role: Create a new role from one or more templates.
Role name: Zabbix_AWSAS_HostDel
--> Create Function

Timeout: 2 min
Handler: `zaas.lambda_delhandler`
Upload the "lambda.zip" previusly created
Fill our Environment variables as below:

| Env Name | Description | Required |
| ---- | ---- | ---- |
| ZABHOST | Zabbix Url **without trailing slash** | YES |
| ZABUSER | Zabbix username | YES |
| ZABPWD | Zabbix Password | YES |
| DEBUG | Debug Script | NO |

### Create Cloudwatch Events for AddHost
Create new rule as below
Service name: Auto Scaling
Event Type: Instance Launch and Terminate
Specific instance event(s): Instance-launch Lifecycle
Specific group name(s): <Add your Target Group>
Targets: Lambda Function: Zabbix_AWSAS_HostReg
--> Configure details

Name: Zabbix_AWSAS_HostReg_GW
Description: <foo>
--> Create rule

### Create Cloudwatch Events for DelHost
Create new rule as below
Service name: Auto Scaling
Event Type: Instance Launch and Terminate
Specific instance event(s): Instance-terminate Lifecycle
Specific group name(s): <Add your Target Group>
Targets: Lambda Function: Zabbix_AWSAS_HostDel
--> Configure details

Name: Zabbix_AWSAS_HostDel_GW
Description: <foo>
--> Create rule

### Add IAM policy to the Lambda functions
IAM -> Roles
* Find Zabbix_AWSAS_HostReg and attach "Zabbix_AWSAS" Policy
* Find Zabbix_AWSAS_HostDel and attach "Zabbix_AWSAS" Policy 
