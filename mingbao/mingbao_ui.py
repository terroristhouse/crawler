
import sys,os
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']

from PyQt5.QtWidgets import QApplication,QLabel,QPushButton,QGridLayout,QCalendarWidget,QWidget,QLineEdit
from PyQt5.QtGui import QIcon

class Example(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300,300,600,300)
        self.setWindowTitle('明报-每日明报')
        self.setWindowIcon(QIcon('ming_icon.jpg'))

        grid = QGridLayout()
        grid.setSpacing(10)
        self.setLayout(grid)

        self.aoi_lbl = QLabel(self)
        self.aoi_lbl.setText('爬虫状态')
        grid.addWidget(self.aoi_lbl,1,1,1,1)

        self.aoi_lbl2 = QLabel(self)
        self.aoi_lbl2.setText('等待中...')
        grid.addWidget(self.aoi_lbl2, 1, 2,1,2)

        # self.aoi_btn = QPushButton(self)
        # self.aoi_btn.setText('配置参数')
        # grid.addWidget(self.aoi_btn,1,4,1,2)

        self.kong_lbl = QLabel(self)
        grid.addWidget(self.kong_lbl,2,1)

        self.hat_btn = QPushButton(self)
        self.hat_btn.setText('手动触发')
        grid.addWidget(self.hat_btn, 3, 1, 1, 1)

        self.hat_lbl = QLabel(self)
        self.hat_lbl.setText('选择爬取日期点击确定按钮')
        grid.addWidget(self.hat_lbl, 3, 2, 1, 2)

        # self.proxy_lbl = QLabel(self)
        # self.proxy_lbl.setText('代理')
        # grid.addWidget(self.proxy_lbl, 3, 4, 1, 1)
        #
        # self.proxy_lin = QLineEdit(self)
        # self.proxy_lin.setText('192.168.0.70')
        # grid.addWidget(self.proxy_lin, 3, 5, 1, 2)


        self.cal = QCalendarWidget(self)
        grid.addWidget(self.cal,4,1,1,2)

        # self.sql_lbl = QLabel(self)
        # self.sql_lbl.setText('数据库')
        # grid.addWidget(self.sql_lbl, 4, 4, 4, 1)
        #
        # self.host_lbl = QLabel(self)
        # self.host_lbl.setText('host')
        # grid.addWidget(self.host_lbl, 4, 5, 1, 1)
        #
        # self.host_lin = QLineEdit(self)
        # self.host_lin.setText('127.0.0.1')
        # grid.addWidget(self.host_lin, 4, 6, 1, 2)

        self.hat_btn2 = QPushButton(self)
        self.hat_btn2.setText('确定')
        grid.addWidget(self.hat_btn2, 5, 1, 1, 1)



        self.show()



# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = Example()
#     exit(app.exec_())











































