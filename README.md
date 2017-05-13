# graylog2-collector-zabbix
Zabbix template to monitor the state of Graylog's registered sidecar collectors.

It uses Zabbix Low Level Discovery (LLD) to identify the collectors through Graylog's API.

## Installation
### External Script
* Copy the .py and .conf in your Zabbix ExternalScript directory.
* Modify the values to reflect your environment in the .conf file

The password in the .conf file is using a simple base64 obfuscation. You can obtain your password's base64 value like:
```
$ python
>>> base64.b64encode("mypass")
'bXlwYXNz'
```

To verify:
```
>>> base64.b64decode("bXlwYXNz")
'mypass'
```

### Import the template

### Link the template
You can link it to the Zabbix server itself if you wish, or anywhere for that matter.
Lt the discovery rules a little time.

### Notes
Return codes taken from source code backends/registry.go, except for code 99, which indicates an inactive collector. Hopefully, the time to catch that before it dissapears.
