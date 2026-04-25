import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: page

    property var planItems: []
    property string currentPlanId: ""
    property var statusOptions: ["未开始", "进行中", "已完成", "搁置"]
    property var priorityOptions: ["低", "普通", "高"]

    background: Rectangle { color: "#F6F7F3" }

    function refresh() {
        planItems = archiveStore.searchPlans(searchField.text)
    }

    function setComboText(combo, options, value, fallbackIndex) {
        const idx = options.indexOf(value)
        combo.currentIndex = idx >= 0 ? idx : fallbackIndex
    }

    function startNew() {
        const plan = archiveStore.createPlan()
        currentPlanId = plan.id
        titleField.text = plan.title
        dueDateField.text = plan.due_date
        setComboText(statusBox, statusOptions, plan.status, 0)
        setComboText(priorityBox, priorityOptions, plan.priority, 1)
        notesField.text = plan.notes
    }

    function loadPlan(planId) {
        const plan = archiveStore.getPlan(planId)
        if (!plan || !plan.id) {
            return
        }
        currentPlanId = plan.id
        titleField.text = plan.title
        dueDateField.text = plan.due_date
        setComboText(statusBox, statusOptions, plan.status, 0)
        setComboText(priorityBox, priorityOptions, plan.priority, 1)
        notesField.text = plan.notes
    }

    function saveCurrent() {
        const saved = archiveStore.savePlan({
            "id": currentPlanId,
            "title": titleField.text,
            "due_date": dueDateField.text,
            "status": statusBox.currentText,
            "priority": priorityBox.currentText,
            "notes": notesField.text
        })
        if (saved && saved.id) {
            currentPlanId = saved.id
            refresh()
        }
    }

    function markDone() {
        setComboText(statusBox, statusOptions, "已完成", 2)
        saveCurrent()
    }

    Component.onCompleted: {
        refresh()
        if (planItems.length > 0) {
            loadPlan(planItems[0].id)
        } else {
            startNew()
        }
    }

    Connections {
        target: archiveStore
        function onDataChanged() {
            refresh()
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
                spacing: 10

                SectionTitle {
                    Layout.fillWidth: true
                    text: "轻计划"
                }

                Button {
                    text: "新建"
                    onClicked: startNew()
                }
            }

            TextField {
                id: searchField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "搜索标题、日期、状态、备注"
                onTextChanged: refresh()
            }

            ListView {
                id: planList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                height: planItems.length === 0 ? 88 : Math.min(310, planItems.length * 84)
                spacing: 8
                clip: true
                model: planItems

                delegate: RecordCard {
                    width: planList.width
                    title: modelData.displayTitle
                    subtitle: modelData.due_date + " | " + modelData.status + " | " + modelData.priority
                    meta: modelData.notes
                    selected: modelData.id === currentPlanId
                    onClicked: loadPlan(modelData.id)
                }
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "计划"
            }

            TextField {
                id: titleField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "例如：整理四月照片、周末读完两章"
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "日期"
            }

            TextField {
                id: dueDateField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                inputMethodHints: Qt.ImhDate
                placeholderText: "2026-04-24"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    FieldLabel { text: "状态" }

                    ComboBox {
                        id: statusBox
                        Layout.fillWidth: true
                        model: page.statusOptions
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    FieldLabel { text: "优先级" }

                    ComboBox {
                        id: priorityBox
                        Layout.fillWidth: true
                        model: page.priorityOptions
                    }
                }
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "备注"
            }

            TextArea {
                id: notesField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 380
                wrapMode: TextEdit.Wrap
                placeholderText: "这里写轻量计划，不做复杂项目管理，只记录下一步。"
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                spacing: 10

                Button {
                    Layout.fillWidth: true
                    text: "保存"
                    highlighted: true
                    onClicked: saveCurrent()
                }

                Button {
                    Layout.fillWidth: true
                    text: "完成"
                    enabled: currentPlanId.length > 0
                    onClicked: markDone()
                }

                Button {
                    Layout.fillWidth: true
                    text: "删除"
                    enabled: currentPlanId.length > 0
                    onClicked: {
                        if (archiveStore.deletePlan(currentPlanId)) {
                            refresh()
                            if (planItems.length > 0) {
                                loadPlan(planItems[0].id)
                            } else {
                                startNew()
                            }
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 18 }
        }
    }
}
