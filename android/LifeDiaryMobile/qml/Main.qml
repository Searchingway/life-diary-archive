import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material

ApplicationWindow {
    id: window

    width: 390
    height: 844
    visible: true
    title: "人生档案"
    color: "#F6F7F3"

    Material.theme: Material.Light
    Material.accent: "#315C3C"

    header: ToolBar {
        height: 56
        background: Rectangle { color: "#FFFFFF" }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 18

            Label {
                Layout.fillWidth: true
                text: "人生档案"
                color: "#202722"
                font.pixelSize: 20
                font.weight: Font.DemiBold
            }

            Label {
                text: "本地"
                color: "#315C3C"
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
        }
    }

    SwipeView {
        id: pages
        anchors.fill: parent
        currentIndex: nav.currentIndex
        interactive: false

        DiaryPage {}
        FootprintPage {}
        BookPage {}
        PlanPage {}
    }

    footer: TabBar {
        id: nav
        currentIndex: pages.currentIndex
        background: Rectangle { color: "#FFFFFF" }

        TabButton { text: "日记" }
        TabButton { text: "足迹" }
        TabButton { text: "读书" }
        TabButton { text: "计划" }
    }

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
