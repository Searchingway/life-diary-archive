import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: page

    property var items: []
    property var resourceItems: []
    property string currentId: ""
    property var typeOptions: ["接单", "学习", "武术", "精神分析", "消费", "项目", "关系", "身体", "其他"]
    property var statusOptions: ["考虑中", "已决定", "已放弃", "已完成"]
    property var resourceOptions: ["时间", "金钱", "精力", "情绪", "勇气", "身体", "注意力", "风险", "机会成本", "其他"]
    property var blockOptions: ["不打断", "轻微打断", "明显打断", "毁掉半天", "毁掉一天"]
    property var moneyCycleOptions: ["一次性", "每天", "每周", "每月", "每年"]
    property var moneyDirectionOptions: ["支出", "收入", "需要预留"]

    background: Rectangle { color: "#F6F7F3" }

    function refresh() {
        items = archiveStore.searchResources(searchField.text)
    }

    function setCombo(combo, options, value, fallback) {
        const index = options.indexOf(value)
        combo.currentIndex = index >= 0 ? index : fallback
    }

    function setResourceItems(value) {
        resourceItems = value || []
        resourceList.model = resourceItems
    }

    function startNew() {
        const record = archiveStore.createResource()
        currentId = record.id
        titleField.text = record.title
        descriptionField.text = record.description
        setCombo(typeBox, typeOptions, record.type, 8)
        setCombo(statusBox, statusOptions, record.status, 0)
        setResourceItems(record.resource_items || [])
        overallField.text = record.overall_judgement
        feelingField.text = record.subjective_feeling
        const test = record.recurrence_test || {}
        nextWeekField.text = test.next_week || ""
        oneYearField.text = test.one_year || ""
        repeatField.text = test.repeat_willingness || ""
        notesField.text = record.notes
    }

    function loadRecord(recordId) {
        const record = archiveStore.getResource(recordId)
        if (!record || !record.id) {
            return
        }
        currentId = record.id
        titleField.text = record.title
        descriptionField.text = record.description
        setCombo(typeBox, typeOptions, record.type, 8)
        setCombo(statusBox, statusOptions, record.status, 0)
        setResourceItems(record.resource_items || [])
        overallField.text = record.overall_judgement
        feelingField.text = record.subjective_feeling
        const test = record.recurrence_test || {}
        nextWeekField.text = test.next_week || ""
        oneYearField.text = test.one_year || ""
        repeatField.text = test.repeat_willingness || ""
        notesField.text = record.notes
    }

    function addResourceItem() {
        const kind = resourceKindBox.currentText
        let item = {"id": Date.now().toString(), "type": kind, "remark": itemRemarkField.text}
        if (kind === "时间") {
            item.direct_time = directTimeField.text
            item.indirect_time = indirectTimeField.text
            item.recovery_time = recoveryTimeField.text
            item.block_time = blockBox.currentText
        } else if (kind === "金钱") {
            item.amount = amountField.text
            item.cycle = moneyCycleBox.currentText
            item.direction = moneyDirectionBox.currentText
        } else {
            item.value = genericValueField.text
        }
        const next = resourceItems.slice()
        next.push(item)
        setResourceItems(next)
        itemRemarkField.text = ""
        genericValueField.text = ""
        saveCurrent()
    }

    function removeResourceItem(index) {
        const next = resourceItems.slice()
        next.splice(index, 1)
        setResourceItems(next)
        saveCurrent()
    }

    function describeItem(item) {
        if (item.type === "时间") {
            return "直接 " + (item.direct_time || "-") + "，间接 " + (item.indirect_time || "-") + "，恢复 " + (item.recovery_time || "-") + "，" + (item.block_time || "不打断")
        }
        if (item.type === "金钱") {
            return (item.direction || "支出") + " " + (item.amount || "-") + " / " + (item.cycle || "一次性")
        }
        return (item.value || "") + (item.remark ? " | " + item.remark : "")
    }

    function saveCurrent() {
        const saved = archiveStore.saveResource({
            "id": currentId,
            "title": titleField.text,
            "description": descriptionField.text,
            "type": typeBox.currentText,
            "status": statusBox.currentText,
            "resource_items": resourceItems,
            "overall_judgement": overallField.text,
            "subjective_feeling": feelingField.text,
            "recurrence_test": {
                "next_week": nextWeekField.text,
                "one_year": oneYearField.text,
                "repeat_willingness": repeatField.text
            },
            "notes": notesField.text
        })
        if (saved && saved.id) {
            currentId = saved.id
            setResourceItems(saved.resource_items || [])
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
            if (archiveStore.deleteResource(currentId)) {
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
                SectionTitle { Layout.fillWidth: true; text: "轻资源" }
                Button { text: "新建"; onClicked: startNew() }
            }

            TextField {
                id: searchField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "搜索标题、类型、状态、判断"
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
                    meta: modelData.overall_judgement
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
                text: "暂无轻资源"
            }

            FieldLabel { Layout.leftMargin: 16; text: "标题" }
            TextField {
                id: titleField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "这件事是什么"
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

            FieldLabel { Layout.leftMargin: 16; text: "描述" }
            TextField {
                id: descriptionField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "简短描述"
            }

            FieldLabel { Layout.leftMargin: 16; text: "资源项" }
            ListView {
                id: resourceList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: resourceItems.length === 0 ? 54 : Math.min(220, resourceItems.length * 76)
                spacing: 8
                clip: true
                model: resourceItems
                delegate: Rectangle {
                    width: resourceList.width
                    height: 68
                    radius: 8
                    color: "#FFFFFF"
                    border.color: "#D8DDD2"
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { Layout.fillWidth: true; text: modelData.type; color: "#202722"; font.weight: Font.DemiBold; elide: Text.ElideRight }
                            Label { Layout.fillWidth: true; text: page.describeItem(modelData); color: "#53645A"; font.pixelSize: 12; elide: Text.ElideRight }
                        }
                        Button { text: "删"; onClicked: page.removeResourceItem(index) }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                visible: resourceItems.length === 0
                color: "#7A8493"
                horizontalAlignment: Text.AlignHCenter
                text: "还没有资源项"
            }

            ComboBox {
                id: resourceKindBox
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                model: page.resourceOptions
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                visible: resourceKindBox.currentText === "时间"
                spacing: 8
                TextField { id: directTimeField; Layout.fillWidth: true; placeholderText: "直接时间，例如 2 小时" }
                TextField { id: indirectTimeField; Layout.fillWidth: true; placeholderText: "间接时间，例如 沟通 30 分钟" }
                TextField { id: recoveryTimeField; Layout.fillWidth: true; placeholderText: "恢复时间，例如 需要休息半天" }
                ComboBox { id: blockBox; Layout.fillWidth: true; model: page.blockOptions }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                visible: resourceKindBox.currentText === "金钱"
                spacing: 8
                TextField { id: amountField; Layout.fillWidth: true; placeholderText: "金额" }
                ComboBox { id: moneyCycleBox; Layout.fillWidth: true; model: page.moneyCycleOptions }
                ComboBox { id: moneyDirectionBox; Layout.fillWidth: true; model: page.moneyDirectionOptions }
            }

            TextField {
                id: genericValueField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                visible: resourceKindBox.currentText !== "时间" && resourceKindBox.currentText !== "金钱"
                placeholderText: "资源消耗描述"
            }

            TextField {
                id: itemRemarkField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "资源项备注"
            }

            Button {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "添加资源项"
                onClicked: addResourceItem()
            }

            FieldLabel { Layout.leftMargin: 16; text: "总体判断" }
            TextField { id: overallField; Layout.fillWidth: true; Layout.leftMargin: 16; Layout.rightMargin: 16; placeholderText: "值得 / 不值得 / 需要换方式" }

            FieldLabel { Layout.leftMargin: 16; text: "主观感受" }
            TextField { id: feelingField; Layout.fillWidth: true; Layout.leftMargin: 16; Layout.rightMargin: 16; placeholderText: "想到它时身体和心里的感觉" }

            FieldLabel { Layout.leftMargin: 16; text: "轮回测试" }
            TextField { id: nextWeekField; Layout.fillWidth: true; Layout.leftMargin: 16; Layout.rightMargin: 16; placeholderText: "如果这件事下周再来一次，我还愿意做吗？" }
            TextField { id: oneYearField; Layout.fillWidth: true; Layout.leftMargin: 16; Layout.rightMargin: 16; placeholderText: "如果这种模式持续一年，我会变成什么样？" }
            TextField { id: repeatField; Layout.fillWidth: true; Layout.leftMargin: 16; Layout.rightMargin: 16; placeholderText: "我是否愿意主动重复它？" }

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
