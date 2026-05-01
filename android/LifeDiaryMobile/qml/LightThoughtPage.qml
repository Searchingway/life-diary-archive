import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: page

    property var items: []
    property var ideas: []
    property string currentId: ""
    property var typeOptions: ["接单思考", "学习思考", "人生方向", "关系问题", "情绪问题", "项目方案", "消费决策", "身体作息", "其他"]
    property var statusOptions: ["思考中", "已有结论", "已转计划", "暂时搁置"]

    background: Rectangle { color: "#F6F7F3" }

    function refresh() {
        items = archiveStore.searchThoughts(searchField.text)
    }

    function setCombo(combo, options, value, fallback) {
        const index = options.indexOf(value)
        combo.currentIndex = index >= 0 ? index : fallback
    }

    function setIdeas(value) {
        ideas = value || []
        ideaList.model = ideas
    }

    function startNew() {
        const record = archiveStore.createThought()
        currentId = record.id
        titleField.text = record.title
        descriptionField.text = record.description
        setCombo(typeBox, typeOptions, record.type, 8)
        setCombo(statusBox, statusOptions, record.status, 0)
        conclusionField.text = record.preliminary_conclusion
        notesField.text = record.notes
        setIdeas(record.ideas || [])
        newIdeaField.text = ""
    }

    function loadRecord(recordId) {
        const record = archiveStore.getThought(recordId)
        if (!record || !record.id) {
            return
        }
        currentId = record.id
        titleField.text = record.title
        descriptionField.text = record.description
        setCombo(typeBox, typeOptions, record.type, 8)
        setCombo(statusBox, statusOptions, record.status, 0)
        conclusionField.text = record.preliminary_conclusion
        notesField.text = record.notes
        setIdeas(record.ideas || [])
        newIdeaField.text = ""
    }

    function addIdea() {
        const text = newIdeaField.text.trim()
        if (text.length === 0) {
            return
        }
        const next = ideas.slice()
        next.push({"id": Date.now().toString(), "time": new Date().toISOString(), "text": text})
        setIdeas(next)
        newIdeaField.text = ""
        saveCurrent()
    }

    function saveCurrent() {
        const saved = archiveStore.saveThought({
            "id": currentId,
            "title": titleField.text,
            "description": descriptionField.text,
            "type": typeBox.currentText,
            "status": statusBox.currentText,
            "ideas": ideas,
            "preliminary_conclusion": conclusionField.text,
            "notes": notesField.text
        })
        if (saved && saved.id) {
            currentId = saved.id
            setIdeas(saved.ideas || [])
            refresh()
        }
    }

    Component.onCompleted: {
        refresh()
        items.length > 0 ? loadRecord(items[0].id) : startNew()
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
            if (archiveStore.deleteThought(currentId)) {
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
                SectionTitle { Layout.fillWidth: true; text: "轻思考" }
                Button { text: "新建"; onClicked: startNew() }
            }

            TextField {
                id: searchField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "搜索标题、类型、状态、描述"
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
                    title: modelData.displayTitle
                    subtitle: modelData.type + " | " + modelData.status
                    meta: modelData.description
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
                text: "暂无轻思考"
            }

            FieldLabel { Layout.leftMargin: 16; text: "标题 / 问题" }
            TextField {
                id: titleField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "现在想不明白什么"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10
                ColumnLayout {
                    Layout.fillWidth: true
                    FieldLabel { text: "类型" }
                    ComboBox { id: typeBox; Layout.fillWidth: true; model: page.typeOptions }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    FieldLabel { text: "状态" }
                    ComboBox { id: statusBox; Layout.fillWidth: true; model: page.statusOptions }
                }
            }

            FieldLabel { Layout.leftMargin: 16; text: "简短描述" }
            ScrollView {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 120
                clip: true
                TextArea { id: descriptionField; wrapMode: TextEdit.Wrap; placeholderText: "一句话说明背景" }
            }

            FieldLabel { Layout.leftMargin: 16; text: "想法列表" }
            ListView {
                id: ideaList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: ideas.length === 0 ? 54 : Math.min(180, ideas.length * 72)
                spacing: 8
                clip: true
                model: ideas
                delegate: Rectangle {
                    width: ideaList.width
                    height: 64
                    radius: 8
                    color: "#FFFFFF"
                    border.color: "#D8DDD2"
                    Label {
                        anchors.fill: parent
                        anchors.margins: 10
                        text: modelData.text
                        color: "#202722"
                        wrapMode: Text.Wrap
                        elide: Text.ElideRight
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                visible: ideas.length === 0
                color: "#7A8493"
                horizontalAlignment: Text.AlignHCenter
                text: "还没有追加想法"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 8
                TextField {
                    id: newIdeaField
                    Layout.fillWidth: true
                    placeholderText: "追加一条想法"
                }
                Button { text: "追加"; onClicked: addIdea() }
            }

            FieldLabel { Layout.leftMargin: 16; text: "初步结论" }
            TextField {
                id: conclusionField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "如果暂时没有结论，可以留空"
            }

            FieldLabel { Layout.leftMargin: 16; text: "备注" }
            ScrollView {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 140
                clip: true
                TextArea { id: notesField; wrapMode: TextEdit.Wrap }
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
