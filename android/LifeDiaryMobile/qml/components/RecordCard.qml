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
    color: selected ? "#DCEBD8" : "#FFFFFF"
    border.color: selected ? "#315C3C" : "#D8DDD2"
    border.width: 1

    MouseArea {
        anchors.fill: parent
        onClicked: root.clicked()
    }

    Column {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 4

        Label {
            width: parent.width
            color: "#202722"
            elide: Text.ElideRight
            font.pixelSize: 15
            font.weight: Font.DemiBold
            text: root.title
        }

        Label {
            width: parent.width
            color: "#53645A"
            elide: Text.ElideRight
            font.pixelSize: 12
            text: root.subtitle
            visible: text.length > 0
        }

        Label {
            width: parent.width
            color: "#6F7F57"
            elide: Text.ElideRight
            font.pixelSize: 11
            text: root.meta
            visible: text.length > 0
        }
    }
}
