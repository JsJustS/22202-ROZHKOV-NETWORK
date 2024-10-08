import asyncio

import aiohttp.client_exceptions
from PyQt6 import QtGui

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
        self.searchLine.returnPressed.connect(self.refreshList)
        self.list.itemDoubleClicked.connect(self.showDataWidget)

        self.loop = loop or asyncio.get_event_loop()
        self.list_of_locations = list()
        self.show()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        super(Window, self).closeEvent(a0)

    @asyncSlot()
    async def refreshList(self):
        suggestion = self.searchLine.text()
        if suggestion == "":
            return

        self.list_of_locations = await asreq.getListOfLocationsFromSuggestion(suggestion)
        self.list.clear()

        if isinstance(self.list_of_locations, asreq.LocationException):
            err = self.list_of_locations
            message = f"[{err.error_code}]: {str(err)}"
            self.list.addItem(message)
            return

        for location in self.list_of_locations:
            item = ""
            if location.name is not None: item += location.name
            if location.country is not None: item += ", " + location.country
            if location.state is not None: item += ", " + location.state
            if location.street is not None: item += ", " + location.street
            if location.osm_id is not None: item += ", " + str(location.osm_id)
            if location.osm_type is not None: item += ", " + location.osm_type
            if location.osm_key is not None: item += ", " + location.osm_key
            if location.osm_value is not None: item += ", " + location.osm_value
            self.list.addItem(item)

    def showDataWidget(self, item: QListWidgetItem):
        try:
            index = self.list.indexFromItem(item).row()
            location = self.list_of_locations[index]

            new_window = DataWindow(location)
            new_window.show()

            asyncio.ensure_future(new_window.updateLocationData())
        except Exception as e:
            print(e)


class DataWindow(QWidget):
    def __init__(self, location: asreq.Location):
        super().__init__()
        self.location = location
        self.ui = uic.loadUi('design/data.ui', self)
        self.setWindowTitle(location.name + " | " + location.osm_value)

        self.list_of_pois = list()
        self.poiList.itemClicked.connect(self.setDesc)

    async def updateLocationData(self):
        await asyncio.gather(
            asyncio.create_task(self.updateWeather()),
            asyncio.create_task(self.updatePOIs())
        )

    async def updateWeather(self):
        self.weatherLine.setText("Загружается...")
        try:
            weather = await asreq.getWeatherInLocation(self.location)
            self.weatherLine.setText(weather)
        except aiohttp.client_exceptions.ClientConnectorError:
            self.weatherLine.setText("Не коннектится к api :(")

    async def updatePOIs(self):
        self.poiList.setDisabled(True)
        self.poiList.clear()
        self.poiDesc.clear()

        self.poiList.addItem("Загружается...")

        self.list_of_pois = await asreq.getPOIsWithDescriptionInLocation(self.location)
        self.list_of_pois = list(filter(lambda x: x is not None, self.list_of_pois))

        self.poiList.clear()
        for poi in self.list_of_pois:
            item = poi.name if poi.name else str(poi.lat) + ", " + str(poi.lng)
            self.poiList.addItem(item)
        self.poiList.setEnabled(True)

    def setDesc(self, item):
        try:
            index = self.poiList.indexFromItem(item).row()
            poi = self.list_of_pois[index]

            self.poiDesc.clear()
            self.poiDesc.setPlainText(poi.getDescription())
        except Exception as e:
            print(e)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = Window()
    with loop:
        loop.run_forever()
