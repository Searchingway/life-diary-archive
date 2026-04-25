#include "ArchiveStore.h"

#include <QCoreApplication>
#include <QDate>
#include <QDateTime>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMap>
#include <QRegularExpression>
#include <QSaveFile>
#include <QStandardPaths>
#include <QUuid>

#include <algorithm>

namespace {
QString cleanTitle(const QString &value, const QString &fallback)
{
    const QString trimmed = value.trimmed();
    return trimmed.isEmpty() ? fallback : trimmed;
}

struct ZipEntry {
    QString name;
    QByteArray data;
    quint32 crc = 0;
    quint32 localOffset = 0;
    quint16 modTime = 0;
    quint16 modDate = 0;
};

void appendUInt16(QByteArray *target, quint16 value)
{
    target->append(char(value & 0xff));
    target->append(char((value >> 8) & 0xff));
}

void appendUInt32(QByteArray *target, quint32 value)
{
    target->append(char(value & 0xff));
    target->append(char((value >> 8) & 0xff));
    target->append(char((value >> 16) & 0xff));
    target->append(char((value >> 24) & 0xff));
}

quint32 crc32(const QByteArray &data)
{
    quint32 crc = 0xffffffffU;
    for (uchar byte : data) {
        crc ^= byte;
        for (int bit = 0; bit < 8; ++bit) {
            const quint32 mask = -(crc & 1U);
            crc = (crc >> 1) ^ (0xedb88320U & mask);
        }
    }
    return ~crc;
}

quint16 dosTime(const QDateTime &dateTime)
{
    const QTime time = dateTime.time();
    return quint16((time.hour() << 11) | (time.minute() << 5) | (time.second() / 2));
}

quint16 dosDate(const QDateTime &dateTime)
{
    const QDate date = dateTime.date();
    const int year = std::max(1980, date.year()) - 1980;
    return quint16((year << 9) | (date.month() << 5) | date.day());
}

bool writeZipFile(const QString &zipPath, QList<ZipEntry> entries)
{
    QByteArray output;
    const QDateTime now = QDateTime::currentDateTime();
    const quint16 modTime = dosTime(now);
    const quint16 modDate = dosDate(now);

    for (ZipEntry &entry : entries) {
        entry.crc = crc32(entry.data);
        entry.localOffset = quint32(output.size());
        entry.modTime = modTime;
        entry.modDate = modDate;

        const QByteArray name = entry.name.toUtf8();
        appendUInt32(&output, 0x04034b50U);
        appendUInt16(&output, 20);
        appendUInt16(&output, 0);
        appendUInt16(&output, 0);
        appendUInt16(&output, entry.modTime);
        appendUInt16(&output, entry.modDate);
        appendUInt32(&output, entry.crc);
        appendUInt32(&output, quint32(entry.data.size()));
        appendUInt32(&output, quint32(entry.data.size()));
        appendUInt16(&output, quint16(name.size()));
        appendUInt16(&output, 0);
        output.append(name);
        output.append(entry.data);
    }

    const quint32 centralOffset = quint32(output.size());
    for (const ZipEntry &entry : entries) {
        const QByteArray name = entry.name.toUtf8();
        appendUInt32(&output, 0x02014b50U);
        appendUInt16(&output, 20);
        appendUInt16(&output, 20);
        appendUInt16(&output, 0);
        appendUInt16(&output, 0);
        appendUInt16(&output, entry.modTime);
        appendUInt16(&output, entry.modDate);
        appendUInt32(&output, entry.crc);
        appendUInt32(&output, quint32(entry.data.size()));
        appendUInt32(&output, quint32(entry.data.size()));
        appendUInt16(&output, quint16(name.size()));
        appendUInt16(&output, 0);
        appendUInt16(&output, 0);
        appendUInt16(&output, 0);
        appendUInt16(&output, 0);
        appendUInt32(&output, 0);
        appendUInt32(&output, entry.localOffset);
        output.append(name);
    }

    const quint32 centralSize = quint32(output.size()) - centralOffset;
    appendUInt32(&output, 0x06054b50U);
    appendUInt16(&output, 0);
    appendUInt16(&output, 0);
    appendUInt16(&output, quint16(entries.size()));
    appendUInt16(&output, quint16(entries.size()));
    appendUInt32(&output, centralSize);
    appendUInt32(&output, centralOffset);
    appendUInt16(&output, 0);

    QSaveFile file(zipPath);
    if (!file.open(QIODevice::WriteOnly)) {
        return false;
    }
    file.write(output);
    return file.commit();
}

void collectFiles(const QDir &rootDir, const QDir &currentDir, const QString &folderName, QList<ZipEntry> *entries)
{
    const QFileInfoList children = currentDir.entryInfoList(
        QDir::Files | QDir::Dirs | QDir::NoDotAndDotDot,
        QDir::Name | QDir::DirsFirst);

    for (const QFileInfo &child : children) {
        if (child.isDir()) {
            collectFiles(rootDir, QDir(child.absoluteFilePath()), folderName, entries);
            continue;
        }

        QFile file(child.absoluteFilePath());
        if (!file.open(QIODevice::ReadOnly)) {
            continue;
        }

        QString relativeName = rootDir.relativeFilePath(child.absoluteFilePath());
        entries->append({
            folderName + QStringLiteral("/") + relativeName.replace(QLatin1Char('\\'), QLatin1Char('/')),
            file.readAll(),
            0,
            0,
            0,
            0,
        });
    }
}
}

ArchiveStore::ArchiveStore(QObject *parent)
    : QObject(parent)
{
    const QString overrideRoot = qEnvironmentVariable("LIFE_DIARY_DATA_ROOT");
    if (!overrideRoot.trimmed().isEmpty()) {
        m_root = QDir::fromNativeSeparators(overrideRoot.trimmed());
    } else {
        const QString appData = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
        m_root = QDir(appData).filePath(QStringLiteral("Diary"));
    }

    ensureDir(entriesPath());
    ensureDir(footprintsPath());
    ensureDir(booksPath());
    ensureDir(plansPath());
}

QString ArchiveStore::dataRoot() const
{
    return QDir::toNativeSeparators(m_root);
}

QString ArchiveStore::lastError() const
{
    return m_lastError;
}

QString ArchiveStore::toast() const
{
    return m_toast;
}

QVariantList ArchiveStore::searchDiaries(const QString &query) const
{
    QVariantList items;
    const QDir entries(entriesPath());
    for (const QFileInfo &child : entries.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot)) {
        const QVariantMap entry = loadDiaryFromDir(QDir(child.absoluteFilePath()), false);
        if (entry.isEmpty()) {
            continue;
        }
        if (!matchesAny({
                entry.value(QStringLiteral("date")).toString(),
                entry.value(QStringLiteral("title")).toString(),
                entry.value(QStringLiteral("body")).toString(),
                entry.value(QStringLiteral("imageLabels")).toString(),
            },
            query)) {
            continue;
        }
        items.append(entry);
    }
    sortDiaries(&items);
    return items;
}

QVariantMap ArchiveStore::createDiary() const
{
    const QString timestamp = nowIso();
    return {
        {QStringLiteral("id"), newId()},
        {QStringLiteral("date"), todayIso()},
        {QStringLiteral("title"), QString()},
        {QStringLiteral("body"), QString()},
        {QStringLiteral("created_at"), timestamp},
        {QStringLiteral("updated_at"), timestamp},
        {QStringLiteral("images"), QVariantList()},
        {QStringLiteral("displayTitle"), QStringLiteral("无标题日记")},
    };
}

QVariantMap ArchiveStore::getDiary(const QString &entryId) const
{
    if (entryId.trimmed().isEmpty()) {
        return {};
    }
    return loadDiaryFromDir(QDir(QDir(entriesPath()).filePath(entryId)), true);
}

QVariantMap ArchiveStore::saveDiary(const QVariantMap &payload)
{
    clearError();
    QString id = mapString(payload, QStringLiteral("id"));
    if (id.isEmpty()) {
        id = newId();
    }

    const QString entryDirPath = QDir(entriesPath()).filePath(id);
    if (!ensureDir(entryDirPath)) {
        setError(QStringLiteral("无法创建日记目录"));
        return {};
    }

    const QVariantMap existing = getDiary(id);
    const QString timestamp = nowIso();
    const QVariantList images = payload.contains(QStringLiteral("images"))
        ? readImages(payload.value(QStringLiteral("images")))
        : existing.value(QStringLiteral("images")).toList();

    QVariantMap metadata;
    metadata.insert(QStringLiteral("id"), id);
    metadata.insert(QStringLiteral("date"), mapString(payload, QStringLiteral("date"), todayIso()));
    metadata.insert(QStringLiteral("title"), mapString(payload, QStringLiteral("title")));
    metadata.insert(QStringLiteral("images"), images);
    metadata.insert(QStringLiteral("created_at"), mapString(existing, QStringLiteral("created_at"), timestamp));
    metadata.insert(QStringLiteral("updated_at"), timestamp);
    metadata.insert(QStringLiteral("body_file"), QStringLiteral("content.md"));

    const QString body = mapString(payload, QStringLiteral("body"));
    if (!writeTextFile(QDir(entryDirPath).filePath(QStringLiteral("content.md")), body)
        || !writeJsonFile(QDir(entryDirPath).filePath(QStringLiteral("entry.json")), metadata)) {
        setError(QStringLiteral("日记保存失败"));
        return {};
    }

    setToast(QStringLiteral("日记已保存"));
    emit dataChanged();
    return getDiary(id);
}

bool ArchiveStore::deleteDiary(const QString &entryId)
{
    const bool ok = softDelete(
        QDir(QDir(entriesPath()).filePath(entryId)).filePath(QStringLiteral("entry.json")),
        QStringLiteral("找不到要删除的日记"));
    if (ok) {
        setToast(QStringLiteral("日记已删除"));
        emit dataChanged();
    }
    return ok;
}

QVariantMap ArchiveStore::diaryHeatmap(int weeks) const
{
    const int safeWeeks = std::clamp(weeks, 1, 52);
    const QDate today = QDate::currentDate();
    const QDate start = today.addDays(-(safeWeeks * 7) + 1);
    QMap<QDate, int> counts;
    int total = 0;

    for (const QVariant &item : searchDiaries(QString())) {
        const QVariantMap entry = item.toMap();
        const QDate day = QDate::fromString(entry.value(QStringLiteral("date")).toString(), Qt::ISODate);
        if (!day.isValid() || day < start || day > today) {
            continue;
        }
        counts[day] += 1;
        total += 1;
    }

    const QStringList colors = {
        QStringLiteral("#EBEDF0"),
        QStringLiteral("#9BE9A8"),
        QStringLiteral("#40C463"),
        QStringLiteral("#30A14E"),
        QStringLiteral("#216E39"),
    };

    QVariantList cells;
    for (int row = 0; row < 7; ++row) {
        for (int column = 0; column < safeWeeks; ++column) {
            const QDate day = start.addDays(column * 7 + row);
            const int count = counts.value(day, 0);
            QVariantMap cell;
            cell.insert(QStringLiteral("date"), day.toString(Qt::ISODate));
            cell.insert(QStringLiteral("count"), count);
            cell.insert(QStringLiteral("color"), colors.at(std::min(count, int(colors.size()) - 1)));
            cells.append(cell);
        }
    }

    QVariantMap result;
    result.insert(QStringLiteral("weeks"), safeWeeks);
    result.insert(QStringLiteral("total"), total);
    result.insert(QStringLiteral("activeDays"), counts.size());
    result.insert(QStringLiteral("summary"), QStringLiteral("最近 %1 周共 %2 篇日记，覆盖 %3 天").arg(safeWeeks).arg(total).arg(counts.size()));
    result.insert(QStringLiteral("cells"), cells);
    return result;
}

QString ArchiveStore::exportModulePackage(const QString &module)
{
    clearError();
    const QString key = module.trimmed().toLower();
    QString folderName;
    QString title;
    QString sourcePath;

    if (key == QStringLiteral("diary")) {
        folderName = QStringLiteral("entries");
        title = QStringLiteral("日记");
        sourcePath = entriesPath();
    } else if (key == QStringLiteral("footprint")) {
        folderName = QStringLiteral("footprints");
        title = QStringLiteral("足迹");
        sourcePath = footprintsPath();
    } else if (key == QStringLiteral("book")) {
        folderName = QStringLiteral("books");
        title = QStringLiteral("读书");
        sourcePath = booksPath();
    } else {
        setError(QStringLiteral("未知导出模块"));
        return {};
    }

    const QDir sourceDir(sourcePath);
    if (!sourceDir.exists()) {
        setError(QStringLiteral("暂无可导出的%1数据").arg(title));
        return {};
    }

    QList<ZipEntry> entries;
    collectFiles(sourceDir, sourceDir, folderName, &entries);
    if (entries.isEmpty()) {
        setError(QStringLiteral("暂无可导出的%1数据").arg(title));
        return {};
    }

    if (!ensureDir(exportsPath())) {
        setError(QStringLiteral("无法创建导出目录"));
        return {};
    }

    QVariantMap manifest;
    manifest.insert(QStringLiteral("app"), QStringLiteral("life_diary"));
    manifest.insert(QStringLiteral("package_version"), 1);
    manifest.insert(QStringLiteral("module"), key);
    manifest.insert(QStringLiteral("module_title"), title);
    manifest.insert(QStringLiteral("data_directory"), folderName);
    manifest.insert(QStringLiteral("exported_at"), QDateTime::currentDateTime().toString(Qt::ISODateWithMs));
    manifest.insert(QStringLiteral("file_count"), entries.size());

    entries.prepend({
        QStringLiteral("manifest.json"),
        QJsonDocument::fromVariant(manifest).toJson(QJsonDocument::Indented),
        0,
        0,
        0,
        0,
    });

    const QString timestamp = QDateTime::currentDateTime().toString(QStringLiteral("yyyyMMdd_hhmmss"));
    QDir exportDir(exportsPath());
    QString zipPath = exportDir.filePath(QStringLiteral("life_diary_%1_%2.zip").arg(key, timestamp));
    int counter = 1;
    while (QFileInfo::exists(zipPath)) {
        zipPath = exportDir.filePath(QStringLiteral("life_diary_%1_%2_%3.zip").arg(key, timestamp).arg(counter));
        ++counter;
    }

    if (!writeZipFile(zipPath, entries)) {
        setError(QStringLiteral("压缩包导出失败"));
        return {};
    }

    const QString displayPath = QDir::toNativeSeparators(zipPath);
    setToast(QStringLiteral("%1压缩包已导出：%2").arg(title, displayPath));
    return displayPath;
}

QVariantList ArchiveStore::searchFootprints(const QString &query) const
{
    QVariantList items;
    const QDir footprints(footprintsPath());
    for (const QFileInfo &child : footprints.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot)) {
        const QVariantMap place = loadFootprintFromDir(QDir(child.absoluteFilePath()), false);
        if (place.isEmpty()) {
            continue;
        }
        QStringList haystacks = {
            place.value(QStringLiteral("place_name")).toString(),
            place.value(QStringLiteral("summary")).toString(),
            place.value(QStringLiteral("imageLabels")).toString(),
        };
        for (const QVariant &item : place.value(QStringLiteral("visits")).toList()) {
            const QVariantMap visit = item.toMap();
            haystacks << visit.value(QStringLiteral("date")).toString()
                      << visit.value(QStringLiteral("thought")).toString()
                      << visit.value(QStringLiteral("imageLabels")).toString();
        }
        if (!matchesAny(haystacks, query)) {
            continue;
        }
        items.append(place);
    }
    sortByUpdated(&items);
    return items;
}

QVariantMap ArchiveStore::createFootprint() const
{
    const QString timestamp = nowIso();
    return {
        {QStringLiteral("id"), newId()},
        {QStringLiteral("place_name"), QString()},
        {QStringLiteral("summary"), QString()},
        {QStringLiteral("created_at"), timestamp},
        {QStringLiteral("updated_at"), timestamp},
        {QStringLiteral("images"), QVariantList()},
        {QStringLiteral("visits"), QVariantList()},
        {QStringLiteral("displayTitle"), QStringLiteral("未命名地点")},
        {QStringLiteral("visitCount"), 0},
    };
}

QVariantMap ArchiveStore::getFootprint(const QString &placeId) const
{
    if (placeId.trimmed().isEmpty()) {
        return {};
    }
    return loadFootprintFromDir(QDir(QDir(footprintsPath()).filePath(placeId)), true);
}

QVariantMap ArchiveStore::saveFootprint(const QVariantMap &payload)
{
    clearError();
    QString id = mapString(payload, QStringLiteral("id"));
    if (id.isEmpty()) {
        id = newId();
    }

    const QString placeDirPath = QDir(footprintsPath()).filePath(id);
    if (!ensureDir(placeDirPath)) {
        setError(QStringLiteral("无法创建足迹目录"));
        return {};
    }

    const QVariantMap existing = getFootprint(id);
    const QString timestamp = nowIso();
    const QVariantList images = payload.contains(QStringLiteral("images"))
        ? readImages(payload.value(QStringLiteral("images")))
        : existing.value(QStringLiteral("images")).toList();
    const QVariantList visitIds = readVisitIds(existing);

    QVariantMap metadata;
    metadata.insert(QStringLiteral("id"), id);
    metadata.insert(QStringLiteral("place_name"), mapString(payload, QStringLiteral("place_name")));
    metadata.insert(QStringLiteral("images"), images);
    metadata.insert(QStringLiteral("created_at"), mapString(existing, QStringLiteral("created_at"), timestamp));
    metadata.insert(QStringLiteral("updated_at"), timestamp);
    metadata.insert(QStringLiteral("summary_file"), QStringLiteral("summary.md"));
    metadata.insert(QStringLiteral("visit_ids"), visitIds);

    const QString summary = mapString(payload, QStringLiteral("summary"));
    if (!writeTextFile(QDir(placeDirPath).filePath(QStringLiteral("summary.md")), summary)
        || !writeJsonFile(QDir(placeDirPath).filePath(QStringLiteral("footprint.json")), metadata)) {
        setError(QStringLiteral("足迹保存失败"));
        return {};
    }

    setToast(QStringLiteral("地点足迹已保存"));
    emit dataChanged();
    return getFootprint(id);
}

QVariantMap ArchiveStore::createFootprintVisit(const QString &date) const
{
    const QString timestamp = nowIso();
    return {
        {QStringLiteral("id"), newId()},
        {QStringLiteral("date"), date.trimmed().isEmpty() ? todayIso() : date.trimmed()},
        {QStringLiteral("thought"), QString()},
        {QStringLiteral("created_at"), timestamp},
        {QStringLiteral("updated_at"), timestamp},
        {QStringLiteral("related_entry_id"), QString()},
        {QStringLiteral("images"), QVariantList()},
        {QStringLiteral("displayTitle"), todayIso()},
    };
}

QVariantMap ArchiveStore::saveFootprintVisit(const QString &placeId, const QVariantMap &payload)
{
    clearError();
    if (placeId.trimmed().isEmpty()) {
        setError(QStringLiteral("请先保存地点足迹"));
        return {};
    }

    const QString placeDirPath = QDir(footprintsPath()).filePath(placeId);
    if (!QDir(placeDirPath).exists()) {
        setError(QStringLiteral("请先保存地点足迹"));
        return {};
    }

    QString id = mapString(payload, QStringLiteral("id"));
    if (id.isEmpty()) {
        id = newId();
    }

    const QString visitDirPath = QDir(QDir(placeDirPath).filePath(QStringLiteral("visits"))).filePath(id);
    if (!ensureDir(visitDirPath)) {
        setError(QStringLiteral("无法创建足迹日期目录"));
        return {};
    }

    const QVariantMap existing = loadVisitFromDir(QDir(visitDirPath));
    const QString timestamp = nowIso();
    const QVariantList images = payload.contains(QStringLiteral("images"))
        ? readImages(payload.value(QStringLiteral("images")))
        : existing.value(QStringLiteral("images")).toList();

    QVariantMap metadata;
    metadata.insert(QStringLiteral("id"), id);
    metadata.insert(QStringLiteral("date"), mapString(payload, QStringLiteral("date"), todayIso()));
    metadata.insert(QStringLiteral("images"), images);
    metadata.insert(QStringLiteral("related_entry_id"), mapString(payload, QStringLiteral("related_entry_id")));
    metadata.insert(QStringLiteral("created_at"), mapString(existing, QStringLiteral("created_at"), timestamp));
    metadata.insert(QStringLiteral("updated_at"), timestamp);
    metadata.insert(QStringLiteral("thought_file"), QStringLiteral("thought.md"));

    if (!writeTextFile(QDir(visitDirPath).filePath(QStringLiteral("thought.md")), mapString(payload, QStringLiteral("thought")))
        || !writeJsonFile(QDir(visitDirPath).filePath(QStringLiteral("visit.json")), metadata)) {
        setError(QStringLiteral("足迹日期保存失败"));
        return {};
    }

    QVariantMap placeMeta = readJsonFile(QDir(placeDirPath).filePath(QStringLiteral("footprint.json")));
    QVariantList visitIds = placeMeta.value(QStringLiteral("visit_ids")).toList();
    bool exists = false;
    for (const QVariant &item : visitIds) {
        if (item.toString() == id) {
            exists = true;
            break;
        }
    }
    if (!exists) {
        visitIds.append(id);
    }
    placeMeta.insert(QStringLiteral("visit_ids"), visitIds);
    placeMeta.insert(QStringLiteral("updated_at"), timestamp);
    writeJsonFile(QDir(placeDirPath).filePath(QStringLiteral("footprint.json")), placeMeta);

    setToast(QStringLiteral("足迹日期已保存"));
    emit dataChanged();
    return getFootprint(placeId);
}

bool ArchiveStore::deleteFootprint(const QString &placeId)
{
    const bool ok = softDelete(
        QDir(QDir(footprintsPath()).filePath(placeId)).filePath(QStringLiteral("footprint.json")),
        QStringLiteral("找不到要删除的地点足迹"));
    if (ok) {
        setToast(QStringLiteral("地点足迹已删除"));
        emit dataChanged();
    }
    return ok;
}

bool ArchiveStore::deleteFootprintVisit(const QString &placeId, const QString &visitId)
{
    clearError();
    const QString placeDirPath = QDir(footprintsPath()).filePath(placeId);
    const QString visitDirPath = QDir(QDir(placeDirPath).filePath(QStringLiteral("visits"))).filePath(visitId);
    if (!QDir(visitDirPath).exists()) {
        setError(QStringLiteral("找不到要删除的足迹日期"));
        return false;
    }

    QDir(visitDirPath).removeRecursively();

    QVariantMap placeMeta = readJsonFile(QDir(placeDirPath).filePath(QStringLiteral("footprint.json")));
    QVariantList nextIds;
    for (const QVariant &item : placeMeta.value(QStringLiteral("visit_ids")).toList()) {
        if (item.toString() != visitId) {
            nextIds.append(item.toString());
        }
    }
    placeMeta.insert(QStringLiteral("visit_ids"), nextIds);
    placeMeta.insert(QStringLiteral("updated_at"), nowIso());
    writeJsonFile(QDir(placeDirPath).filePath(QStringLiteral("footprint.json")), placeMeta);

    setToast(QStringLiteral("足迹日期已删除"));
    emit dataChanged();
    return true;
}

QVariantList ArchiveStore::searchBooks(const QString &query) const
{
    QVariantList items;
    const QDir books(booksPath());
    for (const QFileInfo &child : books.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot)) {
        const QVariantMap book = loadBookFromDir(QDir(child.absoluteFilePath()), false);
        if (book.isEmpty()) {
            continue;
        }
        if (!matchesAny({
                book.value(QStringLiteral("title")).toString(),
                book.value(QStringLiteral("author")).toString(),
                book.value(QStringLiteral("status")).toString(),
                book.value(QStringLiteral("tagsText")).toString(),
                book.value(QStringLiteral("summary")).toString(),
                book.value(QStringLiteral("notes")).toString(),
                book.value(QStringLiteral("imageLabels")).toString(),
            },
            query)) {
            continue;
        }
        items.append(book);
    }
    sortByUpdated(&items);
    return items;
}

QVariantMap ArchiveStore::createBook() const
{
    const QString timestamp = nowIso();
    return {
        {QStringLiteral("id"), newId()},
        {QStringLiteral("title"), QString()},
        {QStringLiteral("author"), QString()},
        {QStringLiteral("status"), QStringLiteral("想读")},
        {QStringLiteral("start_date"), QString()},
        {QStringLiteral("finish_date"), QString()},
        {QStringLiteral("tags"), QStringList()},
        {QStringLiteral("tagsText"), QString()},
        {QStringLiteral("summary"), QString()},
        {QStringLiteral("notes"), QString()},
        {QStringLiteral("created_at"), timestamp},
        {QStringLiteral("updated_at"), timestamp},
        {QStringLiteral("images"), QVariantList()},
        {QStringLiteral("related_diaries"), QVariantList()},
        {QStringLiteral("displayTitle"), QStringLiteral("未命名书籍")},
    };
}

QVariantMap ArchiveStore::getBook(const QString &bookId) const
{
    if (bookId.trimmed().isEmpty()) {
        return {};
    }
    return loadBookFromDir(QDir(QDir(booksPath()).filePath(bookId)), true);
}

QVariantMap ArchiveStore::saveBook(const QVariantMap &payload)
{
    clearError();
    QString id = mapString(payload, QStringLiteral("id"));
    if (id.isEmpty()) {
        id = newId();
    }

    const QString bookDirPath = QDir(booksPath()).filePath(id);
    if (!ensureDir(bookDirPath)) {
        setError(QStringLiteral("无法创建读书目录"));
        return {};
    }

    const QVariantMap existing = getBook(id);
    const QString timestamp = nowIso();
    const QVariantList images = payload.contains(QStringLiteral("images"))
        ? readImages(payload.value(QStringLiteral("images")))
        : existing.value(QStringLiteral("images")).toList();
    const QVariantList related = payload.contains(QStringLiteral("related_diaries"))
        ? readRelatedDiaries(payload.value(QStringLiteral("related_diaries")))
        : existing.value(QStringLiteral("related_diaries")).toList();
    const QStringList tags = readTags(payload.contains(QStringLiteral("tags"))
        ? payload.value(QStringLiteral("tags"))
        : payload.value(QStringLiteral("tagsText")));

    QVariantMap metadata;
    metadata.insert(QStringLiteral("id"), id);
    metadata.insert(QStringLiteral("title"), mapString(payload, QStringLiteral("title")));
    metadata.insert(QStringLiteral("author"), mapString(payload, QStringLiteral("author")));
    metadata.insert(QStringLiteral("status"), mapString(payload, QStringLiteral("status"), QStringLiteral("想读")));
    metadata.insert(QStringLiteral("start_date"), mapString(payload, QStringLiteral("start_date")));
    metadata.insert(QStringLiteral("finish_date"), mapString(payload, QStringLiteral("finish_date")));
    metadata.insert(QStringLiteral("tags"), tags);
    metadata.insert(QStringLiteral("images"), images);
    metadata.insert(QStringLiteral("related_diaries"), related);
    metadata.insert(QStringLiteral("created_at"), mapString(existing, QStringLiteral("created_at"), timestamp));
    metadata.insert(QStringLiteral("updated_at"), timestamp);
    metadata.insert(QStringLiteral("summary_file"), QStringLiteral("summary.md"));
    metadata.insert(QStringLiteral("notes_file"), QStringLiteral("notes.md"));

    if (!writeTextFile(QDir(bookDirPath).filePath(QStringLiteral("summary.md")), mapString(payload, QStringLiteral("summary")))
        || !writeTextFile(QDir(bookDirPath).filePath(QStringLiteral("notes.md")), mapString(payload, QStringLiteral("notes")))
        || !writeJsonFile(QDir(bookDirPath).filePath(QStringLiteral("book.json")), metadata)) {
        setError(QStringLiteral("读书笔记保存失败"));
        return {};
    }

    setToast(QStringLiteral("读书笔记已保存"));
    emit dataChanged();
    return getBook(id);
}

bool ArchiveStore::deleteBook(const QString &bookId)
{
    const bool ok = softDelete(
        QDir(QDir(booksPath()).filePath(bookId)).filePath(QStringLiteral("book.json")),
        QStringLiteral("找不到要删除的读书笔记"));
    if (ok) {
        setToast(QStringLiteral("读书笔记已删除"));
        emit dataChanged();
    }
    return ok;
}

QVariantList ArchiveStore::searchPlans(const QString &query) const
{
    QVariantList items;
    const QDir plans(plansPath());
    for (const QFileInfo &child : plans.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot)) {
        const QVariantMap plan = loadPlanFromDir(QDir(child.absoluteFilePath()), false);
        if (plan.isEmpty()) {
            continue;
        }
        if (!matchesAny({
                plan.value(QStringLiteral("title")).toString(),
                plan.value(QStringLiteral("due_date")).toString(),
                plan.value(QStringLiteral("status")).toString(),
                plan.value(QStringLiteral("priority")).toString(),
                plan.value(QStringLiteral("notes")).toString(),
            },
            query)) {
            continue;
        }
        items.append(plan);
    }
    sortPlans(&items);
    return items;
}

QVariantMap ArchiveStore::createPlan() const
{
    const QString timestamp = nowIso();
    return {
        {QStringLiteral("id"), newId()},
        {QStringLiteral("title"), QString()},
        {QStringLiteral("due_date"), todayIso()},
        {QStringLiteral("status"), QStringLiteral("未开始")},
        {QStringLiteral("priority"), QStringLiteral("普通")},
        {QStringLiteral("notes"), QString()},
        {QStringLiteral("created_at"), timestamp},
        {QStringLiteral("updated_at"), timestamp},
        {QStringLiteral("displayTitle"), QStringLiteral("未命名计划")},
    };
}

QVariantMap ArchiveStore::getPlan(const QString &planId) const
{
    if (planId.trimmed().isEmpty()) {
        return {};
    }
    return loadPlanFromDir(QDir(QDir(plansPath()).filePath(planId)), true);
}

QVariantMap ArchiveStore::savePlan(const QVariantMap &payload)
{
    clearError();
    QString id = mapString(payload, QStringLiteral("id"));
    if (id.isEmpty()) {
        id = newId();
    }

    const QString planDirPath = QDir(plansPath()).filePath(id);
    if (!ensureDir(planDirPath)) {
        setError(QStringLiteral("无法创建轻计划目录"));
        return {};
    }

    const QVariantMap existing = getPlan(id);
    const QString timestamp = nowIso();
    QVariantMap metadata;
    metadata.insert(QStringLiteral("id"), id);
    metadata.insert(QStringLiteral("title"), mapString(payload, QStringLiteral("title")));
    metadata.insert(QStringLiteral("due_date"), mapString(payload, QStringLiteral("due_date"), todayIso()));
    metadata.insert(QStringLiteral("status"), mapString(payload, QStringLiteral("status"), QStringLiteral("未开始")));
    metadata.insert(QStringLiteral("priority"), mapString(payload, QStringLiteral("priority"), QStringLiteral("普通")));
    metadata.insert(QStringLiteral("notes"), mapString(payload, QStringLiteral("notes")));
    metadata.insert(QStringLiteral("created_at"), mapString(existing, QStringLiteral("created_at"), timestamp));
    metadata.insert(QStringLiteral("updated_at"), timestamp);

    if (!writeJsonFile(QDir(planDirPath).filePath(QStringLiteral("plan.json")), metadata)) {
        setError(QStringLiteral("轻计划保存失败"));
        return {};
    }

    setToast(QStringLiteral("轻计划已保存"));
    emit dataChanged();
    return getPlan(id);
}

bool ArchiveStore::deletePlan(const QString &planId)
{
    const bool ok = softDelete(
        QDir(QDir(plansPath()).filePath(planId)).filePath(QStringLiteral("plan.json")),
        QStringLiteral("找不到要删除的轻计划"));
    if (ok) {
        setToast(QStringLiteral("轻计划已删除"));
        emit dataChanged();
    }
    return ok;
}

QString ArchiveStore::entriesPath() const
{
    return QDir(m_root).filePath(QStringLiteral("entries"));
}

QString ArchiveStore::footprintsPath() const
{
    return QDir(m_root).filePath(QStringLiteral("footprints"));
}

QString ArchiveStore::booksPath() const
{
    return QDir(m_root).filePath(QStringLiteral("books"));
}

QString ArchiveStore::plansPath() const
{
    return QDir(m_root).filePath(QStringLiteral("plans"));
}

QString ArchiveStore::exportsPath() const
{
    return QDir(m_root).filePath(QStringLiteral("exports"));
}

QVariantMap ArchiveStore::loadDiaryFromDir(const QDir &entryDir, bool includeDeleted) const
{
    bool ok = false;
    QVariantMap data = readJsonFile(entryDir.filePath(QStringLiteral("entry.json")), &ok);
    if (!ok) {
        return {};
    }
    if (data.value(QStringLiteral("deleted")).toBool() && !includeDeleted) {
        return {};
    }

    const QString bodyFile = mapString(data, QStringLiteral("body_file"), QStringLiteral("content.md"));
    const QString body = readTextFile(entryDir.filePath(bodyFile));
    QVariantList images = readImages(data.value(QStringLiteral("images")));

    QStringList labels;
    for (const QVariant &image : images) {
        labels << image.toMap().value(QStringLiteral("label")).toString();
    }

    QVariantMap entry;
    entry.insert(QStringLiteral("id"), mapString(data, QStringLiteral("id"), entryDir.dirName()));
    entry.insert(QStringLiteral("date"), mapString(data, QStringLiteral("date")));
    entry.insert(QStringLiteral("title"), mapString(data, QStringLiteral("title")));
    entry.insert(QStringLiteral("body"), body);
    entry.insert(QStringLiteral("created_at"), mapString(data, QStringLiteral("created_at")));
    entry.insert(QStringLiteral("updated_at"), mapString(data, QStringLiteral("updated_at")));
    entry.insert(QStringLiteral("images"), images);
    entry.insert(QStringLiteral("imageLabels"), labels.join(QLatin1Char(' ')));
    entry.insert(QStringLiteral("displayTitle"), cleanTitle(entry.value(QStringLiteral("title")).toString(), QStringLiteral("无标题日记")));
    return entry;
}

QVariantMap ArchiveStore::loadFootprintFromDir(const QDir &placeDir, bool includeDeleted) const
{
    bool ok = false;
    QVariantMap data = readJsonFile(placeDir.filePath(QStringLiteral("footprint.json")), &ok);
    if (!ok) {
        return {};
    }
    if (data.value(QStringLiteral("deleted")).toBool() && !includeDeleted) {
        return {};
    }

    QString summary;
    QVariantList visits;
    if (!data.contains(QStringLiteral("visit_ids")) && !data.contains(QStringLiteral("summary_file"))) {
        summary = QString();
        const QString thought = readTextFile(placeDir.filePath(QStringLiteral("thought.md")));
        QVariantMap visit;
        visit.insert(QStringLiteral("id"), QStringLiteral("%1_legacy").arg(mapString(data, QStringLiteral("id"), placeDir.dirName())));
        visit.insert(QStringLiteral("date"), mapString(data, QStringLiteral("date")));
        visit.insert(QStringLiteral("thought"), thought);
        visit.insert(QStringLiteral("created_at"), mapString(data, QStringLiteral("created_at")));
        visit.insert(QStringLiteral("updated_at"), mapString(data, QStringLiteral("updated_at")));
        visit.insert(QStringLiteral("related_entry_id"), mapString(data, QStringLiteral("related_entry_id")));
        visit.insert(QStringLiteral("images"), readImages(data.value(QStringLiteral("images"))));
        visit.insert(QStringLiteral("displayTitle"), cleanTitle(visit.value(QStringLiteral("date")).toString(), QStringLiteral("未设日期关联")));
        visits.append(visit);
    } else {
        const QString summaryFile = mapString(data, QStringLiteral("summary_file"), QStringLiteral("summary.md"));
        summary = readTextFile(placeDir.filePath(summaryFile));
        const QDir visitsDir(placeDir.filePath(QStringLiteral("visits")));
        for (const QVariant &visitIdValue : data.value(QStringLiteral("visit_ids")).toList()) {
            const QVariantMap visit = loadVisitFromDir(QDir(visitsDir.filePath(visitIdValue.toString())));
            if (!visit.isEmpty()) {
                visits.append(visit);
            }
        }
    }

    std::sort(visits.begin(), visits.end(), [](const QVariant &left, const QVariant &right) {
        const QVariantMap a = left.toMap();
        const QVariantMap b = right.toMap();
        const QString keyA = a.value(QStringLiteral("date")).toString() + a.value(QStringLiteral("updated_at")).toString();
        const QString keyB = b.value(QStringLiteral("date")).toString() + b.value(QStringLiteral("updated_at")).toString();
        return keyA > keyB;
    });

    QVariantList images = readImages(data.value(QStringLiteral("images")));
    QStringList labels;
    for (const QVariant &image : images) {
        labels << image.toMap().value(QStringLiteral("label")).toString();
    }

    QString latestVisitDate;
    if (!visits.isEmpty()) {
        latestVisitDate = visits.first().toMap().value(QStringLiteral("date")).toString();
    }

    QVariantMap place;
    place.insert(QStringLiteral("id"), mapString(data, QStringLiteral("id"), placeDir.dirName()));
    place.insert(QStringLiteral("place_name"), mapString(data, QStringLiteral("place_name")));
    place.insert(QStringLiteral("summary"), summary);
    place.insert(QStringLiteral("created_at"), mapString(data, QStringLiteral("created_at")));
    place.insert(QStringLiteral("updated_at"), mapString(data, QStringLiteral("updated_at")));
    place.insert(QStringLiteral("images"), images);
    place.insert(QStringLiteral("imageLabels"), labels.join(QLatin1Char(' ')));
    place.insert(QStringLiteral("visits"), visits);
    place.insert(QStringLiteral("visitCount"), visits.size());
    place.insert(QStringLiteral("latestVisitDate"), latestVisitDate);
    place.insert(QStringLiteral("displayTitle"), cleanTitle(place.value(QStringLiteral("place_name")).toString(), QStringLiteral("未命名地点")));
    return place;
}

QVariantMap ArchiveStore::loadVisitFromDir(const QDir &visitDir) const
{
    bool ok = false;
    QVariantMap data = readJsonFile(visitDir.filePath(QStringLiteral("visit.json")), &ok);
    if (!ok) {
        return {};
    }

    const QString thoughtFile = mapString(data, QStringLiteral("thought_file"), QStringLiteral("thought.md"));
    QVariantList images = readImages(data.value(QStringLiteral("images")));
    QStringList labels;
    for (const QVariant &image : images) {
        labels << image.toMap().value(QStringLiteral("label")).toString();
    }

    QVariantMap visit;
    visit.insert(QStringLiteral("id"), mapString(data, QStringLiteral("id"), visitDir.dirName()));
    visit.insert(QStringLiteral("date"), mapString(data, QStringLiteral("date")));
    visit.insert(QStringLiteral("thought"), readTextFile(visitDir.filePath(thoughtFile)));
    visit.insert(QStringLiteral("created_at"), mapString(data, QStringLiteral("created_at")));
    visit.insert(QStringLiteral("updated_at"), mapString(data, QStringLiteral("updated_at")));
    visit.insert(QStringLiteral("related_entry_id"), mapString(data, QStringLiteral("related_entry_id")));
    visit.insert(QStringLiteral("images"), images);
    visit.insert(QStringLiteral("imageLabels"), labels.join(QLatin1Char(' ')));
    visit.insert(QStringLiteral("displayTitle"), cleanTitle(visit.value(QStringLiteral("date")).toString(), QStringLiteral("未设日期关联")));
    return visit;
}

QVariantMap ArchiveStore::loadBookFromDir(const QDir &bookDir, bool includeDeleted) const
{
    bool ok = false;
    QVariantMap data = readJsonFile(bookDir.filePath(QStringLiteral("book.json")), &ok);
    if (!ok) {
        return {};
    }
    if (data.value(QStringLiteral("deleted")).toBool() && !includeDeleted) {
        return {};
    }

    const QString summaryFile = mapString(data, QStringLiteral("summary_file"), QStringLiteral("summary.md"));
    const QString notesFile = mapString(data, QStringLiteral("notes_file"), QStringLiteral("notes.md"));
    const QStringList tags = readTags(data.value(QStringLiteral("tags")));
    QVariantList images = readImages(data.value(QStringLiteral("images")));

    QStringList labels;
    for (const QVariant &image : images) {
        labels << image.toMap().value(QStringLiteral("label")).toString();
    }

    QVariantMap book;
    book.insert(QStringLiteral("id"), mapString(data, QStringLiteral("id"), bookDir.dirName()));
    book.insert(QStringLiteral("title"), mapString(data, QStringLiteral("title")));
    book.insert(QStringLiteral("author"), mapString(data, QStringLiteral("author")));
    book.insert(QStringLiteral("status"), mapString(data, QStringLiteral("status"), QStringLiteral("想读")));
    book.insert(QStringLiteral("start_date"), mapString(data, QStringLiteral("start_date")));
    book.insert(QStringLiteral("finish_date"), mapString(data, QStringLiteral("finish_date")));
    book.insert(QStringLiteral("tags"), tags);
    book.insert(QStringLiteral("tagsText"), tags.join(QStringLiteral(", ")));
    book.insert(QStringLiteral("summary"), readTextFile(bookDir.filePath(summaryFile)));
    book.insert(QStringLiteral("notes"), readTextFile(bookDir.filePath(notesFile)));
    book.insert(QStringLiteral("created_at"), mapString(data, QStringLiteral("created_at")));
    book.insert(QStringLiteral("updated_at"), mapString(data, QStringLiteral("updated_at")));
    book.insert(QStringLiteral("images"), images);
    book.insert(QStringLiteral("imageLabels"), labels.join(QLatin1Char(' ')));
    book.insert(QStringLiteral("related_diaries"), readRelatedDiaries(data.value(QStringLiteral("related_diaries"))));
    book.insert(QStringLiteral("displayTitle"), cleanTitle(book.value(QStringLiteral("title")).toString(), QStringLiteral("未命名书籍")));
    return book;
}

QVariantMap ArchiveStore::loadPlanFromDir(const QDir &planDir, bool includeDeleted) const
{
    bool ok = false;
    QVariantMap data = readJsonFile(planDir.filePath(QStringLiteral("plan.json")), &ok);
    if (!ok) {
        return {};
    }
    if (data.value(QStringLiteral("deleted")).toBool() && !includeDeleted) {
        return {};
    }

    const QString title = mapString(data, QStringLiteral("title"));
    const QString dueDate = mapString(data, QStringLiteral("due_date"), mapString(data, QStringLiteral("date"), todayIso()));
    QString status = mapString(data, QStringLiteral("status"));
    if (status.isEmpty()) {
        status = data.value(QStringLiteral("completed")).toString().trimmed().isEmpty()
            ? QStringLiteral("未开始")
            : QStringLiteral("进行中");
    }
    const QString priority = mapString(data, QStringLiteral("priority"), QStringLiteral("普通"));
    QString notes = mapString(data, QStringLiteral("notes"));
    if (notes.isEmpty()) {
        QStringList legacyParts;
        const QString completed = mapString(data, QStringLiteral("completed"));
        const QString missed = mapString(data, QStringLiteral("missed"));
        const QString tomorrow = mapString(data, QStringLiteral("tomorrow_top3"));
        const QString longTerm = mapString(data, QStringLiteral("long_term"));
        if (!completed.trimmed().isEmpty()) {
            legacyParts << QStringLiteral("今天完成了什么：\n%1").arg(completed);
        }
        if (!missed.trimmed().isEmpty()) {
            legacyParts << QStringLiteral("今天没完成什么：\n%1").arg(missed);
        }
        if (!tomorrow.trimmed().isEmpty()) {
            legacyParts << QStringLiteral("明天最重要的三件事：\n%1").arg(tomorrow);
        }
        if (!longTerm.trimmed().isEmpty()) {
            legacyParts << QStringLiteral("长期推进事项：\n%1").arg(longTerm);
        }
        notes = legacyParts.join(QStringLiteral("\n\n"));
    }

    QVariantMap plan;
    plan.insert(QStringLiteral("id"), mapString(data, QStringLiteral("id"), planDir.dirName()));
    plan.insert(QStringLiteral("title"), title);
    plan.insert(QStringLiteral("due_date"), dueDate);
    plan.insert(QStringLiteral("status"), status);
    plan.insert(QStringLiteral("priority"), priority);
    plan.insert(QStringLiteral("notes"), notes);
    plan.insert(QStringLiteral("created_at"), mapString(data, QStringLiteral("created_at")));
    plan.insert(QStringLiteral("updated_at"), mapString(data, QStringLiteral("updated_at")));
    plan.insert(QStringLiteral("displayTitle"), cleanTitle(title, QStringLiteral("未命名计划")));
    return plan;
}

bool ArchiveStore::writeJsonFile(const QString &path, const QVariantMap &value)
{
    QSaveFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        return false;
    }
    const QJsonDocument document = QJsonDocument::fromVariant(value);
    file.write(document.toJson(QJsonDocument::Indented));
    return file.commit();
}

QVariantMap ArchiveStore::readJsonFile(const QString &path, bool *ok) const
{
    if (ok) {
        *ok = false;
    }
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        return {};
    }
    const QJsonDocument document = QJsonDocument::fromJson(file.readAll());
    if (!document.isObject()) {
        return {};
    }
    if (ok) {
        *ok = true;
    }
    return document.object().toVariantMap();
}

QString ArchiveStore::readTextFile(const QString &path) const
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        return {};
    }
    return QString::fromUtf8(file.readAll());
}

bool ArchiveStore::writeTextFile(const QString &path, const QString &value)
{
    QSaveFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        return false;
    }
    file.write(value.toUtf8());
    return file.commit();
}

bool ArchiveStore::ensureDir(const QString &path) const
{
    QDir dir(path);
    return dir.exists() || dir.mkpath(QStringLiteral("."));
}

bool ArchiveStore::softDelete(const QString &jsonPath, const QString &missingMessage)
{
    clearError();
    bool ok = false;
    QVariantMap data = readJsonFile(jsonPath, &ok);
    if (!ok) {
        setError(missingMessage);
        return false;
    }
    const QString timestamp = nowIso();
    data.insert(QStringLiteral("deleted"), true);
    data.insert(QStringLiteral("deleted_at"), timestamp);
    data.insert(QStringLiteral("updated_at"), timestamp);
    if (!writeJsonFile(jsonPath, data)) {
        setError(QStringLiteral("删除标记写入失败"));
        return false;
    }
    return true;
}

QVariantList ArchiveStore::readImages(const QVariant &value) const
{
    QVariantList images;
    for (const QVariant &item : value.toList()) {
        QVariantMap image;
        if (item.canConvert<QString>() && item.typeId() == QMetaType::QString) {
            image.insert(QStringLiteral("file_name"), item.toString());
            image.insert(QStringLiteral("label"), QString());
        } else {
            const QVariantMap raw = item.toMap();
            image.insert(QStringLiteral("file_name"), raw.value(QStringLiteral("file_name")).toString());
            image.insert(QStringLiteral("label"), raw.value(QStringLiteral("label")).toString());
        }
        if (!image.value(QStringLiteral("file_name")).toString().trimmed().isEmpty()) {
            images.append(image);
        }
    }
    return images;
}

QVariantList ArchiveStore::readRelatedDiaries(const QVariant &value) const
{
    QVariantList items;
    for (const QVariant &item : value.toList()) {
        const QVariantMap raw = item.toMap();
        QVariantMap related;
        related.insert(QStringLiteral("entry_id"), raw.value(QStringLiteral("entry_id")).toString());
        related.insert(QStringLiteral("date"), raw.value(QStringLiteral("date")).toString());
        related.insert(QStringLiteral("title"), raw.value(QStringLiteral("title")).toString());
        related.insert(
            QStringLiteral("displayTitle"),
            QStringLiteral("%1 | %2").arg(
                related.value(QStringLiteral("date")).toString(),
                cleanTitle(related.value(QStringLiteral("title")).toString(), QStringLiteral("无标题日记"))));
        if (!related.value(QStringLiteral("entry_id")).toString().isEmpty()) {
            items.append(related);
        }
    }
    return items;
}

QStringList ArchiveStore::readTags(const QVariant &value) const
{
    QStringList tags;
    if (value.typeId() == QMetaType::QString) {
        for (const QString &part : value.toString().split(QRegularExpression(QStringLiteral("[,，]")), Qt::SkipEmptyParts)) {
            const QString tag = part.trimmed();
            if (!tag.isEmpty()) {
                tags << tag;
            }
        }
        return tags;
    }

    for (const QVariant &item : value.toList()) {
        const QString tag = item.toString().trimmed();
        if (!tag.isEmpty()) {
            tags << tag;
        }
    }
    return tags;
}

QVariantList ArchiveStore::readVisitIds(const QVariantMap &place) const
{
    QVariantList visitIds;
    for (const QVariant &item : place.value(QStringLiteral("visits")).toList()) {
        const QString id = item.toMap().value(QStringLiteral("id")).toString();
        if (!id.isEmpty()) {
            visitIds.append(id);
        }
    }
    return visitIds;
}

QString ArchiveStore::nowIso() const
{
    return QDateTime::currentDateTime().toString(Qt::ISODateWithMs);
}

QString ArchiveStore::newId() const
{
    return QUuid::createUuid().toString(QUuid::Id128);
}

QString ArchiveStore::todayIso() const
{
    return QDate::currentDate().toString(Qt::ISODate);
}

QString ArchiveStore::mapString(const QVariantMap &map, const QString &key, const QString &fallback) const
{
    const QVariant value = map.value(key);
    if (!value.isValid() || value.isNull()) {
        return fallback;
    }
    return value.toString();
}

bool ArchiveStore::matchesAny(const QStringList &haystacks, const QString &query) const
{
    const QString keyword = query.trimmed().toLower();
    if (keyword.isEmpty()) {
        return true;
    }
    for (const QString &text : haystacks) {
        if (text.toLower().contains(keyword)) {
            return true;
        }
    }
    return false;
}

void ArchiveStore::sortByUpdated(QVariantList *items) const
{
    std::sort(items->begin(), items->end(), [](const QVariant &left, const QVariant &right) {
        const QVariantMap a = left.toMap();
        const QVariantMap b = right.toMap();
        const QString keyA = a.value(QStringLiteral("updated_at")).toString()
            + a.value(QStringLiteral("created_at")).toString()
            + a.value(QStringLiteral("displayTitle")).toString().toLower();
        const QString keyB = b.value(QStringLiteral("updated_at")).toString()
            + b.value(QStringLiteral("created_at")).toString()
            + b.value(QStringLiteral("displayTitle")).toString().toLower();
        return keyA > keyB;
    });
}

void ArchiveStore::sortDiaries(QVariantList *items) const
{
    std::sort(items->begin(), items->end(), [](const QVariant &left, const QVariant &right) {
        const QVariantMap a = left.toMap();
        const QVariantMap b = right.toMap();
        const QString keyA = a.value(QStringLiteral("date")).toString()
            + a.value(QStringLiteral("updated_at")).toString()
            + a.value(QStringLiteral("created_at")).toString();
        const QString keyB = b.value(QStringLiteral("date")).toString()
            + b.value(QStringLiteral("updated_at")).toString()
            + b.value(QStringLiteral("created_at")).toString();
        return keyA > keyB;
    });
}

void ArchiveStore::sortPlans(QVariantList *items) const
{
    const QMap<QString, int> statusOrder = {
        {QStringLiteral("进行中"), 0},
        {QStringLiteral("未开始"), 1},
        {QStringLiteral("搁置"), 2},
        {QStringLiteral("已完成"), 3},
    };

    std::sort(items->begin(), items->end(), [&statusOrder](const QVariant &left, const QVariant &right) {
        const QVariantMap a = left.toMap();
        const QVariantMap b = right.toMap();
        const int orderA = statusOrder.value(a.value(QStringLiteral("status")).toString(), 9);
        const int orderB = statusOrder.value(b.value(QStringLiteral("status")).toString(), 9);
        if (orderA != orderB) {
            return orderA < orderB;
        }

        const QString keyA = a.value(QStringLiteral("due_date")).toString()
            + a.value(QStringLiteral("updated_at")).toString()
            + a.value(QStringLiteral("displayTitle")).toString().toLower();
        const QString keyB = b.value(QStringLiteral("due_date")).toString()
            + b.value(QStringLiteral("updated_at")).toString()
            + b.value(QStringLiteral("displayTitle")).toString().toLower();
        return keyA < keyB;
    });
}

void ArchiveStore::setError(const QString &message)
{
    if (m_lastError == message) {
        return;
    }
    m_lastError = message;
    emit lastErrorChanged();
}

void ArchiveStore::setToast(const QString &message)
{
    m_toast = message;
    emit toastChanged();
}

void ArchiveStore::clearError()
{
    setError(QString());
}
