import asyncio
import asyncrequests as asreq

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QListWidgetItem
from qasync import QEventLoop, asyncSlot
import sys
from qtpy import uic


class Window(QMainWindow):
    def __init__(self, loop: QEventLoop = None):
        super().__init__()
        self.ui = uic.loadUi('design/main.ui', self)

        self.searchBtn.clicked.connect(self.refreshList)
        self.list.itemDoubleClicked.connect(self.showDataWidget)

        self.loop = loop or asyncio.get_event_loop()
        self.list_of_locations = list()
        self.show()

    @asyncSlot()
    async def refreshList(self):
        suggestion = self.searchLine.text()
        if suggestion == "":
            return

        self.list_of_locations = await asreq.getListOfLocationsFromSuggestion(suggestion)
        self.list.clear()
        for location in self.list_of_locations:
            self.list.addItem(location.name)

    def showDataWidget(self, item: QListWidgetItem):
        try:
            index = self.list.indexFromItem(item).row()
            location = self.list_of_locations[index]
            if location.name != item.text():
                raise Exception("cringe")

            new_window = DataWindow(location)
            new_window.show()

            asyncio.ensure_future(new_window.updateLocationData())
        except Exception as e:
            print(e)


class DataWindow(QWidget):
    def __init__(self, location: asreq.Location):
        super().__init__()
        self.ui = uic.loadUi('design/data.ui', self)
        self.setWindowTitle(location.name)

    async def updateLocationData(self):
        print("lol!")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = Window()
    with loop:
        loop.run_forever()
