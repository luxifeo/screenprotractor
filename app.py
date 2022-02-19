import math
import sys
from loguru import logger
import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt

def getAngle(vector1: tuple, vector2: tuple):
    length1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
    length2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)
    if length1 == 0 or length2 == 0:
        raise ValueError('Cannot calculate the angle created by zero length vector')

    cos = (vector1[0] * vector2[0] + vector1[1] * vector2[1]) / (length1 * length2)
    angle = math.acos(cos) / math.pi * 180
    # angle range: 0 -> 180
    # logger.info(f'Cos {cos}, Angle {angle}')
    return angle

class Canvas(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.pointO = QPointF(200, 200)
        self.pointA = QPointF(100, 100)
        self.pointB = QPointF(300, 300)
        self.points = [self.pointO, self.pointA, self.pointB]
        canvas = QPixmap(self.size())
        canvas.fill(QColor(255, 255, 255, 255))
        self.setPixmap(canvas)

        self.closestPoint = None
        self.isMoving = False

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        # print(ev.x(), ev.y())
        x = ev.x()
        y = ev.y()

        
        if not self.isMoving:

            minDist = math.inf
            for point in self.points:
                dist = math.sqrt((point.x() - x) ** 2 + (point.y() - y) ** 2)
                if dist < minDist:
                    minDist = dist
                    self.closestPoint = point
            if minDist < 10:
                # print('Mouse is close to point', self.closestPoint)
                pass
            else:
                self.closestPoint = None

        else:
            self.closestPoint.setX(x)
            self.closestPoint.setY(y)
            self.repaint()

        return super().mouseMoveEvent(ev)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if self.closestPoint is not None and ev.button() == Qt.LeftButton:
            self.isMoving = True
        return super().mousePressEvent(ev)

    def contextMenuEvent(self, ev: QContextMenuEvent) -> None:
        contextMenu = QMenu(self)
        quitAction = contextMenu.addAction('Quit')

        action = contextMenu.exec_(self.mapToGlobal(ev.pos()))
        if action == quitAction:
            self.close()

        return super().contextMenuEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        if self.isMoving:
            self.isMoving = False
        return super().mouseReleaseEvent(ev)

    def paintEvent(self, a0: QPaintEvent) -> None:
        self.pixmap().fill(QColor(255, 255, 255, 100))
        painter = QPainter(self.pixmap())
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawLine(self.pointO, self.pointA)
        painter.drawLine(self.pointO, self.pointB)
        
        width = height = 40
        factor = 16

        startAngle = factor * 200 # angle with Ox
        angle = factor * -40

        vectorOA = (self.pointA.x() - self.pointO.x(), self.pointO.y() - self.pointA.y())
        vectorOB = (self.pointB.x() - self.pointO.x(), self.pointO.y() - self.pointB.y())
        try:
            angleAOx = getAngle(vectorOA, (1, 0))
            angleBOx = getAngle(vectorOB, (1, 0))
        except ValueError:
            angleAOx = 0
            angleBOx = 0

        if vectorOA[1] <= 0 and angleAOx != 0:
            angleAOx = 360 - angleAOx
        if vectorOB[1] <= 0 and angleBOx != 0:
            angleBOx = 360 - angleBOx

        angleAOB = angleBOx - angleAOx
        if angleAOB < -180:
            startAngle = angleAOx
            angle = 360 + angleAOB
        elif -180 <= angleAOB < 0:
            startAngle = angleBOx
            angle = -angleAOB
        elif 0 <= angleAOB < 180:
            startAngle = angleAOx
            angle = angleAOB
        elif 180 <= angleAOB:
            startAngle = angleBOx
            angle = 360 - angleAOB


        logger.info(f'{angleAOx}, {angleBOx}, {angleAOB}, {startAngle}, {angle}')

        startAngle = int(startAngle * factor)
        angle = int(angle * factor)
        # print(angleAOx, angleBOx)
        ### To draw arc, we need AOx and BOx angle
        ### arc is drawn clockwise
        painter.drawArc(int(self.pointO.x() - width // 2), int(self.pointO.y() - height // 2), width, height, startAngle, angle)
        
        penWidth = 5
        circleX = circleY = 3

        greenPen = QPen(Qt.green, penWidth)
        redPen = QPen(Qt.red, penWidth)
        bluePen = QPen(Qt.blue, penWidth)

        greenBrush = QBrush(Qt.green, Qt.SolidPattern)
        redBrush = QBrush(Qt.red, Qt.SolidPattern)
        blueBrush = QBrush(Qt.blue, Qt.SolidPattern)

        # O is green
        painter.setPen(greenPen)
        painter.setBrush(greenBrush)
        painter.drawEllipse(self.pointO, circleX, circleY)
        # A is red
        painter.setPen(redPen)
        painter.setBrush(redBrush)
        painter.drawEllipse(self.pointA, circleX, circleY)
        # B is blue
        painter.setPen(bluePen)
        painter.setBrush(blueBrush)
        painter.drawEllipse(self.pointB, circleX, circleY)
        
        pen = QPen(Qt.black)
        painter.setPen(pen)

        text = f'Angle: {angle / factor:.1f}° - {angle / factor / 180 * math.pi:.4f} rad'
        textRect = painter.boundingRect(0, 0, 150, 30, 0, text)
        textW = textRect.width()
        textH = textRect.height()
        padding = 15
        painter.fillRect(0, 0, padding * 2 + textW, padding * 2 + textH, QColor(255, 255, 255, 255))
        painter.drawText(padding, padding + textH, text)
        painter.drawText(int(self.pointO.x() + penWidth), int(self.pointO.y() - penWidth), f'O ({self.pointO.x():.0f}, {self.pointO.y():.0f})')
        painter.drawText(int(self.pointA.x() + penWidth), int(self.pointA.y() - penWidth), f'A ({self.pointA.x():.0f}, {self.pointA.y():.0f})')
        painter.drawText(int(self.pointB.x() + penWidth), int(self.pointB.y() - penWidth), f'B ({self.pointB.x():.0f}, {self.pointB.y():.0f})')



        painter.end()
        return super().paintEvent(a0)

    def keyPressEvent(self, ev: QKeyEvent) -> None:
        if ev.key() == Qt.Key.Key_Q:
            self.close()

        return super().keyPressEvent(ev)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Canvas()
    window.setWindowIcon(QIcon('icon.png'))
    window.show()
    sys.exit(app.exec_())
