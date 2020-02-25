data = '''
[settings]
default = images.settings
[deploy]
# url = http://localhost:6800/
project = images
'''

with open('scrapy.cfg', 'w') as f:
    f.write(data)