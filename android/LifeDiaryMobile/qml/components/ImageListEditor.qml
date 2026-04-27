import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ColumnLayout {
    id: root

    property string title: "图片"
    property string scope: ""
    property string primaryId: ""
    property string secondaryId: ""
    property string emptyText: "还没有图片"
    property string addButtonText: "添加图片"
    property var imageItems: []
    property int selectedIndex: -1
    property bool syncingLabel: false

    signal imagesUpdated(var images)

    Layout.fillWidth: true
    spacing: 8
    onSelectedIndexChanged: syncLabelField()

    function setImages(value) {
        imageItems = value || []
        if (imageItems.length === 0) {
            selectedIndex = -1
        } else if (selectedIndex < 0 || selectedIndex >= imageItems.length) {
            selectedIndex = 0
        }
        syncLabelField()
    }

    function replaceImages(value, preferredIndex) {
        imageItems = value || []
        if (imageItems.length === 0) {
            selectedIndex = -1
        } else {
            selectedIndex = Math.max(0, Math.min(preferredIndex, imageItems.length - 1))
        }
        syncLabelField()
        imagesUpdated(imageItems)
    }

    function selectedImage() {
        if (selectedIndex < 0 || selectedIndex >= imageItems.length) {
            return null
        }
        return imageItems[selectedIndex]
    }

    function imageTitle(index, image) {
        if (image && image.label && image.label.length > 0) {
            return image.label
        }
        return "图片 " + (index + 1)
    }

    function previewUrl() {
        const image = selectedImage()
        if (!image || !image.file_name) {
            return ""
        }
        return archiveStore.imageFileUrl(scope, primaryId, secondaryId, image.file_name)
    }

    function syncLabelField() {
        if (typeof labelField === "undefined" || labelField === null) {
            return
        }
        const image = selectedImage()
        syncingLabel = true
        labelField.text = image && image.label ? image.label : ""
        syncingLabel = false
    }

    FieldLabel {
        Layout.fillWidth: true
        text: root.title
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8

        Button {
            Layout.fillWidth: true
            text: root.addButtonText
            onClicked: imageDialog.open()
        }

        Button {
            Layout.fillWidth: true
            text: "移除所选"
            enabled: root.selectedIndex >= 0
            onClicked: {
                const updated = archiveStore.removeImageAt(root.imageItems, root.selectedIndex)
                root.replaceImages(updated, Math.min(root.selectedIndex, updated.length - 1))
            }
        }
    }

    ListView {
        id: imageList
        Layout.fillWidth: true
        height: root.imageItems.length === 0 ? 54 : Math.min(190, root.imageItems.length * 58)
        spacing: 8
        clip: true
        model: root.imageItems

        delegate: Rectangle {
            width: imageList.width
            height: 50
            radius: 8
            color: index === root.selectedIndex ? "#DCEBD8" : "#FFFFFF"
            border.color: index === root.selectedIndex ? "#315C3C" : "#D8DDD2"
            border.width: 1

            MouseArea {
                anchors.fill: parent
                onClicked: root.selectedIndex = index
            }

            Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 2

                Label {
                    width: parent.width
                    color: "#202722"
                    elide: Text.ElideRight
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    text: root.imageTitle(index, modelData)
                }

                Label {
                    width: parent.width
                    color: "#6F7F57"
                    elide: Text.ElideRight
                    font.pixelSize: 11
                    text: modelData.file_name || ""
                }
            }
        }
    }

    Label {
        Layout.fillWidth: true
        visible: root.imageItems.length === 0
        horizontalAlignment: Text.AlignHCenter
        color: "#7A8493"
        font.pixelSize: 12
        text: root.emptyText
    }

    TextField {
        id: labelField
        Layout.fillWidth: true
        enabled: root.selectedIndex >= 0
        placeholderText: "图片备注（导出 Word / PDF 时显示）"
        onTextChanged: {
            if (root.syncingLabel || root.selectedIndex < 0) {
                return
            }
            const updated = archiveStore.updateImageLabel(root.imageItems, root.selectedIndex, text)
            root.replaceImages(updated, root.selectedIndex)
        }
    }

    Rectangle {
        Layout.fillWidth: true
        height: 180
        radius: 8
        color: "#FFFFFF"
        border.color: "#D8DDD2"
        border.width: 1

        Image {
            anchors.fill: parent
            anchors.margins: 8
            source: root.previewUrl()
            asynchronous: true
            cache: false
            fillMode: Image.PreserveAspectFit
            visible: source.toString().length > 0
        }

        Label {
            anchors.centerIn: parent
            visible: root.previewUrl().length === 0
            color: "#7A8493"
            text: root.selectedIndex >= 0 ? "图片无法预览" : "未选择图片"
        }
    }

    FileDialog {
        id: imageDialog
        title: "选择图片"
        fileMode: FileDialog.OpenFiles
        nameFilters: ["图片 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"]
        onAccepted: {
            let next = root.imageItems
            const files = selectedFiles && selectedFiles.length > 0 ? selectedFiles : [selectedFile]
            for (let i = 0; i < files.length; ++i) {
                next = archiveStore.importImage(root.scope, root.primaryId, root.secondaryId, next, files[i])
            }
            root.replaceImages(next, next.length - 1)
        }
    }
}
