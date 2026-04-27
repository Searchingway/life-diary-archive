import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: page

    property var bookItems: []
    property var bookImages: []
    property string currentBookId: ""

    background: Rectangle { color: "#F6F7F3" }

    function refresh() {
        bookItems = archiveStore.searchBooks(searchField.text)
    }

    function startNew() {
        const book = archiveStore.createBook()
        currentBookId = book.id
        titleField.text = book.title
        authorField.text = book.author
        statusBox.currentIndex = 0
        startDateField.text = book.start_date
        finishDateField.text = book.finish_date
        tagsField.text = book.tagsText
        summaryField.text = book.summary
        notesField.text = book.notes
        setBookImages(book.images || [])
    }

    function loadBook(bookId) {
        const book = archiveStore.getBook(bookId)
        if (!book || !book.id) {
            return
        }
        currentBookId = book.id
        titleField.text = book.title
        authorField.text = book.author
        const idx = statusBox.model.indexOf(book.status)
        statusBox.currentIndex = idx >= 0 ? idx : 0
        startDateField.text = book.start_date
        finishDateField.text = book.finish_date
        tagsField.text = book.tagsText
        summaryField.text = book.summary
        notesField.text = book.notes
        setBookImages(book.images || [])
    }

    function saveCurrent() {
        const saved = archiveStore.saveBook({
            "id": currentBookId,
            "title": titleField.text,
            "author": authorField.text,
            "status": statusBox.currentText,
            "start_date": startDateField.text,
            "finish_date": finishDateField.text,
            "tagsText": tagsField.text,
            "summary": summaryField.text,
            "notes": notesField.text,
            "images": bookImages
        })
        if (saved && saved.id) {
            currentBookId = saved.id
            setBookImages(saved.images || [])
            refresh()
        }
    }

    function setBookImages(images) {
        bookImages = images || []
        if (typeof bookImagePanel !== "undefined" && bookImagePanel !== null) {
            bookImagePanel.setImages(bookImages)
        }
    }

    Component.onCompleted: {
        refresh()
        if (bookItems.length > 0) {
            loadBook(bookItems[0].id)
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
                    text: "读书"
                }

                Button {
                    text: "新建"
                    onClicked: startNew()
                }

                Button {
                    text: "导出包"
                    onClicked: archiveStore.exportModulePackage("book")
                }
            }

            TextField {
                id: searchField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "搜索书名、作者、标签、笔记"
                onTextChanged: refresh()
            }

            ListView {
                id: bookList
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: bookItems.length === 0 ? 88 : Math.min(310, bookItems.length * 84)
                spacing: 8
                clip: true
                model: bookItems

                delegate: RecordCard {
                    width: bookList.width
                    title: modelData.displayTitle
                    subtitle: modelData.author
                    meta: modelData.status + (modelData.tagsText ? " | " + modelData.tagsText : "")
                    selected: modelData.id === currentBookId
                    onClicked: loadBook(modelData.id)
                }
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "书名"
            }

            TextField {
                id: titleField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "正在读什么"
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "作者"
            }

            TextField {
                id: authorField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "作者"
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
                        model: ["想读", "在读", "读完"]
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    FieldLabel { text: "开始" }

                    TextField {
                        id: startDateField
                        Layout.fillWidth: true
                        inputMethodHints: Qt.ImhDate
                        placeholderText: "开始日期"
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    FieldLabel { text: "完成" }

                    TextField {
                        id: finishDateField
                        Layout.fillWidth: true
                        inputMethodHints: Qt.ImhDate
                        placeholderText: "完成日期"
                    }
                }
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "标签"
            }

            TextField {
                id: tagsField
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                placeholderText: "用逗号分隔"
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "阅读摘要"
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 160
                clip: true

                TextArea {
                    id: summaryField
                    wrapMode: TextEdit.Wrap
                    placeholderText: "这本书讲了什么"
                }
            }

            FieldLabel {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                text: "读书笔记"
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.preferredHeight: 340
                clip: true

                TextArea {
                    id: notesField
                    wrapMode: TextEdit.Wrap
                    placeholderText: "书和你发生了什么关系"
                }
            }

            ImageListEditor {
                id: bookImagePanel
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                title: "书封 / 书籍图片"
                scope: "book"
                primaryId: page.currentBookId
                emptyText: "还没有给这本书插入图片"
                addButtonText: "添加书封/图片"
                onImagesUpdated: function(images) {
                    page.bookImages = images
                }
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
                    text: "删除"
                    enabled: currentBookId.length > 0
                    onClicked: {
                        if (archiveStore.deleteBook(currentBookId)) {
                            refresh()
                            if (bookItems.length > 0) {
                                loadBook(bookItems[0].id)
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
