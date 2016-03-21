import subprocess
import re

f = open("list_site_web")
content = f.read()
f.close()

list_site_web = re.split("\n",content)

for x in range(0,len(list_site_web)):
	data = re.split(" ",list_site_web[x])
	if len(data) == 2:
		print data
		subprocess.call(["wget", "-m", "-nd", "-P", data[0], data[1]])
		subprocess.call(["unzip", "-jo", data[0]+"/*.zip", "-d", data[0]])
		subprocess.call(["find", "./"+data[0], "-type", "f", "!", "-name", "*.pdf", "-delete"])
		pass
	pass


## For each site do this :

# wget -m -nd -P site http://www.hpceurope.com/
# unzip -jo 'site/*.zip' -d site/
# find ./site -type f ! -name '*.pdf' -delete
