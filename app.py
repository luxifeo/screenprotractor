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

        ### Point position are relative to window screen

        self.pointO = QPointF(200, 200)
        self.pointA = QPointF(100, 100)
        self.pointB = QPointF(300, 300)
        self.points = [self.pointO, self.pointA, self.pointB]
        canvas = QPixmap(self.size())
        self.setPixmap(canvas)

        self.closestPoint = None
        self.isMoving = False

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screenX, screenY, screenW, screenH = self.getScreenGeometry()
        # logger.info(f'{screenX} {screenY} {screenW} {screenH}')
        self.setGeometry(screenX, screenY, screenW, screenH)

    def getScreenGeometry(self):
        maxX = maxY = -1
        screenSize = QDesktopWidget().screenGeometry()
        minX = screenSize.width()
        minY = screenSize.height()

        for point in self.points:
            pointX = point.x()
            pointY = point.y()
            if pointX > maxX:
                maxX = pointX
            if pointY > maxY:
                maxY = pointY
            if pointX < minX:
                minX = pointX
            if pointY < minY:
                minY = pointY

        padding = 60

        minX = max(0, minX - padding)
        minY = max(0, minY - padding)
        maxX = min(screenSize.width() - 1, maxX + padding)
        maxY = min(screenSize.height() - 1, maxY + padding)

        logger.debug(f'{minX} {minY} {maxX} {maxY}')

        screenX = int(minX)
        screenY = int(minY)
        screenW = int(maxX - minX)
        screenH = int(maxY - minY)

        return screenX, screenY, screenW, screenH

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        # print(ev.x(), ev.y())
        x = ev.x()
        y = ev.y()

        
        if not self.isMoving:

            minDist = math.inf
            for point in self.points:
                pointX = point.x() - self.x()
                pointY = point.y() - self.y()
                dist = math.sqrt((pointX - x) ** 2 + (pointY - y) ** 2)
                if dist < minDist:
                    minDist = dist
                    self.closestPoint = point
            if minDist < 10:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.closestPoint = None
                self.setCursor(Qt.ArrowCursor)

        else:
            ### If point is near window border, expand it
            self.closestPoint.setX(x + self.x())
            self.closestPoint.setY(y + self.y())

            screenX, screenY, screenW, screenH = self.getScreenGeometry()
            logger.info(f'{screenX} {screenY} {screenW} {screenH} {self.x()}')
            newRect = QRect(screenX, screenY, screenW, screenH)
            if newRect == self.geometry():
                self.repaint()
            else:
                self.setGeometry(newRect)

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

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.setPixmap(QPixmap(self.size()))
        return super().resizeEvent(a0)

    def paintEvent(self, a0: QPaintEvent) -> None:
        self.pixmap().fill(QColor(255, 255, 255, 100))
        painter = QPainter(self.pixmap())
        painter.setRenderHint(QPainter.Antialiasing, True)

        screenX = self.x()
        screenY = self.y()
        relativePointO = QPointF(self.pointO.x() - screenX, self.pointO.y() - screenY)
        relativePointA = QPointF(self.pointA.x() - screenX, self.pointA.y() - screenY)
        relativePointB = QPointF(self.pointB.x() - screenX, self.pointB.y() - screenY)

        painter.drawLine(relativePointO, relativePointA)
        painter.drawLine(relativePointO, relativePointB)
        
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


        # logger.info(f'{angleAOx}, {angleBOx}, {angleAOB}, {startAngle}, {angle}')

        startAngle = int(startAngle * factor)
        angle = int(angle * factor)
        # print(angleAOx, angleBOx)
        ### To draw arc, we need AOx and BOx angle
        ### arc is drawn clockwise
        painter.drawArc(int(relativePointO.x() - width // 2), int(relativePointO.y() - height // 2), width, height, startAngle, angle)
        
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
        painter.drawEllipse(relativePointO, circleX, circleY)
        # A is red
        painter.setPen(redPen)
        painter.setBrush(redBrush)
        painter.drawEllipse(relativePointA, circleX, circleY)
        # B is blue
        painter.setPen(bluePen)
        painter.setBrush(blueBrush)
        painter.drawEllipse(relativePointB, circleX, circleY)
        
        pen = QPen(Qt.black)
        painter.setPen(pen)

        text = f'Angle: {angle / factor:.1f}° - {angle / factor / 180 * math.pi:.4f} rad'
        textRect = painter.boundingRect(0, 0, 150, 30, 0, text)
        textW = textRect.width()
        textH = textRect.height()
        padding = 15
        painter.fillRect(0, 0, padding * 2 + textW, padding * 2 + textH, QColor(255, 255, 255, 255))
        painter.drawText(padding, padding + textH, text)
        painter.drawText(int(relativePointO.x() + penWidth), int(relativePointO.y() - penWidth), f'O ({self.pointO.x():.0f}, {self.pointO.y():.0f})')
        painter.drawText(int(relativePointA.x() + penWidth), int(relativePointA.y() - penWidth), f'A ({self.pointA.x():.0f}, {self.pointA.y():.0f})')
        painter.drawText(int(relativePointB.x() + penWidth), int(relativePointB.y() - penWidth), f'B ({self.pointB.x():.0f}, {self.pointB.y():.0f})')

        painter.end()
        return super().paintEvent(a0)

    def keyPressEvent(self, ev: QKeyEvent) -> None:
        if ev.key() == Qt.Key.Key_Q:
            self.close()

        return super().keyPressEvent(ev)

if __name__ == '__main__':
    if not os.environ.get('DEBUG'):
        logger.remove(0)
        logger.add(sys.stderr, level="CRITICAL")
    app = QApplication(sys.argv)
    window = Canvas()
    window.setWindowIcon(QIcon('icon.png'))
    window.show()
    sys.exit(app.exec_())
