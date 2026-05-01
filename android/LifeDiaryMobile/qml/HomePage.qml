import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: page

    property string pageTitle: "人生档案随手记"
    signal openPage(string key)

    background: Rectangle { color: "#F6F7F3" }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        ColumnLayout {
            width: page.width
            spacing: 14

            Item { Layout.preferredHeight: 10 }

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 18
                Layout.rightMargin: 18
                text: "每天能快速记录、稳定保存、方便导出。"
                color: "#53645A"
                font.pixelSize: 14
                wrapMode: Text.Wrap
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                columns: page.width < 430 ? 2 : 3
                rowSpacing: 10
                columnSpacing: 10

                Repeater {
                    model: [
                        {"key": "diary", "title": "写日记", "meta": "今天发生了什么"},
                        {"key": "footprint", "title": "记足迹", "meta": "地点和日期记录"},
                        {"key": "plan", "title": "轻计划", "meta": "只记下一步"},
                        {"key": "thought", "title": "轻思考", "meta": "暂时想不明白"},
                        {"key": "resource", "title": "轻资源", "meta": "时间金钱精力"},
                        {"key": "observation", "title": "自我观察", "meta": "此刻状态"}
                    ]

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 104
                        radius: 8
                        color: "#FFFFFF"
                        border.color: "#D8DDD2"
                        border.width: 1

                        Column {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 8

                            Label {
                                width: parent.width
                                text: modelData.title
                                color: "#202722"
                                font.pixelSize: 17
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            Label {
                                width: parent.width
                                text: modelData.meta
                                color: "#6A766C"
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: page.openPage(modelData.key)
                        }
                    }
                }
            }

            Button {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "数据管理"
                highlighted: true
                onClicked: page.openPage("data")
            }

            Button {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "读书笔记"
                onClicked: page.openPage("book")
            }

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 18
                Layout.rightMargin: 18
                text: "日记、足迹、轻计划和图片数据会继续沿用原来的保存结构。"
                color: "#7A8493"
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }

            Item { Layout.preferredHeight: 18 }
        }
    }
}
