from PyQt5.QtWidgets import QWidget, QPlainTextEdit
from PyQt5.QtGui import QPainter, QColor, QFont, QTextFormat, QSyntaxHighlighter, QTextCharFormat, QKeyEvent
from PyQt5.QtCore import Qt, QRect, QRegExp

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaSize(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Consolas", 12))
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        self.lineNumberArea = LineNumberArea(self)
        self.setViewportMargins(self.lineNumberAreaSize(), 0, 0, 0)  # Fixed usage

        self.textChanged.connect(self.updateLineNumberArea)
        self.highlighter = PythonSyntaxHighlighter(self.document())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.contentsRect()
        self.lineNumberArea.setGeometry(rect.left(), rect.top(), self.lineNumberAreaSize(), rect.height())

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")  # Convert tab to 4 spaces
            return
        super().keyPressEvent(event)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(30, 30, 30))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top < event.rect().bottom():
            if block.isVisible():
                number = str(blockNumber + 1)
                painter.setPen(Qt.lightGray)
                painter.drawText(0, int(top), self.lineNumberArea.width() - 5, int(bottom - top),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def updateLineNumberArea(self):
        self.viewport().update()
        self.lineNumberArea.update()

    def lineNumberAreaSize(self):
        digits = len(str(max(1, self.blockCount())))
        return self.fontMetrics().horizontalAdvance("9") * digits + 10  # Ensures an integer

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlight_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff7b72"))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = [
            "def", "class", "if", "elif", "else", "for", "while", "return",
            "import", "from", "as", "with", "try", "except", "finally",
            "raise", "yield", "lambda", "global", "nonlocal"
        ]

        for word in keywords:
            pattern = QRegExp(r"\b" + word + r"\b")
            self.highlight_rules.append((pattern, keyword_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#7ec699"))
        self.highlight_rules.append((QRegExp("#[^\n]*"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlight_rules:
            expression = pattern
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)

