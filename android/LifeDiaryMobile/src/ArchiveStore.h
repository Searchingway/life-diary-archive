#pragma once

#include <QObject>
#include <QUrl>
#include <QVariantList>
#include <QVariantMap>

class QDir;

class ArchiveStore : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString dataRoot READ dataRoot CONSTANT)
    Q_PROPERTY(QString lastError READ lastError NOTIFY lastErrorChanged)
    Q_PROPERTY(QString toast READ toast NOTIFY toastChanged)

public:
    explicit ArchiveStore(QObject *parent = nullptr);

    QString dataRoot() const;
    QString lastError() const;
    QString toast() const;

    Q_INVOKABLE QVariantList searchDiaries(const QString &query) const;
    Q_INVOKABLE QVariantMap createDiary() const;
    Q_INVOKABLE QVariantMap getDiary(const QString &entryId) const;
    Q_INVOKABLE QVariantMap saveDiary(const QVariantMap &payload);
    Q_INVOKABLE bool deleteDiary(const QString &entryId);
    Q_INVOKABLE QVariantMap diaryHeatmap(int weeks = 18) const;
    Q_INVOKABLE QString exportModulePackage(const QString &module);
    Q_INVOKABLE QVariantList importImage(
        const QString &scope,
        const QString &primaryId,
        const QString &secondaryId,
        const QVariantList &currentImages,
        const QUrl &sourceUrl);
    Q_INVOKABLE QVariantList removeImageAt(const QVariantList &currentImages, int index) const;
    Q_INVOKABLE QVariantList updateImageLabel(const QVariantList &currentImages, int index, const QString &label) const;
    Q_INVOKABLE QString imageFileUrl(
        const QString &scope,
        const QString &primaryId,
        const QString &secondaryId,
        const QString &fileName) const;

    Q_INVOKABLE QVariantList searchFootprints(const QString &query) const;
    Q_INVOKABLE QVariantMap createFootprint() const;
    Q_INVOKABLE QVariantMap getFootprint(const QString &placeId) const;
    Q_INVOKABLE QVariantMap saveFootprint(const QVariantMap &payload);
    Q_INVOKABLE QVariantMap createFootprintVisit(const QString &date = QString()) const;
    Q_INVOKABLE QVariantMap saveFootprintVisit(const QString &placeId, const QVariantMap &payload);
    Q_INVOKABLE bool deleteFootprint(const QString &placeId);
    Q_INVOKABLE bool deleteFootprintVisit(const QString &placeId, const QString &visitId);

    Q_INVOKABLE QVariantList searchBooks(const QString &query) const;
    Q_INVOKABLE QVariantMap createBook() const;
    Q_INVOKABLE QVariantMap getBook(const QString &bookId) const;
    Q_INVOKABLE QVariantMap saveBook(const QVariantMap &payload);
    Q_INVOKABLE bool deleteBook(const QString &bookId);

    Q_INVOKABLE QVariantList searchPlans(const QString &query) const;
    Q_INVOKABLE QVariantMap createPlan() const;
    Q_INVOKABLE QVariantMap getPlan(const QString &planId) const;
    Q_INVOKABLE QVariantMap savePlan(const QVariantMap &payload);
    Q_INVOKABLE bool deletePlan(const QString &planId);

    Q_INVOKABLE QVariantList searchThoughts(const QString &query) const;
    Q_INVOKABLE QVariantMap createThought() const;
    Q_INVOKABLE QVariantMap getThought(const QString &thoughtId) const;
    Q_INVOKABLE QVariantMap saveThought(const QVariantMap &payload);
    Q_INVOKABLE bool deleteThought(const QString &thoughtId);

    Q_INVOKABLE QVariantList searchResources(const QString &query) const;
    Q_INVOKABLE QVariantMap createResource() const;
    Q_INVOKABLE QVariantMap getResource(const QString &resourceId) const;
    Q_INVOKABLE QVariantMap saveResource(const QVariantMap &payload);
    Q_INVOKABLE bool deleteResource(const QString &resourceId);

    Q_INVOKABLE QVariantList searchObservations(const QString &query) const;
    Q_INVOKABLE QVariantMap createObservation() const;
    Q_INVOKABLE QVariantMap getObservation(const QString &observationId) const;
    Q_INVOKABLE QVariantMap saveObservation(const QVariantMap &payload);
    Q_INVOKABLE bool deleteObservation(const QString &observationId);

    Q_INVOKABLE QVariantMap dataOverview() const;
    Q_INVOKABLE QString exportFullBackup(bool forShare = false);
    Q_INVOKABLE bool exportAndShareBackup();
    Q_INVOKABLE bool importBackupPackage(const QUrl &sourceUrl);

signals:
    void dataChanged();
    void lastErrorChanged();
    void toastChanged();

private:
    QString m_root;
    QString m_lastError;
    QString m_toast;

    QString entriesPath() const;
    QString footprintsPath() const;
    QString booksPath() const;
    QString plansPath() const;
    QString thoughtsPath() const;
    QString resourcesPath() const;
    QString observationsPath() const;
    QString exportsPath() const;
    QString shareBackupsPath() const;

    QVariantMap loadDiaryFromDir(const QDir &entryDir, bool includeDeleted) const;
    QVariantMap loadFootprintFromDir(const QDir &placeDir, bool includeDeleted) const;
    QVariantMap loadVisitFromDir(const QDir &visitDir) const;
    QVariantMap loadBookFromDir(const QDir &bookDir, bool includeDeleted) const;
    QVariantMap loadPlanFromDir(const QDir &planDir, bool includeDeleted) const;
    QVariantMap loadJsonRecordFromDir(
        const QDir &recordDir,
        const QString &jsonFile,
        const QString &titleKey,
        const QString &fallbackTitle,
        bool includeDeleted) const;

    bool writeJsonFile(const QString &path, const QVariantMap &value);
    QVariantMap readJsonFile(const QString &path, bool *ok = nullptr) const;
    QString readTextFile(const QString &path) const;
    bool writeTextFile(const QString &path, const QString &value);
    bool ensureDir(const QString &path) const;
    bool softDelete(const QString &jsonPath, const QString &missingMessage);

    QVariantList readImages(const QVariant &value) const;
    QVariantList readMapList(const QVariant &value) const;
    QString imageDirForScope(const QString &scope, const QString &primaryId, const QString &secondaryId) const;
    QString imageFileNameFromUrl(const QUrl &sourceUrl) const;
    QString uniqueImageName(const QString &imagesDirPath, const QString &originalName) const;
    bool copyImageIntoDir(const QUrl &sourceUrl, const QString &targetPath);
    void pruneUnusedImages(const QString &imagesDirPath, const QVariantList &images) const;
    QVariantList readRelatedDiaries(const QVariant &value) const;
    QStringList readTags(const QVariant &value) const;
    QVariantList readVisitIds(const QVariantMap &place) const;

    QString nowIso() const;
    QString newId() const;
    QString todayIso() const;
    QString mapString(const QVariantMap &map, const QString &key, const QString &fallback = QString()) const;
    bool matchesAny(const QStringList &haystacks, const QString &query) const;
    void sortByUpdated(QVariantList *items) const;
    void sortDiaries(QVariantList *items) const;
    void sortPlans(QVariantList *items) const;
    int countRecords(const QString &folderPath, const QString &jsonFile) const;
    bool addFullBackupEntries(const QString &zipPath, bool forShare, QString *displayPath);
    bool copyDirectory(const QString &sourcePath, const QString &targetPath) const;
    bool extractBackupToTemp(const QString &zipPath, QString *tempDiaryPath, QStringList *topLevelFolders) const;
    QString localPathFromUrl(const QUrl &sourceUrl) const;
    bool shareFileOnAndroid(const QString &filePath);

    void setError(const QString &message);
    void setToast(const QString &message);
    void clearError();
};
