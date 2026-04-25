import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: page

    property var placeItems: []
    property var visitItems: []
    property string currentPlaceId: ""
    property string currentVisitId: ""

    background: Rectangle { color: "#F6F7F3" }

    function refresh() {
        placeItems = archiveStore.searchFootprints(searchField.text)
    }

    function startNewPlace() {
        const place = archiveStore.createFootprint()
        currentPlaceId = place.id
        placeNameField.text = place.place_name
        summaryField.text = place.summary
        visitItems = []
        startNewVisit()
    }

    function loadPlace(placeId) {
        const place = archiveStore.getFootprint(placeId)
        if (!place || !place.id) {
            return
        }
        currentPlaceId = place.id
        placeNameField.text = place.place_name
        summaryField.text = place.summary
        visitItems = place.visits || []
        if (visitItems.length > 0) {
            loadVisit(visitItems[0])
        } else {
            startNewVisit()
        }
    }

    function savePlaceOnly() {
        const saved = archiveStore.saveFootprint({
            "id": currentPlaceId,
            "place_name": placeNameField.text,
            "summary": summaryField.text
        })
        if (saved && saved.id) {
            currentPlaceId = saved.id
            visitItems = saved.visits || []
            refresh()
        }
        return saved
    }

    function startNewVisit() {
        const visit = archiveStore.createFootprintVisit()
        currentVisitId = visit.id
        visitDateField.text = visit.date
        visitThoughtField.text = visit.thought
    }

    function loadVisit(visit) {
        currentVisitId = visit.id
        visitDateField.text = visit.date
        visitThoughtField.text = visit.thought
    }

    function saveVisit() {
        const savedPlace = savePlaceOnly()
        if (!savedPlace || !savedPlace.id) {
            return
        }
        const updated = archiveStore.saveFootprintVisit(currentPlaceId, {
            "id": currentVisitId,
            "date": visitDateField.text,
            "thought": visitThoughtField.text
        })
        if (updated && updated.id) {
            visitItems = updated.visits || []
            refresh()
        }
    }

    Component.onCompleted: {
        refresh()
        if (placeItems.length > 0) {
            loadPlace(placeItems[0].id)
        } else {
            startNewPlace()
        }
    }

    Connections {
        target: archiveStore
        function onDataChanged() {
            refresh()
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        ColumnLayout {
            width: page.width
            spacing: 12

            Item { Layout.preferredHeight: 4 }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10

                SectionTitle {
                    Layout.fillWidth: true
                    text: "足迹"
                }

                Button {
                    text: "新建"
                    onClicked: startNewPlace()
                }

                Button {
                    text: "导出包"
                    onClicked: archiveStore.exportModulePackage("footprint")
                }
            }

            TextField {
                id: searchField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "搜索地点、简介、日期、感悟"
                onTextChanged: refresh()
            }

            ListView {
                id: placeList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                height: placeItems.length === 0 ? 88 : Math.min(310, placeItems.length * 84)
                spacing: 8
                clip: true
                model: placeItems

                delegate: RecordCard {
                    width: placeList.width
                    title: modelData.displayTitle
                    subtitle: modelData.latestVisitDate ? modelData.latestVisitDate : "未添加日期"
                    meta: "日期记录 " + modelData.visitCount
                    selected: modelData.id === currentPlaceId
                    onClicked: loadPlace(modelData.id)
                }
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "地点名称"
            }

            TextField {
                id: placeNameField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "去了哪里"
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "地点简介"
            }

            TextArea {
                id: summaryField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 150
                wrapMode: TextEdit.Wrap
                placeholderText: "这个地点给你的长期印象"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10

                Button {
                    Layout.fillWidth: true
                    text: "保存地点"
                    highlighted: true
                    onClicked: savePlaceOnly()
                }

                Button {
                    Layout.fillWidth: true
                    text: "删除地点"
                    onClicked: {
                        if (archiveStore.deleteFootprint(currentPlaceId)) {
                            refresh()
                            if (placeItems.length > 0) {
                                loadPlace(placeItems[0].id)
                            } else {
                                startNewPlace()
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                height: 1
                color: "#DDE2E8"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10

                SectionTitle {
                    Layout.fillWidth: true
                    text: "日期记录"
                    font.pixelSize: 16
                }

                Button {
                    text: "新增"
                    onClicked: startNewVisit()
                }
            }

            ListView {
                id: visitList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                height: visitItems.length === 0 ? 0 : Math.min(230, visitItems.length * 76)
                spacing: 8
                clip: true
                model: visitItems

                delegate: RecordCard {
                    width: visitList.width
                    height: 68
                    title: modelData.displayTitle
                    subtitle: modelData.thought
                    selected: modelData.id === currentVisitId
                    onClicked: loadVisit(modelData)
                }
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "日期"
            }

            TextField {
                id: visitDateField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                inputMethodHints: Qt.ImhDate
                placeholderText: "2026-04-24"
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "当天感悟"
            }

            TextArea {
                id: visitThoughtField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 220
                wrapMode: TextEdit.Wrap
                placeholderText: "这一天在这里留下了什么"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10

                Button {
                    Layout.fillWidth: true
                    text: "保存日期"
                    highlighted: true
                    onClicked: saveVisit()
                }

                Button {
                    Layout.fillWidth: true
                    text: "删除日期"
                    enabled: currentVisitId.length > 0 && visitItems.length > 0
                    onClicked: {
                        if (archiveStore.deleteFootprintVisit(currentPlaceId, currentVisitId)) {
                            loadPlace(currentPlaceId)
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 18 }
        }
    }
}
