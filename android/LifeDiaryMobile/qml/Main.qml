import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material

ApplicationWindow {
    id: window

    width: 390
    height: 844
    visible: true
    title: "人生档案随手记"
    color: "#F6F7F3"

    Material.theme: Material.Light
    Material.accent: "#315C3C"

    function openPage(key) {
        const map = {
            "diary": diaryPageComponent,
            "footprint": footprintPageComponent,
            "plan": planPageComponent,
            "thought": thoughtPageComponent,
            "resource": resourcePageComponent,
            "observation": observationPageComponent,
            "data": dataManagerPageComponent,
            "book": bookPageComponent
        }
        if (map[key]) {
            stack.push(map[key])
        }
    }

    header: ToolBar {
        height: 56
        background: Rectangle { color: "#FFFFFF" }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 18
            spacing: 8

            ToolButton {
                visible: stack.depth > 1
                text: "‹"
                font.pixelSize: 26
                onClicked: stack.pop()
            }

            Label {
                Layout.fillWidth: true
                text: stack.currentItem && stack.currentItem.pageTitle ? stack.currentItem.pageTitle : "人生档案随手记"
                color: "#202722"
                font.pixelSize: 20
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            Label {
                text: "本地"
                color: "#315C3C"
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
        }
    }

    StackView {
        id: stack
        anchors.fill: parent
        initialItem: HomePage {
            onOpenPage: function(key) {
                window.openPage(key)
            }
        }
    }

    Component { id: diaryPageComponent; DiaryPage { property string pageTitle: "写日记" } }
    Component { id: footprintPageComponent; FootprintPage { property string pageTitle: "记足迹" } }
    Component { id: planPageComponent; PlanPage { property string pageTitle: "轻计划" } }
    Component { id: thoughtPageComponent; LightThoughtPage { property string pageTitle: "轻思考" } }
    Component { id: resourcePageComponent; LightResourcePage { property string pageTitle: "轻资源" } }
    Component { id: observationPageComponent; SelfObservationPage { property string pageTitle: "自我观察" } }
    Component { id: dataManagerPageComponent; DataManagerPage { property string pageTitle: "数据管理" } }
    Component { id: bookPageComponent; BookPage { property string pageTitle: "读书笔记" } }

    Popup {
        id: toastPopup
        x: Math.round((window.width - width) / 2)
        y: window.height - height - 92
        width: Math.min(window.width - 36, toastLabel.implicitWidth + 36)
        height: toastLabel.implicitHeight + 22
        modal: false
        focus: false
        closePolicy: Popup.NoAutoClose
        padding: 0

        background: Rectangle {
            radius: 8
            color: archiveStore.lastError.length > 0 ? "#9D3D35" : "#24452E"
        }

        Label {
            id: toastLabel
            anchors.centerIn: parent
            width: parent.width - 24
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            color: "#FFFFFF"
            font.pixelSize: 13
            text: archiveStore.lastError.length > 0 ? archiveStore.lastError : archiveStore.toast
        }

        Timer {
            id: toastTimer
            interval: 1800
            onTriggered: toastPopup.close()
        }
    }

    Connections {
        target: archiveStore
        function onToastChanged() {
            if (archiveStore.toast.length > 0) {
                toastPopup.open()
                toastTimer.restart()
            }
        }
        function onLastErrorChanged() {
            if (archiveStore.lastError.length > 0) {
                toastPopup.open()
                toastTimer.restart()
            }
        }
    }
}
