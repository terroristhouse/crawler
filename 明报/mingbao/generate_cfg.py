data = '''
[settings]
default = mingbao.settings
[deploy]
# url = http://localhost:6800/
project = mingbao
'''

with open('scrapy.cfg', 'w') as f:
    f.write(data)