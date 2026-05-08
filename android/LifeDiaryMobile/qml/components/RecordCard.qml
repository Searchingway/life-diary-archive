import QtQuick
import QtQuick.Controls

Rectangle {
    id: root

    property string title: ""
    property string subtitle: ""
    property string meta: ""
    property bool selected: false
    signal clicked()

    width: parent ? parent.width : 320
    height: 76
    radius: 8
    clip: true
    color: selected ? "#DCEBD8" : "#FFFFFF"
    border.color: selected ? "#315C3C" : "#D8DDD2"
    border.width: 1

    MouseArea {
        anchors.fill: parent
        onClicked: root.clicked()
    }

    Column {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        spacing: 4

        Label {
            width: parent.width
            height: 20
            color: "#202722"
            elide: Text.ElideRight
            font.pixelSize: 15
            font.weight: Font.DemiBold
            text: root.title
            verticalAlignment: Text.AlignVCenter
        }

        Label {
            width: parent.width
            height: 16
            color: "#53645A"
            elide: Text.ElideRight
            font.pixelSize: 12
            text: root.subtitle
            visible: text.length > 0
            verticalAlignment: Text.AlignVCenter
        }

        Label {
            width: parent.width
            height: 16
            color: "#6F7F57"
            elide: Text.ElideRight
            maximumLineCount: 1
            font.pixelSize: 11
            text: root.meta
            visible: text.length > 0
            verticalAlignment: Text.AlignVCenter
        }
    }
}
