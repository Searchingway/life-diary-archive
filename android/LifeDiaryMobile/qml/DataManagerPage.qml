import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "components"

Page {
    id: page

    property var overview: ({})
    property var modules: []

    background: Rectangle { color: "#F6F7F3" }

    function refresh() {
        overview = archiveStore.dataOverview()
        modules = overview.modules || []
    }

    Component.onCompleted: refresh()

    Connections {
        target: archiveStore
        function onDataChanged() { refresh() }
    }

    FileDialog {
        id: importDialog
        title: "选择 LifeDiary ZIP 数据包"
        nameFilters: ["ZIP 数据包 (*.zip)"]
        onAccepted: {
            if (archiveStore.importBackupPackage(selectedFile)) {
                refresh()
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        ColumnLayout {
            width: page.width
            spacing: 12

            Item { Layout.preferredHeight: 4 }

            SectionTitle {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "数据管理"
            }

            Button {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                highlighted: true
                text: "导出并分享数据包"
                onClicked: archiveStore.exportAndShareBackup()
            }

            Button {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "导出到本地"
                onClicked: archiveStore.exportFullBackup(false)
            }

            Button {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "从数据包导入"
                onClicked: importDialog.open()
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                radius: 8
                color: "#FFFFFF"
                border.color: "#D8DDD2"
                border.width: 1
                implicitHeight: dataColumn.implicitHeight + 28

                ColumnLayout {
                    id: dataColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 8

                    Label {
                        Layout.fillWidth: true
                        text: "当前数据目录"
                        color: "#24452E"
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }

                    Label {
                        Layout.fillWidth: true
                        text: overview.dataRoot || ""
                        color: "#202722"
                        font.pixelSize: 12
                        wrapMode: Text.WrapAnywhere
                    }

                    Label {
                        Layout.fillWidth: true
                        text: "本地导出目录：" + (overview.exportsPath || "")
                        color: "#53645A"
                        font.pixelSize: 12
                        wrapMode: Text.WrapAnywhere
                    }
                }
            }

            ListView {
                id: moduleList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: Math.max(88, modules.length * 58)
                spacing: 8
                interactive: false
                model: modules
                delegate: Rectangle {
                    width: moduleList.width
                    height: 50
                    radius: 8
                    color: "#FFFFFF"
                    border.color: "#D8DDD2"
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        Label {
                            Layout.fillWidth: true
                            text: modelData.title + "  " + modelData.folder
                            color: "#202722"
                            font.pixelSize: 14
                            elide: Text.ElideRight
                        }
                        Label {
                            text: modelData.count + " 条"
                            color: "#315C3C"
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                radius: 8
                color: "#FFFFFF"
                border.color: "#D8DDD2"
                border.width: 1
                implicitHeight: infoColumn.implicitHeight + 28

                ColumnLayout {
                    id: infoColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 8

                    Label {
                        Layout.fillWidth: true
                        text: "数据说明"
                        color: "#24452E"
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }

                    Label {
                        Layout.fillWidth: true
                        text: overview.description || "数据保存在本机 Diary 目录，建议定期导出备份。"
                        color: "#53645A"
                        font.pixelSize: 13
                        wrapMode: Text.Wrap
                    }

                    Label {
                        Layout.fillWidth: true
                        text: "分享数据包会生成 ZIP 后直接调起 Android 系统分享面板，可选择微信、QQ、文件传输助手、网盘或其他 App。导入前会自动备份当前数据，导入失败不会覆盖当前数据。"
                        color: "#53645A"
                        font.pixelSize: 13
                        wrapMode: Text.Wrap
                    }
                }
            }

            Item { Layout.preferredHeight: 18 }
        }
    }
}
