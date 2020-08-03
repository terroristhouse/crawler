data = '''
[settings]
default = HK.settings
[deploy]
# url = http://localhost:6800/
project = HK
'''

with open('scrapy.cfg', 'w') as f:
    f.write(data)