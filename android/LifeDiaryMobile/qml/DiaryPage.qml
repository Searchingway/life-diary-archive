import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: page

    property var diaryItems: []
    property var heatmap: ({})
    property var diaryImages: []
    property string currentId: ""

    background: Rectangle { color: "#F6F7F3" }

    function refresh() {
        diaryItems = archiveStore.searchDiaries(searchField.text)
        heatmap = archiveStore.diaryHeatmap(18)
    }

    function startNew() {
        const entry = archiveStore.createDiary()
        currentId = entry.id
        dateField.text = entry.date
        titleField.text = entry.title
        bodyField.text = entry.body
        setDiaryImages(entry.images || [])
    }

    function loadEntry(entryId) {
        const entry = archiveStore.getDiary(entryId)
        if (!entry || !entry.id) {
            return
        }
        currentId = entry.id
        dateField.text = entry.date
        titleField.text = entry.title
        bodyField.text = entry.body
        setDiaryImages(entry.images || [])
    }

    function saveCurrent() {
        const saved = archiveStore.saveDiary({
            "id": currentId,
            "date": dateField.text,
            "title": titleField.text,
            "body": bodyField.text,
            "images": diaryImages
        })
        if (saved && saved.id) {
            currentId = saved.id
            setDiaryImages(saved.images || [])
            refresh()
        }
    }

    function setDiaryImages(images) {
        diaryImages = images || []
        if (typeof diaryImagePanel !== "undefined" && diaryImagePanel !== null) {
            diaryImagePanel.setImages(diaryImages)
        }
    }

    Component.onCompleted: {
        refresh()
        if (diaryItems.length > 0) {
            loadEntry(diaryItems[0].id)
        } else {
            startNew()
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
                    text: "日记"
                }

                Button {
                    text: "新建"
                    onClicked: startNew()
                }

                Button {
                    text: "导出包"
                    onClicked: archiveStore.exportModulePackage("diary")
                }
            }

            TextField {
                id: searchField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "搜索日期、标题、正文"
                onTextChanged: refresh()
            }

            ListView {
                id: diaryList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: diaryItems.length === 0 ? 88 : Math.min(330, diaryItems.length * 84)
                spacing: 8
                clip: true
                model: diaryItems

                delegate: RecordCard {
                    width: diaryList.width
                    title: modelData.displayTitle
                    subtitle: modelData.date
                    meta: modelData.body
                    selected: modelData.id === currentId
                    onClicked: loadEntry(modelData.id)
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                visible: diaryItems.length === 0
                horizontalAlignment: Text.AlignHCenter
                color: "#7A8493"
                text: "暂无日记"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                height: 1
                color: "#DDE2E8"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                height: 126
                radius: 10
                color: "#FFFFFF"
                border.color: "#D8DDD2"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 8

                    Label {
                        Layout.fillWidth: true
                        color: "#24452E"
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        text: heatmap.summary ? heatmap.summary : "最近 18 周日记热力图"
                    }

                    GridLayout {
                        id: heatGrid
                        columns: 18
                        rowSpacing: 4
                        columnSpacing: 4

                        Repeater {
                            model: heatmap.cells ? heatmap.cells : []

                            Rectangle {
                                width: 12
                                height: 12
                                radius: 3
                                color: modelData.color

                                MouseArea {
                                    id: heatHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }

                                ToolTip.visible: heatHover.containsMouse
                                ToolTip.text: modelData.date + "：" + modelData.count + " 篇"
                            }
                        }
                    }
                }
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "日期"
            }

            TextField {
                id: dateField
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
                text: "标题"
            }

            TextField {
                id: titleField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "给今天留一个名字"
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "正文"
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 340
                clip: true

                TextArea {
                    id: bodyField
                    wrapMode: TextEdit.Wrap
                    placeholderText: "今天发生了什么"
                }
            }

            ImageListEditor {
                id: diaryImagePanel
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                title: "已插入图片"
                scope: "diary"
                primaryId: page.currentId
                emptyText: "还没有给这篇日记插入图片"
                onImagesUpdated: function(images) {
                    page.diaryImages = images
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10

                Button {
                    Layout.fillWidth: true
                    text: "保存"
                    highlighted: true
                    onClicked: saveCurrent()
                }

                Button {
                    Layout.fillWidth: true
                    text: "删除"
                    enabled: currentId.length > 0
                    onClicked: {
                        if (archiveStore.deleteDiary(currentId)) {
                            refresh()
                            if (diaryItems.length > 0) {
                                loadEntry(diaryItems[0].id)
                            } else {
                                startNew()
                            }
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 18 }
        }
    }
}
