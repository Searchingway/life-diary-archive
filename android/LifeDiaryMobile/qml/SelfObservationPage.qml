import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: page

    property var items: []
    property string currentId: ""
    property var emotionOptions: ["开心", "平静", "焦虑", "难过", "生气", "疲惫", "空虚", "兴奋", "烦躁", "其他"]
    property var needOptions: ["休息", "吃饭", "睡觉", "运动", "找人说话", "继续做事", "暂时放下", "写下来", "其他"]

    background: Rectangle { color: "#F6F7F3" }

    function refresh() {
        items = archiveStore.searchObservations(searchField.text)
    }

    function setCombo(combo, options, value, fallback) {
        const index = options.indexOf(value)
        combo.currentIndex = index >= 0 ? index : fallback
    }

    function startNew() {
        const record = archiveStore.createObservation()
        currentId = record.id
        timeField.text = record.time
        setCombo(emotionBox, emotionOptions, record.emotion, 1)
        intensitySlider.value = record.intensity || 3
        triggerField.text = record.trigger
        bodyField.text = record.body_sensation
        setCombo(needBox, needOptions, record.need, 7)
        notesField.text = record.notes
    }

    function loadRecord(recordId) {
        const record = archiveStore.getObservation(recordId)
        if (!record || !record.id) {
            return
        }
        currentId = record.id
        timeField.text = record.time
        setCombo(emotionBox, emotionOptions, record.emotion, 1)
        intensitySlider.value = record.intensity || 3
        triggerField.text = record.trigger
        bodyField.text = record.body_sensation
        setCombo(needBox, needOptions, record.need, 7)
        notesField.text = record.notes
    }

    function saveCurrent() {
        const saved = archiveStore.saveObservation({
            "id": currentId,
            "time": timeField.text,
            "emotion": emotionBox.currentText,
            "intensity": Math.round(intensitySlider.value),
            "trigger": triggerField.text,
            "body_sensation": bodyField.text,
            "need": needBox.currentText,
            "notes": notesField.text
        })
        if (saved && saved.id) {
            currentId = saved.id
            refresh()
        }
    }

    Component.onCompleted: {
        refresh()
        if (items.length > 0) {
            loadRecord(items[0].id)
        } else {
            startNew()
        }
    }

    Connections {
        target: archiveStore
        function onDataChanged() { refresh() }
    }

    Dialog {
        id: deleteDialog
        title: "确认删除"
        modal: true
        standardButtons: Dialog.Yes | Dialog.No
        onAccepted: {
            if (archiveStore.deleteObservation(currentId)) {
                refresh()
                items.length > 0 ? loadRecord(items[0].id) : startNew()
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

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                SectionTitle { Layout.fillWidth: true; text: "自我观察" }
                Button { text: "新建"; onClicked: startNew() }
            }

            TextField {
                id: searchField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "搜索情绪、触发原因、身体感受"
                onTextChanged: refresh()
            }

            ListView {
                id: recordList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: items.length === 0 ? 88 : Math.min(300, items.length * 84)
                spacing: 8
                clip: true
                model: items
                delegate: RecordCard {
                    width: recordList.width
                    title: modelData.emotion + " " + modelData.intensity + "/5"
                    subtitle: modelData.time
                    meta: modelData.need
                    selected: modelData.id === currentId
                    onClicked: loadRecord(modelData.id)
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                visible: items.length === 0
                horizontalAlignment: Text.AlignHCenter
                color: "#7A8493"
                text: "暂无自我观察"
            }

            FieldLabel { Layout.leftMargin: 16; text: "时间" }
            TextField {
                id: timeField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "自动生成，也可以手动改"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    FieldLabel { text: "情绪" }
                    ComboBox { id: emotionBox; Layout.fillWidth: true; model: page.emotionOptions }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    FieldLabel { text: "我现在需要什么" }
                    ComboBox { id: needBox; Layout.fillWidth: true; model: page.needOptions }
                }
            }

            FieldLabel { Layout.leftMargin: 16; text: "强度 " + Math.round(intensitySlider.value) + "/5" }
            Slider {
                id: intensitySlider
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                from: 1
                to: 5
                stepSize: 1
                snapMode: Slider.SnapAlways
                value: 3
            }

            FieldLabel { Layout.leftMargin: 16; text: "触发原因" }
            TextField {
                id: triggerField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "刚才发生了什么"
            }

            FieldLabel { Layout.leftMargin: 16; text: "身体感受" }
            TextField {
                id: bodyField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "胸口、胃、肩颈、困意等"
            }

            FieldLabel { Layout.leftMargin: 16; text: "备注" }
            ScrollView {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 160
                clip: true
                TextArea { id: notesField; wrapMode: TextEdit.Wrap; placeholderText: "补充一句就行" }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10
                Button { Layout.fillWidth: true; highlighted: true; text: "保存"; onClicked: saveCurrent() }
                Button { Layout.fillWidth: true; text: "删除"; enabled: currentId.length > 0; onClicked: deleteDialog.open() }
            }

            Item { Layout.preferredHeight: 18 }
        }
    }
}
