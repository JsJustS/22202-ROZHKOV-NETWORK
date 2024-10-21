from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from qtpy import uic
import snakes.snakes_pb2 as snakes


class GameWidget(QWidget):
    def __init__(self, client: QWidget, server_name: str, settings: snakes.GameConfig):
        super().__init__()
        self.ui = uic.loadUi('ui/game.ui', self)

        self.server_name = server_name
        self.settings = settings

        self.client = client

        self.leaveButton.clicked.connect(self.returnToClient)
        self.show()

    def returnToClient(self):
        self.client.playerNameLine.setEnabled(True)
        self.client.hostButton.setEnabled(True)
        self.client.avaliableGamesTable.setEnabled(True)
        self.client.show()
        self.close()

    def paintEvent(self, event):
        try:
            canvas = self.artWidget
            painter = QPainter(self)

            pen = QPen()
            pen.setColor(QColor('black'))
            pen.setWidth(10)
            painter.setPen(pen)
            painter.fillRect(canvas.x(), canvas.y(), canvas.width(), canvas.height(), QColor('black'))
            painter.end()
        except Exception as e:
            print(e)


class PenWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # super().__init__()
        self.setMaximumWidth(16777215)
        self.setMaximumHeight(16777215)

        self.field = []
        self.last = None

    def parseField(self):
        parsed = [(0, 0)]
        if len(self.field) < 2: return parsed
        lx, ly = self.field[0]

        for x, y in self.field[1:]:
            parsed.append((x - lx, y - ly))
            lx, ly = x, y
        return parsed

    def paintEvent(self, event):
        self.setMinimumHeight(self.parent().height())
        self.setMinimumWidth(self.parent().width())

        painter = QPainter()
        painter.setPen(QPen(Qt.lightGray, 1))
        n = max(10, min(self.parent().width()-30, self.parent().height()-30) // 15)

        if len(self.field):
            for i in range(-1, 2):
                for j in range(-1, 2):
                    painter.fillRect(
                        14 + n * (self.field[-1][0] + i),
                        14 + n * (self.field[-1][1] + j),
                        n, n, Qt.gray
                    )
            for i, j in self.field[1:-1]:
                x = 14 + n * i
                y = 14 + n * j
                painter.fillRect(x, y, n, n, Qt.green)
            painter.fillRect(14 + n * self.field[0][0], 14 + n * self.field[0][1], n, n, Qt.darkRed)
            painter.fillRect(14 + n * self.field[-1][0], 14 + n * self.field[-1][1], n, n, Qt.darkGreen)

        x, y = 14, 14
        while x < self.parent().width()-14:
            y = 14
            while y < self.parent().height()-14:
                painter.drawRect(x, y, n, n)
                y += n
            x += n

        if self.parent().parent().parent().modeBox.currentIndex() != 2:
            alpha_color = QColor(100, 100, 100, 100)
            painter.fillRect(14, 14, self.parent().width() - 14, self.parent().height() - 14, alpha_color)

        painter.eraseRect(self.parent().width() - 14, 0, 20, self.parent().height())
        painter.eraseRect(0, self.parent().height() - 14, self.parent().width(), 20)

        painter.setPen(QPen(Qt.black, 8, Qt.DashLine))
        painter.drawRect(10, 10, self.parent().width() - 20, self.parent().height() - 20)
